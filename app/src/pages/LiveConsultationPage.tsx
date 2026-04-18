import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
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
import type {
  SessionClientMessage,
  SessionServerEvent,
  SessionStartView,
} from '../types/contracts';
import { blobToBase64 } from '../utils/base64';

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
  const [error, setError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<'idle' | 'connecting' | 'connected' | 'disconnected'>(
    'idle',
  );
  const [microphoneState, setMicrophoneState] = useState<'unknown' | 'granted' | 'denied'>('unknown');
  const [sessionMessage, setSessionMessage] = useState<string | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const sessionRef = useRef<SessionStartView | null>(null);
  const chunkIndexRef = useRef(0);
  const consultationQuery = useConsultationDetailQuery(consultationId);
  const startSessionMutation = useStartSessionMutation(consultationId);
  const endSessionMutation = useEndSessionMutation(consultationId);
  const { refetch: refetchConsultation } = consultationQuery;
  const consultation = consultationQuery.data ?? null;
  const queryError = consultationQuery.error
    ? consultationQuery.error instanceof ApiError
      ? consultationQuery.error.message
      : 'Não foi possível carregar os detalhes da consulta.'
    : null;

  useEffect(() => {
    return () => {
      recorderRef.current?.stop();
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      socketRef.current?.close();
    };
  }, []);

  const connectWebSocket = useCallback(
    (session: SessionStartView) => {
      const url = `${toWebSocketUrl(session)}?token=${encodeURIComponent(session.connection_token)}`;
      setConnectionState('connecting');
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        setConnectionState('connected');
        const initPayload: SessionClientMessage = {
          action: 'session.init',
          data: {
            consultation_id: consultationId,
            session_id: session.session_id,
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
          setSessionMessage(String(payload.data.message ?? 'Sessão conectada.'));
          return;
        }

        if (payload.event === 'session.warning') {
          setSessionMessage(String(payload.data.message ?? 'Aviso de sessão.'));
          return;
        }

        if (payload.event === 'session.ended') {
          setSessionMessage(String(payload.data.message ?? 'Sessão encerrada.'));
          setConnectionState('disconnected');
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
        setConnectionState('disconnected');
        setSessionMessage('Conexão perdida. Use o botão de reconectar.');
      };

      socket.onclose = () => {
        setConnectionState('disconnected');
      };
    },
    [consultationId, refetchConsultation],
  );

  const requestMicrophone = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicrophoneState('denied');
      throw new ApiError('Seu navegador não suporta captura de áudio.', 400, 'microphone_unsupported');
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      setMicrophoneState('granted');
      return stream;
    } catch {
      setMicrophoneState('denied');
      throw new ApiError('Permissão de microfone negada.', 400, 'microphone_denied');
    }
  }, []);

  async function handleStartRecording() {
    if (!consultationId) {
      return;
    }

    setError(null);
    setSessionMessage(null);

    try {
      const stream = mediaStreamRef.current ?? (await requestMicrophone());
      const startView = await startSessionMutation.mutateAsync();
      sessionRef.current = startView;

      connectWebSocket(startView);

      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunkIndexRef.current = 0;

      recorder.ondataavailable = (event) => {
        void (async () => {
          if (!event.data || event.data.size === 0) {
            return;
          }

          if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
            return;
          }

          const audioBase64 = await blobToBase64(event.data);
          const payload: SessionClientMessage = {
            action: 'audio.chunk',
            data: {
              chunk_index: chunkIndexRef.current,
              audio: audioBase64,
              timestamp: new Date().toISOString(),
            },
          };
          socketRef.current.send(JSON.stringify(payload));
          chunkIndexRef.current += 1;
        })();
      };

      recorder.start(1000);
      setSessionMessage('Sessão de gravação iniciada.');
      await refetchConsultation();
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Falha ao iniciar sessão de gravação.');
      }
    }
  }

  async function handleStopRecording() {
    if (!consultationId) {
      return;
    }

    setError(null);

    try {
      recorderRef.current?.stop();
      recorderRef.current = null;

      if (socketRef.current?.readyState === WebSocket.OPEN) {
        const stopPayload: SessionClientMessage = {
          action: 'session.stop',
          data: {
            consultation_id: consultationId,
          },
        };
        socketRef.current.send(JSON.stringify(stopPayload));
      }

      await endSessionMutation.mutateAsync();
      setSessionMessage('Gravação encerrada. Processamento iniciado.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Falha ao encerrar gravação.');
      }
    } finally {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
      socketRef.current?.close();
      socketRef.current = null;
      setConnectionState('disconnected');
      await refetchConsultation();
    }
  }

  async function handleReconnect() {
    if (!sessionRef.current) {
      setError('Nenhuma sessão ativa para reconectar.');
      return;
    }

    connectWebSocket(sessionRef.current);
  }

  const canStartRecording = consultation?.actions.can_start_recording ?? false;
  const canStopRecording = consultation?.actions.can_stop_recording ?? false;

  const statusLabel = useMemo(() => {
    if (!consultation) {
      return 'indisponível';
    }

    return uiConfig?.status_labels?.[consultation.status] ?? consultation.status;
  }, [consultation, uiConfig]);

  return (
    <div className="page-grid page-grid-equal">
      <Card
        title={uiConfig?.labels.live_session_header ?? 'Sessão ao vivo'}
        actions={<RouterLink className="ds-link" to="/consultations">Voltar para consultas</RouterLink>}
      >

        {consultationQuery.isPending ? <Loader label="Carregando consulta" /> : null}

        {!consultationQuery.isPending && consultation ? (
          <div className="status-strip">
            <Chip tone="info">Status: {statusLabel}</Chip>
            <Chip tone={microphoneState === 'denied' ? 'danger' : microphoneState === 'granted' ? 'success' : 'neutral'}>
              Microfone:{' '}
              {microphoneState === 'unknown'
                ? 'Não solicitado'
                : microphoneState === 'granted'
                  ? 'Permitido'
                  : 'Negado'}
            </Chip>
            <Chip tone={connectionState === 'connected' ? 'success' : connectionState === 'disconnected' ? 'warning' : 'neutral'}>
              Conexão: {connectionState}
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
            disabled={!canStartRecording}
            isLoading={startSessionMutation.isPending}
          >
            {startSessionMutation.isPending
              ? 'Iniciando...'
              : uiConfig?.labels.start_recording_button ?? 'Iniciar gravação'}
          </Button>

          <Button
            type="button"
            variant="secondary"
            onClick={() => void handleStopRecording()}
            disabled={!canStopRecording}
            isLoading={endSessionMutation.isPending}
          >
            {endSessionMutation.isPending
              ? 'Encerrando...'
              : uiConfig?.labels.stop_recording_button ?? 'Parar gravação'}
          </Button>

          <Button
            type="button"
            variant="ghost"
            onClick={() => void handleReconnect()}
            disabled={connectionState === 'connected' || !sessionRef.current}
          >
            Reconectar
          </Button>

          <RouterLink to={`/consultations/${consultationId}/review`} className="ds-link">
            Ir para revisão
          </RouterLink>
        </div>
      </Card>

      <Card title="Transcrição ao vivo">
        {transcript.length === 0 ? (
          <EmptyState
            title="Aguardando transcrição"
            description="A transcrição parcial aparecerá aqui durante a sessão."
          />
        ) : (
          <ul className="transcript-list">
            {transcript.map((item) => (
              <li key={item.id}>
                <strong>{item.speaker}:</strong> {item.text}
                {!item.isFinal ? <Text tone="muted">parcial</Text> : null}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
