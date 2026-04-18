import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import {
  endSession,
  getConsultationDetail,
  startSession,
} from '../api/endpoints';
import { useAuth } from '../auth/use-auth';
import { runtimeConfig } from '../config/env';
import type {
  ConsultationDetailView,
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

  const [consultation, setConsultation] = useState<ConsultationDetailView | null>(null);
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
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

  const refreshConsultation = useCallback(async () => {
    if (!consultationId) {
      return;
    }

    try {
      const detail = await getConsultationDetail(consultationId);
      setConsultation(detail);
      setError(null);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel carregar os detalhes da consulta.');
      }
    }
  }, [consultationId]);

  useEffect(() => {
    void (async () => {
      setIsLoading(true);
      await refreshConsultation();
      setIsLoading(false);
    })();
  }, [refreshConsultation]);

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
          setSessionMessage(String(payload.data.message ?? 'Sessao conectada.'));
          return;
        }

        if (payload.event === 'session.warning') {
          setSessionMessage(String(payload.data.message ?? 'Aviso de sessao.'));
          return;
        }

        if (payload.event === 'session.ended') {
          setSessionMessage(String(payload.data.message ?? 'Sessao encerrada.'));
          setConnectionState('disconnected');
          void refreshConsultation();
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
        setSessionMessage('Conexao perdida. Use o botao de reconectar.');
      };

      socket.onclose = () => {
        setConnectionState('disconnected');
      };
    },
    [consultationId, refreshConsultation],
  );

  const requestMicrophone = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicrophoneState('denied');
      throw new ApiError('Seu navegador nao suporta captura de audio.', 400, 'microphone_unsupported');
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      setMicrophoneState('granted');
      return stream;
    } catch {
      setMicrophoneState('denied');
      throw new ApiError('Permissao de microfone negada.', 400, 'microphone_denied');
    }
  }, []);

  async function handleStartRecording() {
    if (!consultationId) {
      return;
    }

    setIsStarting(true);
    setError(null);
    setSessionMessage(null);

    try {
      const stream = mediaStreamRef.current ?? (await requestMicrophone());
      const startView = await startSession(consultationId);
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
      setSessionMessage('Sessao de gravacao iniciada.');
      await refreshConsultation();
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Falha ao iniciar sessao de gravacao.');
      }
    } finally {
      setIsStarting(false);
    }
  }

  async function handleStopRecording() {
    if (!consultationId) {
      return;
    }

    setIsStopping(true);
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

      await endSession(consultationId);
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
      setConnectionState('disconnected');
      await refreshConsultation();
      setIsStopping(false);
    }
  }

  async function handleReconnect() {
    if (!sessionRef.current) {
      setError('Nenhuma sessao ativa para reconectar.');
      return;
    }

    connectWebSocket(sessionRef.current);
  }

  const canStartRecording = consultation?.actions.can_start_recording ?? false;
  const canStopRecording = consultation?.actions.can_stop_recording ?? false;

  const statusLabel = useMemo(() => {
    if (!consultation) {
      return 'indisponivel';
    }

    return uiConfig?.status_labels?.[consultation.status] ?? consultation.status;
  }, [consultation, uiConfig]);

  return (
    <div className="page-grid page-grid-equal">
      <section className="panel">
        <header className="panel-header">
          <h2>{uiConfig?.labels.live_session_header ?? 'Sessao ao vivo'}</h2>
          <Link to="/consultations">Voltar para consultas</Link>
        </header>

        {isLoading ? <p>Carregando consulta...</p> : null}

        {!isLoading && consultation ? (
          <>
            <p>
              <strong>Status:</strong> {statusLabel}
            </p>
            <p>
              <strong>Microfone:</strong>{' '}
              {microphoneState === 'unknown'
                ? 'Nao solicitado'
                : microphoneState === 'granted'
                  ? 'Permitido'
                  : 'Negado'}
            </p>
            <p>
              <strong>Conexao:</strong> {connectionState}
            </p>
          </>
        ) : null}

        {consultation?.warnings.length ? (
          <ul className="warning-list">
            {consultation.warnings.map((warning) => (
              <li key={warning.type}>{warning.message}</li>
            ))}
          </ul>
        ) : null}

        {sessionMessage ? <p className="hint">{sessionMessage}</p> : null}
        {error ? (
          <p className="inline-error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="inline-row">
          <button
            type="button"
            className="primary-button"
            onClick={() => void handleStartRecording()}
            disabled={isStarting || !canStartRecording}
          >
            {isStarting
              ? 'Iniciando...'
              : uiConfig?.labels.start_recording_button ?? 'Iniciar gravacao'}
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={() => void handleStopRecording()}
            disabled={isStopping || !canStopRecording}
          >
            {isStopping
              ? 'Encerrando...'
              : uiConfig?.labels.stop_recording_button ?? 'Parar gravacao'}
          </button>

          <button
            type="button"
            className="ghost-button"
            onClick={() => void handleReconnect()}
            disabled={connectionState === 'connected' || !sessionRef.current}
          >
            Reconectar
          </button>

          <Link to={`/consultations/${consultationId}/review`} className="ghost-link">
            Ir para revisao
          </Link>
        </div>
      </section>

      <section className="panel">
        <h2>Transcricao ao vivo</h2>
        {transcript.length === 0 ? (
          <p className="hint">A transcricao parcial aparecera aqui durante a sessao.</p>
        ) : (
          <ul className="transcript-list">
            {transcript.map((item) => (
              <li key={item.id}>
                <strong>{item.speaker}:</strong> {item.text}
                {!item.isFinal ? ' (parcial)' : ''}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
