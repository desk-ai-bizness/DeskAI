import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { getTranscriptionToken } from '../api/endpoints';
import {
  useConsultationDetailQuery,
  useEndSessionMutation,
  useExportConsultationMutation,
  useFinalizeConsultationMutation,
  usePatientDetailQuery,
  useReviewQuery,
  useStartSessionMutation,
  useUpdateReviewMutation,
} from '../api/query-hooks';
import { useAuth } from '../auth/use-auth';
import {
  Alert,
  Button,
  Card,
  Chip,
  EmptyState,
  Link as UiLink,
  Loader,
  Text,
  TextAreaField,
  TextField,
} from '../components/ui';
import { runtimeConfig } from '../config/env';
import { ElevenLabsScribe } from '../services/elevenlabs-scribe';
import type { ScribeCommittedEvent } from '../services/elevenlabs-scribe';
import { relayCommittedSegment } from '../services/transcript-relay';
import type {
  ExportView,
  ReviewInsight,
  ReviewView,
  SessionClientMessage,
  SessionServerEvent,
  SessionStartView,
  UpdateReviewRequest,
} from '../types/contracts';
import { CURRENT_EVENT_VERSION } from '../types/contracts';
import { toPrettyJson } from '../utils/format';

type RecordingState = 'idle' | 'connecting' | 'recording' | 'paused' | 'disconnected';
type WorkspaceFieldKey =
  | 'queixa_principal'
  | 'historia_doenca_atual'
  | 'medicamentos_em_uso'
  | 'alergias'
  | 'antecedentes_pessoais'
  | 'cirurgias_internacoes'
  | 'antecedentes_familiares'
  | 'habitos_estilo_de_vida'
  | 'revisao_de_sistemas'
  | 'exame_objetivo_observacoes';

interface TranscriptItem {
  id: string;
  speaker: string;
  text: string;
  isFinal: boolean;
}

interface ProvisionalAutofillCandidate {
  fieldKey: WorkspaceFieldKey;
  candidateValue: string;
  confidence: number;
  evidenceExcerpt: string;
}

interface ProvisionalInsightItem {
  insightId: string;
  category: 'documentation_gap' | 'consistency_issue' | 'clinical_attention';
  text: string;
  severity: 'informative' | 'moderate' | 'important';
  evidenceExcerpt: string;
}

interface WorkspaceDraft {
  consultationId: string;
  fields: Record<WorkspaceFieldKey, string>;
  summaryText: string;
}

const WORKSPACE_FIELDS: Array<{ key: WorkspaceFieldKey; label: string; rows: number }> = [
  { key: 'queixa_principal', label: 'Queixa principal', rows: 3 },
  { key: 'historia_doenca_atual', label: 'História da doença atual', rows: 5 },
  { key: 'medicamentos_em_uso', label: 'Medicamentos em uso', rows: 3 },
  { key: 'alergias', label: 'Alergias', rows: 3 },
  { key: 'antecedentes_pessoais', label: 'Antecedentes pessoais', rows: 3 },
  { key: 'cirurgias_internacoes', label: 'Cirurgias e internações', rows: 3 },
  { key: 'antecedentes_familiares', label: 'Antecedentes familiares', rows: 3 },
  { key: 'habitos_estilo_de_vida', label: 'Hábitos e estilo de vida', rows: 3 },
  { key: 'revisao_de_sistemas', label: 'Revisão de sistemas', rows: 3 },
  { key: 'exame_objetivo_observacoes', label: 'Exame objetivo e observações', rows: 4 },
];

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

function emptyWorkspaceFields(): Record<WorkspaceFieldKey, string> {
  return {
    queixa_principal: '',
    historia_doenca_atual: '',
    medicamentos_em_uso: '',
    alergias: '',
    antecedentes_pessoais: '',
    cirurgias_internacoes: '',
    antecedentes_familiares: '',
    habitos_estilo_de_vida: '',
    revisao_de_sistemas: '',
    exame_objetivo_observacoes: '',
  };
}

