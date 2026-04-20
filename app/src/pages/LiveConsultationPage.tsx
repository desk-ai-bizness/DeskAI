import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { getTranscriptionToken } from '../api/endpoints';
import {
  useConsultationDetailQuery,
  useEndSessionMutation,
  useStartSessionMutation,
} from '../api/query-hooks';
import { useAuth } from '../auth/use-auth';
import {
  Alert,
  Button,
  Card,
  Chip,
  EmptyState,
  Loader,
  Text,
} from '../components/ui';
import { runtimeConfig } from '../config/env';
import { ElevenLabsScribe } from '../services/elevenlabs-scribe';
import type { ScribeCommittedEvent } from '../services/elevenlabs-scribe';
import { relayCommittedSegment } from '../services/transcript-relay';
import type {
  SessionClientMessage,
  SessionServerEvent,
  SessionStartView,
} from '../types/contracts';
import { CURRENT_EVENT_VERSION } from '../types/contracts';

type RecordingState = 'idle' | 'connecting' | 'recording' | 'paused' | 'disconnected';

interface TranscriptItem {
  id: string;
  speaker: string;
  text: string;
  isFinal: boolean;
}

function parseSessionEvent(rawMessage: string): SessionServerEvent | null {
  try {
    const parsed = JSON.parse(rawMessage) as SessionServerEvent;
    if (!parsed || typeof parsed !== 'object' || !('event' in parsed)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function toWebSocketUrl(startView: SessionStartView): string {
  if (startView.websocket_url.startsWith('ws://') || startView.websocket_url.startsWith('wss://')) {
    return startView.websocket_url;
  }

  if (runtimeConfig.wsBaseUrl.startsWith('ws://') || runtimeConfig.wsBaseUrl.startsWith('wss://')) {
    return runtimeConfig.wsBaseUrl;
  }

  return startView.websocket_url.replace(/^http/, 'ws');
}

export function LiveConsultationPage() {
  const { consultationId = '' } = useParams();
  const { uiConfig } = useAuth();

  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [partialText, setPartialText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [microphoneState, setMicrophoneState] = useState<'unknown' | 'granted' | 'denied'>('unknown');
  const [sessionMessage, setSessionMessage] = useState<string | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const sessionRef = useRef<SessionStartView | null>(null);
  const scribeRef = useRef<ElevenLabsScribe | null>(null);

  const consultationQuery = useConsultationDetailQuery(consultationId);
  const startSessionMutation = useStartSessionMutation(consultationId);
  const endSessionMutation = useEndSessionMutation(consultationId);
  const { refetch: refetchConsultation } = consultationQuery;
  const consultation = consultationQuery.data ?? null;
  const queryError = consultationQuery.error
    ? consultationQuery.error instanceof ApiError
      ? consultationQuery.error.message
      : 'Nao foi possivel carregar os detalhes da consulta.'
    : null;

  useEffect(() => {
    return () => {
      scribeRef.current?.close();
      processorRef.current?.disconnect();
      audioContextRef.current?.close().catch(() => {});
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      socketRef.current?.close();
    };
  }, []);

  const connectBackendWebSocket = useCallback(
    (session: SessionStartView) => {
      const url = `${toWebSocketUrl(session)}?token=${encodeURIComponent(session.connection_token)}`;
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        const initPayload: SessionClientMessage = {
          action: 'session.init',
          data: {
            consultation_id: consultationId,
            session_id: session.session_id,
            event_version: CURRENT_EVENT_VERSION,
          },
        };
        socket.send(JSON.stringify(initPayload));
      };

      socket.onmessage = (event) => {
        const payload = parseSessionEvent(event.data);
        if (!payload) {
          return;
        }

        if (payload.event === 'session.status') {
          setSessionMessage(String(payload.data.message ?? 'Sessao conectada.'));
          return;
        }

        if (payload.event === 'session.warning') {
          setSessionMessage(String(payload.data.message ?? 'Aviso de sessao.'));
          return;
        }

        if (payload.event === 'session.ended') {
          setSessionMessage(String(payload.data.message ?? 'Sessao encerrada.'));
          setRecordingState('disconnected');
          void refetchConsultation();
          return;
        }

        if (payload.event === 'transcript.partial' || payload.event === 'transcript.final') {
          setTranscript((current) => [
            ...current,
            {
              id: `${Date.now()}-${current.length}`,
              speaker: String(payload.data.speaker ?? 'desconhecido'),
              text: String(payload.data.text ?? ''),
              isFinal: payload.event === 'transcript.final' || Boolean(payload.data.is_final),
            },
          ]);
        }
      };

      socket.onerror = () => {
        setSessionMessage('Conexao com o servidor perdida. Use o botao de reconectar.');
      };

      socket.onclose = () => {
        if (recordingState !== 'idle') {
          setRecordingState('disconnected');
        }
      };
    },
    [consultationId, refetchConsultation, recordingState],
  );

  const requestMicrophone = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicrophoneState('denied');
      throw new ApiError('Seu navegador nao suporta captura de audio.', 400, 'microphone_unsupported');
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      mediaStreamRef.current = stream;
      setMicrophoneState('granted');
      return stream;
    } catch {
      setMicrophoneState('denied');
      throw new ApiError('Permissao de microfone negada.', 400, 'microphone_denied');
    }
  }, []);

  function startAudioCapture(stream: MediaStream, scribe: ElevenLabsScribe): void {
    const audioContext = new AudioContext({ sampleRate: 16000 });
    audioContextRef.current = audioContext;

    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    processorRef.current = processor;

    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      const bytes = new Uint8Array(pcm16.buffer);
      let binary = '';
      const chunkSize = 0x8000;
      for (let j = 0; j < bytes.length; j += chunkSize) {
        const chunk = bytes.subarray(j, j + chunkSize);
        binary += String.fromCharCode(...chunk);
      }
      const base64 = btoa(binary);

      scribe.sendAudio(base64);
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
  }

  function stopAudioCapture(): void {
    processorRef.current?.disconnect();
    processorRef.current = null;

    if (audioContextRef.current) {
      void audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  }

  async function handleStartRecording() {
    if (!consultationId) {
      return;
    }

    setError(null);
    setSessionMessage(null);
    setRecordingState('connecting');

    try {
      const stream = mediaStreamRef.current ?? (await requestMicrophone());
      const startView = await startSessionMutation.mutateAsync();
      sessionRef.current = startView;

      connectBackendWebSocket(startView);

      const tokenView = await getTranscriptionToken(consultationId);

      const scribe = new ElevenLabsScribe();
      scribeRef.current = scribe;

      scribe.onPartial((event) => {
        setPartialText(event.text);
      });

      scribe.onCommitted((event: ScribeCommittedEvent) => {
        setTranscript((current) => [
          ...current,
          {
            id: `scribe-${Date.now()}-${current.length}`,
            speaker: event.speaker === 'unknown' ? 'desconhecido' : event.speaker,
            text: event.text,
            isFinal: true,
          },
        ]);
        setPartialText('');

        relayCommittedSegment(socketRef.current, consultationId, event);
      });

      scribe.onError((event) => {
        setSessionMessage(`Erro de transcricao: ${event.message}`);
      });

      scribe.onClose(() => {
        setSessionMessage('Conexao com transcricao encerrada.');
      });

      scribe.setTokenRefreshCallback(async () => {
        try {
          return await getTranscriptionToken(consultationId);
        } catch {
          return null;
        }
      });

      scribe.connect(tokenView);
      startAudioCapture(stream, scribe);

      setRecordingState('recording');
      setSessionMessage('Sessao de gravacao iniciada.');
      await refetchConsultation();
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Falha ao iniciar sessao de gravacao.');
      }
      setRecordingState('idle');
    }
  }

  function handlePause() {
    stopAudioCapture();

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const pausePayload: SessionClientMessage = {
        action: 'session.pause',
        data: {
          consultation_id: consultationId,
          timestamp: new Date().toISOString(),
          event_version: CURRENT_EVENT_VERSION,
        },
      };
      socketRef.current.send(JSON.stringify(pausePayload));
    }

    setRecordingState('paused');
    setSessionMessage('Gravacao pausada.');
  }

  function handleResume() {
    const stream = mediaStreamRef.current;
    const scribe = scribeRef.current;

    if (!stream || !scribe) {
      setError('Nao foi possivel retomar a gravacao.');
      return;
    }

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const resumePayload: SessionClientMessage = {
        action: 'session.resume',
        data: {
          consultation_id: consultationId,
          timestamp: new Date().toISOString(),
          event_version: CURRENT_EVENT_VERSION,
        },
      };
      socketRef.current.send(JSON.stringify(resumePayload));
    }

    startAudioCapture(stream, scribe);
    setRecordingState('recording');
    setSessionMessage('Gravacao retomada.');
  }

  async function handleStopRecording() {
    if (!consultationId) {
      return;
    }

    setError(null);

    try {
      stopAudioCapture();
      scribeRef.current?.close();
      scribeRef.current = null;

      if (socketRef.current?.readyState === WebSocket.OPEN) {
        const stopPayload: SessionClientMessage = {
          action: 'session.stop',
          data: {
            consultation_id: consultationId,
            event_version: CURRENT_EVENT_VERSION,
          },
        };
        socketRef.current.send(JSON.stringify(stopPayload));
      }

      await endSessionMutation.mutateAsync();
      setSessionMessage('Gravacao encerrada. Processamento iniciado.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Falha ao encerrar gravacao.');
      }
    } finally {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
      socketRef.current?.close();
      socketRef.current = null;
      setRecordingState('disconnected');
      await refetchConsultation();
    }
  }

  async function handleReconnect() {
    if (!sessionRef.current) {
      setError('Nenhuma sessao ativa para reconectar.');
      return;
    }

    connectBackendWebSocket(sessionRef.current);
  }

  const canStartRecording = consultation?.actions.can_start_recording ?? false;
  const canStopRecording = consultation?.actions.can_stop_recording ?? false;

  const statusLabel = useMemo(() => {
    if (!consultation) {
      return 'indisponivel';
    }

    return uiConfig?.status_labels?.[consultation.status] ?? consultation.status;
  }, [consultation, uiConfig]);

  const recordingStateLabel = useMemo(() => {
    const labels: Record<RecordingState, string> = {
      idle: 'Inativo',
      connecting: 'Conectando',
      recording: 'Gravando',
      paused: 'Pausado',
      disconnected: 'Desconectado',
    };
    return labels[recordingState];
  }, [recordingState]);

  const recordingStateTone = useMemo(() => {
    const tones: Record<RecordingState, 'neutral' | 'info' | 'success' | 'warning' | 'danger'> = {
      idle: 'neutral',
      connecting: 'info',
      recording: 'success',
      paused: 'warning',
      disconnected: 'warning',
    };
    return tones[recordingState];
  }, [recordingState]);

  return (
    <div className="page-grid page-grid-equal">
      <Card
        title={uiConfig?.labels.live_session_header ?? 'Sessao ao vivo'}
        actions={<RouterLink className="ds-link" to="/consultations">Voltar para consultas</RouterLink>}
      >

        {consultationQuery.isPending ? <Loader label="Carregando consulta" /> : null}

        {!consultationQuery.isPending && consultation ? (
          <div className="status-strip">
            <Chip tone="info">Status: {statusLabel}</Chip>
            <Chip tone={microphoneState === 'denied' ? 'danger' : microphoneState === 'granted' ? 'success' : 'neutral'}>
              Microfone:{' '}
              {microphoneState === 'unknown'
                ? 'Nao solicitado'
                : microphoneState === 'granted'
                  ? 'Permitido'
                  : 'Negado'}
            </Chip>
            <Chip tone={recordingStateTone}>
              Gravacao: {recordingStateLabel}
            </Chip>
          </div>
        ) : null}

        {consultation?.warnings.length ? (
          <Alert tone="warning">
            <ul className="warning-list">
              {consultation.warnings.map((warning) => (
                <li key={warning.type}>{warning.message}</li>
              ))}
            </ul>
          </Alert>
        ) : null}

        {queryError ? <Alert tone="danger">{queryError}</Alert> : null}
        {sessionMessage ? <Alert tone="info">{sessionMessage}</Alert> : null}
        {error ? (
          <Alert tone="danger">
            {error}
          </Alert>
        ) : null}

        <div className="inline-row">
          <Button
            type="button"
            onClick={() => void handleStartRecording()}
            disabled={!canStartRecording || recordingState !== 'idle'}
            isLoading={startSessionMutation.isPending}
          >
            {startSessionMutation.isPending
              ? 'Iniciando...'
              : uiConfig?.labels.start_recording_button ?? 'Iniciar gravacao'}
          </Button>

          {recordingState === 'recording' ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => handlePause()}
            >
              Pausar gravacao
            </Button>
          ) : null}

          {recordingState === 'paused' ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleResume()}
            >
              Retomar gravacao
            </Button>
          ) : null}

          <Button
            type="button"
            variant="secondary"
            onClick={() => void handleStopRecording()}
            disabled={!canStopRecording}
            isLoading={endSessionMutation.isPending}
          >
            {endSessionMutation.isPending
              ? 'Encerrando...'
              : uiConfig?.labels.stop_recording_button ?? 'Parar gravacao'}
          </Button>

          <Button
            type="button"
            variant="ghost"
            onClick={() => void handleReconnect()}
            disabled={recordingState === 'recording' || !sessionRef.current}
          >
            Reconectar
          </Button>

          <RouterLink to={`/consultations/${consultationId}/review`} className="ds-link">
            Ir para revisao
          </RouterLink>
        </div>
      </Card>

      <Card title="Transcricao ao vivo">
        {transcript.length === 0 && !partialText ? (
          <EmptyState
            title="Aguardando transcricao"
            description="A transcricao aparecera aqui durante a sessao."
          />
        ) : (
          <ul className="transcript-list">
            {transcript.map((item) => (
              <li key={item.id}>
                <strong>{item.speaker}:</strong> {item.text}
                {!item.isFinal ? <Text tone="muted"> parcial</Text> : null}
              </li>
            ))}
            {partialText ? (
              <li>
                <Text tone="muted">{partialText}</Text>
              </li>
            ) : null}
          </ul>
        )}
      </Card>
    </div>
  );
}
