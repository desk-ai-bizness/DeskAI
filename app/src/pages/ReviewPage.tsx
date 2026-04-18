import { FormEvent, useMemo, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import {
  useConsultationDetailQuery,
  useExportConsultationMutation,
  useFinalizeConsultationMutation,
  useReviewQuery,
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
} from '../components/ui';
import type {
  ExportView,
  ReviewInsight,
  ReviewView,
  UpdateReviewRequest,
} from '../types/contracts';
import { toPrettyJson } from '../utils/format';

function normalizeTranscript(review: ReviewView): Array<{ speaker: string; text: string }> {
  if (!review.transcript?.segments) {
    return [];
  }

  return review.transcript.segments.map((segment) => ({
    speaker: segment.speaker,
    text: segment.text,
  }));
}

function buildReviewUpdatePayload(
  medicalHistoryText: string,
  summaryText: string,
  insightActions: Record<string, { action: 'accept' | 'dismiss' | 'edit'; note: string }>,
): UpdateReviewRequest {
  const payload: UpdateReviewRequest = {
    summary: summaryText,
    insights: [],
  };

  const trimmedMedicalHistory = medicalHistoryText.trim();
  if (trimmedMedicalHistory.length > 0) {
    payload.medical_history = JSON.parse(trimmedMedicalHistory) as Record<string, unknown>;
  }

  payload.insights = Object.entries(insightActions).map(([insightId, actionConfig]) => ({
    insight_id: insightId,
    action: actionConfig.action,
    physician_note: actionConfig.note || undefined,
  }));

  return payload;
}

export function ReviewPage() {
  const { consultationId = '' } = useParams();
  const { uiConfig } = useAuth();

  const [reviewDraft, setReviewDraft] = useState<{
    consultationId: string;
    medicalHistoryText: string;
    summaryText: string;
  } | null>(null);
  const [insightActions, setInsightActions] = useState<
    Record<string, { action: 'accept' | 'dismiss' | 'edit'; note: string }>
  >({});

  const [exportResult, setExportResult] = useState<ExportView | null>(null);
  const [finalizationConfirmed, setFinalizationConfirmed] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const consultationQuery = useConsultationDetailQuery(consultationId);
  const reviewQuery = useReviewQuery(consultationId);
  const updateReviewMutation = useUpdateReviewMutation(consultationId);
  const finalizeMutation = useFinalizeConsultationMutation(consultationId);
  const exportMutation = useExportConsultationMutation(consultationId);
  const consultation = consultationQuery.data ?? null;
  const review = reviewQuery.data ?? null;
  const isLoading = consultationQuery.isPending || reviewQuery.isPending;
  const queryError =
    consultationQuery.error || reviewQuery.error
      ? consultationQuery.error instanceof ApiError
        ? consultationQuery.error.message
        : reviewQuery.error instanceof ApiError
          ? reviewQuery.error.message
          : 'Nao foi possivel carregar os dados de revisao.'
      : null;

  const defaultMedicalHistoryText = useMemo(
    () => (review ? toPrettyJson(review.medical_history.content) : ''),
    [review],
  );
  const defaultSummaryText = useMemo(
    () => (review ? toPrettyJson(review.summary.content) : ''),
    [review],
  );
  const activeReviewDraft = reviewDraft?.consultationId === consultationId ? reviewDraft : null;
  const medicalHistoryText = activeReviewDraft?.medicalHistoryText ?? defaultMedicalHistoryText;
  const summaryText = activeReviewDraft?.summaryText ?? defaultSummaryText;

  const sectionOrder = uiConfig?.review_screen.section_order ?? [
    'transcript',
    'medical_history',
    'summary',
    'insights',
  ] as const;
  const sectionConfig = uiConfig?.review_screen.sections ?? {
    transcript: { title: 'Transcricao', editable: false, visible: true },
    medical_history: { title: 'Historia Clinica', editable: true, visible: true },
    summary: { title: 'Resumo da Consulta', editable: true, visible: true },
    insights: { title: 'Insights', editable: true, visible: true },
  };

  const transcriptRows = review ? normalizeTranscript(review) : [];

  const canSave = consultation?.actions.can_edit_review ?? false;
  const canFinalize = consultation?.actions.can_finalize ?? false;
  const canExport = consultation?.actions.can_export ?? false;

  const completenessWarning =
    review?.medical_history.completeness_warning || review?.summary.completeness_warning;

  const statusLabel = useMemo(() => {
    if (!consultation) {
      return 'indisponivel';
    }

    return uiConfig?.status_labels?.[consultation.status] ?? consultation.status;
  }, [consultation, uiConfig]);

  async function handleSaveChanges(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consultationId) {
      return;
    }

    setError(null);
    setFeedback(null);

    try {
      const payload = buildReviewUpdatePayload(medicalHistoryText, summaryText, insightActions);
      await updateReviewMutation.mutateAsync(payload);
      setReviewDraft(null);
      setFeedback('Alteracoes salvas com sucesso.');
      await Promise.all([consultationQuery.refetch(), reviewQuery.refetch()]);
    } catch (requestError) {
      if (requestError instanceof SyntaxError) {
        setError('Historia clinica invalida. Use um JSON valido.');
      } else if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel salvar as alteracoes.');
      }
    }
  }

  async function handleFinalize() {
    if (!consultationId) {
      return;
    }

    if (!finalizationConfirmed) {
      setError('Confirme a finalizacao antes de continuar.');
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
        setError('Nao foi possivel finalizar a consulta.');
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
      setFeedback('Exportacao gerada com sucesso.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel gerar a exportacao.');
      }
    }
  }

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

  function updateMedicalHistoryText(nextMedicalHistoryText: string) {
    setReviewDraft({
      consultationId,
      medicalHistoryText: nextMedicalHistoryText,
      summaryText,
    });
  }

  function updateSummaryText(nextSummaryText: string) {
    setReviewDraft({
      consultationId,
      medicalHistoryText,
      summaryText: nextSummaryText,
    });
  }

  return (
    <div className="page-grid review-layout">
      <aside className="stack page-sidebar">
        <Card
          title={uiConfig?.labels.review_title ?? 'Revisao da consulta'}
          actions={(
            <RouterLink className="ds-link" to={`/consultations/${consultationId}/live`}>
              Voltar para sessao ao vivo
            </RouterLink>
          )}
        >

          {isLoading ? <Loader label="Carregando revisao" /> : null}

          {!isLoading ? (
            <>
              <Chip tone="info">Status: {statusLabel}</Chip>
              <Text tone="muted">{uiConfig?.labels.ai_disclaimer ?? 'Conteudo gerado por IA e sempre revisavel.'}</Text>
              {completenessWarning ? (
                <Alert tone="warning">
                  {uiConfig?.labels.completeness_warning ??
                    'Alguns campos podem estar incompletos. Revise com atencao.'}
                </Alert>
              ) : null}
              {queryError ? <Alert tone="danger">{queryError}</Alert> : null}
              {feedback ? <Alert tone="success">{feedback}</Alert> : null}
              {error ? (
                <Alert tone="danger">
                  {error}
                </Alert>
              ) : null}
            </>
          ) : null}
        </Card>

        <Card title="Finalizacao e exportacao">
          <label className="checkbox-row" htmlFor="finalization-confirm">
            <input
              id="finalization-confirm"
              type="checkbox"
              checked={finalizationConfirmed}
              onChange={(event) => setFinalizationConfirmed(event.target.checked)}
            />
            Confirmo que revisei o conteudo e desejo finalizar esta consulta.
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
              {exportMutation.isPending ? 'Gerando exportacao...' : uiConfig?.labels.export_button ?? 'Exportar'}
            </Button>
          </div>

          {exportResult ? (
            <p>
              Exportacao pronta: <UiLink href={exportResult.export_url}>baixar PDF</UiLink>
            </p>
          ) : null}
        </Card>
      </aside>

      {!isLoading && review ? (
        <form className="stack page-main-panel" onSubmit={handleSaveChanges}>
          {sectionOrder.map((sectionKey) => {
            if (!sectionConfig[sectionKey].visible) {
              return null;
            }

            if (sectionKey === 'transcript') {
              return (
                <Card key={sectionKey} title={sectionConfig.transcript.title}>
                  {transcriptRows.length === 0 ? (
                    <EmptyState
                      title="Transcricao indisponivel"
                      description="Transcricao indisponivel no payload atual."
                    />
                  ) : (
                    <ul className="transcript-list">
                      {transcriptRows.map((segment, index) => (
                        <li key={`${segment.speaker}-${index}`}>
                          <strong>{segment.speaker}:</strong> {segment.text}
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              );
            }

            if (sectionKey === 'medical_history') {
              return (
                <Card key={sectionKey} title={sectionConfig.medical_history.title}>
                  <TextAreaField
                    label="Conteudo da historia clinica"
                    value={medicalHistoryText}
                    onChange={(event) => updateMedicalHistoryText(event.target.value)}
                    rows={12}
                    disabled={!canSave}
                  />
                </Card>
              );
            }

            if (sectionKey === 'summary') {
              return (
                <Card key={sectionKey} title={sectionConfig.summary.title}>
                  <TextAreaField
                    label="Conteudo do resumo"
                    value={summaryText}
                    onChange={(event) => updateSummaryText(event.target.value)}
                    rows={8}
                    disabled={!canSave}
                  />
                </Card>
              );
            }

            return (
              <Card key={sectionKey} title={sectionConfig.insights.title}>
                {review.insights.length === 0 ? (
                  <EmptyState
                    title="Nenhum insight"
                    description="Nenhum insight disponivel."
                  />
                ) : (
                  <ul className="insight-list">
                    {review.insights.map((insight) => {
                      const categoryLabel = uiConfig?.insight_categories[insight.category]?.label;
                      const action = insightActions[insight.insight_id]?.action;
                      const note = insightActions[insight.insight_id]?.note ?? insight.physician_note ?? '';

                      return (
                        <li key={insight.insight_id}>
                          <p>
                            <Chip tone="warning">{categoryLabel ?? insight.category}</Chip>
                          </p>
                          <p>{insight.description}</p>

                          {insight.evidence.length > 0 ? (
                            <ul className="evidence-list">
                              {insight.evidence.map((evidence, index) => (
                                <li key={`${insight.insight_id}-${index}`}>{evidence.text}</li>
                              ))}
                            </ul>
                          ) : null}

                          <div className="inline-row">
                            <Chip
                              type="button"
                              selected={action === 'accept'}
                              onClick={() => updateInsightAction(insight, 'accept')}
                              disabled={!canSave}
                            >
                              Aceitar
                            </Chip>
                            <Chip
                              type="button"
                              selected={action === 'dismiss'}
                              tone="danger"
                              onClick={() => updateInsightAction(insight, 'dismiss')}
                              disabled={!canSave}
                            >
                              Descartar
                            </Chip>
                            <Chip
                              type="button"
                              selected={action === 'edit'}
                              tone="info"
                              onClick={() => updateInsightAction(insight, 'edit')}
                              disabled={!canSave}
                            >
                              Editar
                            </Chip>
                          </div>

                          <TextAreaField
                            label="Observacao do medico (opcional)"
                            rows={2}
                            value={note}
                            onChange={(event) => updateInsightNote(insight, event.target.value)}
                            placeholder="Observacao do medico (opcional)"
                            disabled={!canSave}
                          />
                        </li>
                      );
                    })}
                  </ul>
                )}
              </Card>
            );
          })}

          <div className="inline-row">
            <Button type="submit" disabled={!canSave} isLoading={updateReviewMutation.isPending}>
              {updateReviewMutation.isPending ? 'Salvando...' : 'Salvar alteracoes'}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