function toPlainText(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map((item) => toPlainText(item)).filter(Boolean).join('\n');
  }
  if (typeof value === 'object') {
    return Object.values(value as Record<string, unknown>)
      .map((item) => toPlainText(item))
      .filter(Boolean)
      .join('\n');
  }
  return '';
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function deriveWorkspaceFields(content: unknown): Record<WorkspaceFieldKey, string> {
  const fields = emptyWorkspaceFields();
  const data = asRecord(content);
  const complaint = asRecord(data.queixa_principal);
  const currentHistory = asRecord(data.historia_doenca_atual);
  const pastHistory = asRecord(data.historico_medico_pregresso);

  fields.queixa_principal = toPlainText(complaint.descricao ?? data.queixa_principal);
  fields.historia_doenca_atual = toPlainText(currentHistory.narrativa ?? data.historia_doenca_atual);
  fields.medicamentos_em_uso = toPlainText(data.medicamentos_em_uso);
  fields.alergias = toPlainText(data.alergias);
  fields.antecedentes_pessoais = toPlainText(
    data.antecedentes_pessoais ?? pastHistory.doencas_previas,
  );
  fields.cirurgias_internacoes = [
    toPlainText(data.cirurgias_internacoes ?? pastHistory.cirurgias_previas),
    toPlainText(pastHistory.internacoes_previas),
  ]
    .filter(Boolean)
    .join('\n');
  fields.antecedentes_familiares = toPlainText(data.antecedentes_familiares);
  fields.habitos_estilo_de_vida = toPlainText(data.habitos_estilo_de_vida);
  fields.revisao_de_sistemas = toPlainText(data.revisao_de_sistemas);
  fields.exame_objetivo_observacoes = [
    toPlainText(data.exame_objetivo_observacoes),
    toPlainText(data.achados_exame_fisico),
    toPlainText(data.observacoes_adicionais),
  ]
    .filter(Boolean)
    .join('\n');

  return fields;
}

function buildMedicalHistoryPayload(
  baseContent: unknown,
  fields: Record<WorkspaceFieldKey, string>,
): Record<string, unknown> {
  const next = { ...asRecord(baseContent) };
  next.queixa_principal = {
    ...asRecord(next.queixa_principal),
    descricao: fields.queixa_principal,
  };
  next.historia_doenca_atual = {
    ...asRecord(next.historia_doenca_atual),
    narrativa: fields.historia_doenca_atual,
  };
  next.medicamentos_em_uso = fields.medicamentos_em_uso;
  next.alergias = fields.alergias;
  next.antecedentes_pessoais = fields.antecedentes_pessoais;
  next.cirurgias_internacoes = fields.cirurgias_internacoes;
  next.antecedentes_familiares = fields.antecedentes_familiares;
  next.habitos_estilo_de_vida = fields.habitos_estilo_de_vida;
  next.revisao_de_sistemas = fields.revisao_de_sistemas;
  next.exame_objetivo_observacoes = fields.exame_objetivo_observacoes;
  return next;
}

function summaryContentToText(content: unknown): string {
  if (typeof content === 'string') {
    return content;
  }
  if (content && typeof content === 'object') {
    return toPrettyJson(content);
  }
  return '';
}

function buildSummaryPayload(summaryText: string, existingSummary: unknown): Record<string, unknown> {
  const trimmed = summaryText.trim();
  if (!trimmed) {
    return {};
  }

  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    // Fallback to a safe free-text wrapper.
  }

  return {
    ...asRecord(existingSummary),
    resumo_livre: trimmed,
  };
}

function buildReviewUpdatePayload(
  fields: Record<WorkspaceFieldKey, string>,
  summaryText: string,
  insightActions: Record<string, { action: 'accept' | 'dismiss' | 'edit'; note: string }>,
  baseMedicalHistory: unknown,
  baseSummary: unknown,
): UpdateReviewRequest {
  return {
    medical_history: buildMedicalHistoryPayload(baseMedicalHistory, fields),
    summary: buildSummaryPayload(summaryText, baseSummary),
    insights: Object.entries(insightActions).map(([insightId, actionConfig]) => ({
      insight_id: insightId,
      action: actionConfig.action,
      physician_note: actionConfig.note || undefined,
    })),
  };
}

export function LiveConsultationPage() {
  const { consultationId = '' } = useParams();
  const { uiConfig } = useAuth();

  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [partialText, setPartialText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [microphoneState, setMicrophoneState] = useState<'unknown' | 'granted' | 'denied'>('unknown');
  const [sessionMessage, setSessionMessage] = useState<string | null>(null);
  const [workspaceDraft, setWorkspaceDraft] = useState<WorkspaceDraft | null>(null);
  const [insightActions, setInsightActions] = useState<
    Record<string, { action: 'accept' | 'dismiss' | 'edit'; note: string }>
  >({});
  const [exportResult, setExportResult] = useState<ExportView | null>(null);
  const [finalizationConfirmed, setFinalizationConfirmed] = useState(false);
  const [isEndSessionDialogOpen, setIsEndSessionDialogOpen] = useState(false);
  const [provisionalAutofill, setProvisionalAutofill] = useState<
    Partial<Record<WorkspaceFieldKey, ProvisionalAutofillCandidate>>
  >({});
  const [provisionalInsights, setProvisionalInsights] = useState<ProvisionalInsightItem[]>([]);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const sessionRef = useRef<SessionStartView | null>(null);
  const scribeRef = useRef<ElevenLabsScribe | null>(null);

  const consultationQuery = useConsultationDetailQuery(consultationId);
  const consultation = consultationQuery.data ?? null;
  const shouldLoadReview = Boolean(
    consultation?.has_draft ||
      consultation?.status === 'under_physician_review' ||
      consultation?.status === 'finalized',
  );
  const patientDetailQuery = usePatientDetailQuery(consultation?.patient.patient_id ?? '');
  const reviewQuery = useReviewQuery(consultationId, shouldLoadReview);
  const review = reviewQuery.data ?? null;
  const startSessionMutation = useStartSessionMutation(consultationId);
  const endSessionMutation = useEndSessionMutation(consultationId);
  const updateReviewMutation = useUpdateReviewMutation(consultationId);
  const finalizeMutation = useFinalizeConsultationMutation(consultationId);
  const exportMutation = useExportConsultationMutation(consultationId);
  const { refetch: refetchConsultation } = consultationQuery;

  useEffect(() => {
    return () => {
      scribeRef.current?.close();
      processorRef.current?.disconnect();
      audioContextRef.current?.close().catch(() => {});
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      socketRef.current?.close();
    };
  }, []);

  useEffect(() => {
    if (consultation?.status !== 'in_processing') {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void refetchConsultation();
      if (shouldLoadReview) {
        void reviewQuery.refetch();
      }
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [consultation?.status, refetchConsultation, reviewQuery, shouldLoadReview]);

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
          const status = String(payload.data.status ?? '');
          if (status === 'recording') {
            setRecordingState('recording');
          }
          if (status === 'paused') {
            setRecordingState('paused');
          }
          if (status === 'processing' || status === 'error') {
            setRecordingState('disconnected');
          }
          setSessionMessage(String(payload.data.message ?? 'Sessão conectada.'));
          return;
        }

        if (payload.event === 'session.warning') {
          setSessionMessage(String(payload.data.message ?? 'Aviso de sessão.'));
          return;
        }

        if (payload.event === 'session.ended') {
          setSessionMessage(String(payload.data.message ?? 'Sessão encerrada.'));
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
          return;
        }

        if (payload.event === 'autofill.candidate') {
          const fieldKey = String(payload.data.field_key ?? '') as WorkspaceFieldKey;
          if (!WORKSPACE_FIELDS.some((field) => field.key === fieldKey)) {
            return;
          }
          setProvisionalAutofill((current) => ({
            ...current,
            [fieldKey]: {
              fieldKey,
              candidateValue: String(payload.data.candidate_value ?? ''),
              confidence: Number(payload.data.confidence ?? 0),
              evidenceExcerpt: String(payload.data.evidence_excerpt ?? ''),
            },
          }));
          return;
        }

        if (payload.event === 'insight.provisional') {
          const insightId = String(payload.data.insight_id ?? '');
          setProvisionalInsights((current) => {
            if (current.some((item) => item.insightId === insightId)) {
              return current;
            }

            return [
              ...current,
              {
                insightId,
                category: String(payload.data.category ?? 'documentation_gap') as ProvisionalInsightItem['category'],
                text: String(payload.data.text ?? ''),
                severity: String(payload.data.severity ?? 'informative') as ProvisionalInsightItem['severity'],
                evidenceExcerpt: String(payload.data.evidence_excerpt ?? ''),
              },
            ];
          });
        }
      };

      socket.onerror = () => {
        setSessionMessage('Conexão com o servidor perdida. Use o botão de reconectar.');
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
      throw new ApiError('Seu navegador não suporta captura de áudio.', 400, 'microphone_unsupported');
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
        const sample = Math.max(-1, Math.min(1, inputData[i]));
        pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      }

      const bytes = new Uint8Array(pcm16.buffer);
      let binary = '';
      const chunkSize = 0x8000;
      for (let index = 0; index < bytes.length; index += chunkSize) {
        const chunk = bytes.subarray(index, index + chunkSize);
        binary += String.fromCharCode(...chunk);
      }
      scribe.sendAudio(btoa(binary));
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
    setFeedback(null);
    setSessionMessage(null);
    setRecordingState('connecting');
    setTranscript([]);
    setPartialText('');
    setProvisionalAutofill({});
    setProvisionalInsights([]);

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
        setSessionMessage(`Erro de transcrição: ${event.message}`);
      });

      scribe.onClose(() => {
        setSessionMessage('Conexão com a transcrição encerrada.');
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
      setSessionMessage('Sessão de gravação iniciada.');
      await refetchConsultation();
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Falha ao iniciar sessão de gravação.');
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
    setSessionMessage('Gravação pausada.');
  }

  function handleResume() {
    const stream = mediaStreamRef.current;
    const scribe = scribeRef.current;

    if (!stream || !scribe) {
      setError('Não foi possível retomar a gravação.');
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
    setSessionMessage('Gravação retomada.');
  }

  async function confirmStopRecording() {
    if (!consultationId) {
      return;
    }

    setIsEndSessionDialogOpen(false);
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
      setRecordingState('disconnected');
      await refetchConsultation();
    }
  }

  async function handleReconnect() {
    if (!sessionRef.current) {
      setError('Nenhuma sessão ativa para reconectar.');
      return;
    }

    connectBackendWebSocket(sessionRef.current);
  }

  const reviewFieldDefaults = useMemo(
    () => deriveWorkspaceFields(review?.medical_history.content),
    [review],
  );
  const summaryDefaultText = useMemo(
    () => summaryContentToText(review?.summary.content),
    [review],
  );
  const activeDraft = workspaceDraft?.consultationId === consultationId ? workspaceDraft : null;
  const currentFieldValues = useMemo(() => {
    const draftFields = activeDraft?.fields ?? emptyWorkspaceFields();
    const resolved = emptyWorkspaceFields();

    for (const field of WORKSPACE_FIELDS) {
      if (activeDraft && field.key in draftFields) {
        resolved[field.key] = draftFields[field.key];
        continue;
      }

      if (reviewFieldDefaults[field.key]) {
        resolved[field.key] = reviewFieldDefaults[field.key];
        continue;
      }

      const provisionalValue = provisionalAutofill[field.key]?.candidateValue;
      resolved[field.key] = provisionalValue ?? '';
    }

    return resolved;
  }, [activeDraft?.fields, provisionalAutofill, reviewFieldDefaults]);
  const summaryText = activeDraft?.summaryText ?? summaryDefaultText;

  const patient = patientDetailQuery.data?.patient;
  const patientName = patient?.name ?? consultation?.patient.name ?? '';
  const patientCpf = patient?.cpf ?? 'CPF indisponível';
  const canStartRecording = consultation?.actions.can_start_recording ?? false;
  const canStopRecording = consultation?.actions.can_stop_recording ?? false;
  const canEditReview = consultation?.actions.can_edit_review ?? false;
  const canFinalize = consultation?.actions.can_finalize ?? false;
  const canExport = consultation?.actions.can_export ?? false;

  const consultationError = consultationQuery.error;
  const patientError = patientDetailQuery.error;
  const reviewError = reviewQuery.error;
  const queryError =
    consultationError || patientError || reviewError
      ? consultationError instanceof ApiError
        ? consultationError.message
        : patientError instanceof ApiError
          ? patientError.message
          : reviewError instanceof ApiError
            ? reviewError.message
            : 'Não foi possível carregar o workspace da consulta.'
      : null;

  const completenessWarning =
    review?.medical_history.completeness_warning || review?.summary.completeness_warning;

  const statusLabel = useMemo(() => {
    if (!consultation) {
      return 'indisponível';
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

  const transcriptRows = useMemo(() => {
    if (transcript.length > 0 || partialText) {
      return transcript;
    }

    return (review?.transcript?.segments ?? []).map((segment, index) => ({
      id: `review-${index}`,
      speaker: segment.speaker,
      text: segment.text,
      isFinal: true,
    }));
  }, [partialText, review, transcript]);

  const mergedInsights = useMemo(() => {
    const mappedReviewInsights = (review?.insights ?? []).map((insight) => ({
      kind: 'review' as const,
      id: insight.insight_id,
      category: insight.category,
      description: insight.description,
      evidenceText: insight.evidence[0]?.text ?? '',
      insight,
    }));
    const mappedProvisionalInsights = provisionalInsights
      .filter((item) => !mappedReviewInsights.some((reviewInsight) => reviewInsight.id === item.insightId))
      .map((item) => ({
        kind: 'provisional' as const,
        id: item.insightId,
        category: item.category,
        description: item.text,
        evidenceText: item.evidenceExcerpt,
      }));

    return [...mappedReviewInsights, ...mappedProvisionalInsights];
  }, [provisionalInsights, review]);

  function updateInsightAction(insight: ReviewInsight, action: 'accept' | 'dismiss' | 'edit') {
    setInsightActions((current) => ({
      ...current,
      [insight.insight_id]: {
        action,
        note: current[insight.insight_id]?.note ?? insight.physician_note ?? '',
      },
    }));
  }

  function updateInsightNote(insight: ReviewInsight, note: string) {
    setInsightActions((current) => ({
      ...current,
      [insight.insight_id]: {
        action: current[insight.insight_id]?.action ?? 'edit',
        note,
      },
    }));
  }

  function updateField(fieldKey: WorkspaceFieldKey, value: string) {
    setWorkspaceDraft({
      consultationId,
      fields: {
        ...currentFieldValues,
        [fieldKey]: value,
      },
      summaryText,
    });
  }

  function updateSummaryText(nextSummaryText: string) {
    setWorkspaceDraft({
      consultationId,
      fields: currentFieldValues,
      summaryText: nextSummaryText,
    });
  }

  async function handleSaveChanges(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consultationId || !review) {
      return;
    }

    setError(null);
    setFeedback(null);

    try {
      const payload = buildReviewUpdatePayload(
        currentFieldValues,
        summaryText,
        insightActions,
        review.medical_history.content,
        review.summary.content,
      );
      await updateReviewMutation.mutateAsync(payload);
      setFeedback('Alterações salvas com sucesso.');
      setWorkspaceDraft(null);
      await Promise.all([consultationQuery.refetch(), reviewQuery.refetch()]);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Não foi possível salvar as alterações.');
      }
    }
  }

  async function handleFinalize() {
    if (!consultationId) {
      return;
    }

    if (!finalizationConfirmed) {
      setError('Confirme a finalização antes de continuar.');
      return;
    }

    setError(null);
    setFeedback(null);

    try {
      await finalizeMutation.mutateAsync();
      setFeedback('Consulta finalizada com sucesso.');
      await Promise.all([consultationQuery.refetch(), reviewQuery.refetch()]);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Não foi possível finalizar a consulta.');
      }
    }
  }

  async function handleExport() {
    if (!consultationId) {
      return;
    }

    setError(null);
    setFeedback(null);

    try {
      const response = await exportMutation.mutateAsync();
      setExportResult(response);
      setFeedback('Exportação gerada com sucesso.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Não foi possível gerar a exportação.');
      }
    }
  }

  return (
    <div className="page-grid review-layout">
      <aside className="stack page-sidebar">
        <Card
          title={uiConfig?.labels.live_session_header ?? 'Sessão ao vivo'}
          actions={<RouterLink className="ds-link" to="/consultations">Voltar para consultas</RouterLink>}
        >
          {consultationQuery.isPending ? <Loader label="Carregando consulta" /> : null}

          {!consultationQuery.isPending && consultation ? (
            <>
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
                <Chip tone={recordingStateTone}>Gravacao: {recordingStateLabel}</Chip>
                {consultation.status === 'finalized' ? <Chip tone="success">Somente leitura</Chip> : null}
              </div>

              <div className="nested-form">
                <TextField label="Paciente" value={patientName} readOnly />
                <TextField label="CPF" value={patientCpf} readOnly />
                <TextField label="Data da consulta" value={consultation.scheduled_date} readOnly />
              </div>
            </>
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

          {consultation?.status === 'in_processing' ? (
            <Alert tone="info">
              O áudio já foi encerrado. O workspace continuará nesta tela enquanto a geração do rascunho é concluída.
            </Alert>
          ) : null}

          {queryError ? <Alert tone="danger">{queryError}</Alert> : null}
          {sessionMessage ? <Alert tone="info">{sessionMessage}</Alert> : null}
          {feedback ? <Alert tone="success">{feedback}</Alert> : null}
          {error ? <Alert tone="danger">{error}</Alert> : null}

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
              <Button type="button" variant="secondary" onClick={() => handlePause()}>
                Pausar gravacao
              </Button>
            ) : null}

            {recordingState === 'paused' ? (
              <Button type="button" variant="secondary" onClick={() => handleResume()}>
                Retomar gravacao
              </Button>
            ) : null}

            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsEndSessionDialogOpen(true)}
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
          </div>
        </Card>

        <Card title="Finalização e exportação">
          <label className="checkbox-row" htmlFor="finalization-confirm">
            <input
              id="finalization-confirm"
              type="checkbox"
              checked={finalizationConfirmed}
              onChange={(event) => setFinalizationConfirmed(event.target.checked)}
            />
            Confirmo que revisei o conteúdo e desejo finalizar esta consulta.
          </label>

          <div className="inline-row">
            <Button
              type="button"
              onClick={() => void handleFinalize()}
              disabled={!canFinalize}
              isLoading={finalizeMutation.isPending}
            >
              {finalizeMutation.isPending ? 'Finalizando...' : uiConfig?.labels.finalize_button ?? 'Finalizar'}
            </Button>

            <Button
              type="button"
              variant="secondary"
              onClick={() => void handleExport()}
              disabled={!canExport}
              isLoading={exportMutation.isPending}
            >
              {exportMutation.isPending ? 'Gerando exportação...' : uiConfig?.labels.export_button ?? 'Exportar'}
            </Button>
          </div>

          {exportResult ? (
            <p>
              Exportação pronta: <UiLink href={exportResult.export_url}>baixar PDF</UiLink>
            </p>
          ) : null}
        </Card>

        {isEndSessionDialogOpen ? (
          <Card title="Encerrar gravação agora?" role="dialog" aria-modal="true">
            <Text tone="muted">
              A sessão será encerrada e o processamento continuará neste mesmo workspace para revisão.
            </Text>
            <div className="inline-row">
              <Button type="button" variant="danger" onClick={() => void confirmStopRecording()}>
                Confirmar encerramento
              </Button>
              <Button type="button" variant="ghost" onClick={() => setIsEndSessionDialogOpen(false)}>
                Continuar gravando
              </Button>
            </div>
          </Card>
        ) : null}
      </aside>

      <form className="stack page-main-panel" onSubmit={handleSaveChanges}>
        <Card title="Anamnese">
          <Text tone="muted">
            Conteúdo gerado por IA e sempre sujeito à revisão médica. Campos em rascunho aparecem com evidência quando disponível.
          </Text>

          {completenessWarning ? (
            <Alert tone="warning">
              {uiConfig?.labels.completeness_warning ??
                'Alguns campos podem estar incompletos. Revise com atenção.'}
            </Alert>
          ) : null}

          <div className="stack">
            {WORKSPACE_FIELDS.map((field) => {
              const autofill = provisionalAutofill[field.key];
              return (
                <div key={field.key} className="nested-panel">
                  <TextAreaField
                    label={field.label}
                    value={currentFieldValues[field.key]}
                    onChange={(event) => updateField(field.key, event.target.value)}
                    rows={field.rows}
                    disabled={!canEditReview}
                    helpText={
                      autofill
                        ? `Evidência: ${autofill.evidenceExcerpt}`
                        : canEditReview
                          ? undefined
                          : 'O rascunho pode ser acompanhado aqui durante a sessão e editado após a geração.'
                    }
                  />

                  <div className="inline-row">
                    {autofill ? <Chip tone="info">Preenchido pela IA</Chip> : null}
                    {autofill ? (
                      <Chip tone="warning">Rascunho {Math.round(autofill.confidence * 100)}%</Chip>
                    ) : null}
                    {review?.status === 'finalized' ? <Chip tone="success">Finalizado</Chip> : null}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <Card title="Transcrição">
          {transcriptRows.length === 0 && !partialText ? (
            <EmptyState
              title="Aguardando transcricao"
              description="A transcrição aparecerá aqui durante a sessão."
            />
          ) : (
            <ul className="transcript-list">
              {transcriptRows.map((item) => (
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

        <Card title="Resumo da consulta">
          <TextAreaField
            label="Resumo da consulta"
            value={summaryText}
            onChange={(event) => updateSummaryText(event.target.value)}
            rows={10}
            disabled={!canEditReview}
            helpText="Use JSON válido se quiser preservar a estrutura original do resumo gerado."
          />
        </Card>

        <Card title="Insights para revisão">
          {mergedInsights.length === 0 ? (
            <EmptyState
              title="Nenhum insight disponível"
              description="Os sinais de revisão aparecerão aqui conforme a transcrição e o rascunho avançarem."
            />
          ) : (
            <ul className="insight-list">
              {mergedInsights.map((item) => {
                const categoryLabel = uiConfig?.insight_categories?.[item.category]?.label ?? item.category;
                const reviewInsight = item.kind === 'review' ? item.insight : null;
                const selectedAction = reviewInsight ? insightActions[reviewInsight.insight_id]?.action : null;
                const note = reviewInsight
                  ? insightActions[reviewInsight.insight_id]?.note ?? reviewInsight.physician_note ?? ''
                  : '';

                return (
                  <li key={item.id} className="nested-panel">
                    <div className="inline-row">
                      <Chip tone={item.kind === 'provisional' ? 'info' : 'warning'}>{categoryLabel}</Chip>
                      {item.kind === 'provisional' ? <Chip tone="warning">Provisório</Chip> : null}
                    </div>

                    <p>{item.description}</p>
                    {item.evidenceText ? (
                      <ul className="evidence-list">
                        <li>{item.evidenceText}</li>
                      </ul>
                    ) : null}

                    {reviewInsight ? (
                      <>
                        <div className="inline-row">
                          <Chip
                            type="button"
                            selected={selectedAction === 'accept'}
                            onClick={() => updateInsightAction(reviewInsight, 'accept')}
                            disabled={!canEditReview}
                          >
                            Aceitar
                          </Chip>
                          <Chip
                            type="button"
                            selected={selectedAction === 'dismiss'}
                            tone="danger"
                            onClick={() => updateInsightAction(reviewInsight, 'dismiss')}
                            disabled={!canEditReview}
                          >
                            Descartar
                          </Chip>
                          <Chip
                            type="button"
                            selected={selectedAction === 'edit'}
                            tone="info"
                            onClick={() => updateInsightAction(reviewInsight, 'edit')}
                            disabled={!canEditReview}
                          >
                            Editar
                          </Chip>
                        </div>

                        <TextAreaField
                          label="Observação do médico (opcional)"
                          rows={2}
                          value={note}
                          onChange={(event) => updateInsightNote(reviewInsight, event.target.value)}
                          placeholder="Observação do médico (opcional)"
                          disabled={!canEditReview}
                        />
                      </>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <div className="inline-row">
          <Button
            type="submit"
            disabled={!canEditReview || !review}
            isLoading={updateReviewMutation.isPending}
          >
            {updateReviewMutation.isPending ? 'Salvando...' : 'Salvar alterações'}
          </Button>
        </div>
      </form>
    </div>
  );
}
