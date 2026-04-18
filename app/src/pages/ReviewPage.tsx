import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import {
  exportConsultation,
  finalizeConsultation,
  getConsultationDetail,
  getReview,
  updateReview,
} from '../api/endpoints';
import { useAuth } from '../auth/use-auth';
import type {
  ConsultationDetailView,
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

  const [consultation, setConsultation] = useState<ConsultationDetailView | null>(null);
  const [review, setReview] = useState<ReviewView | null>(null);
  const [medicalHistoryText, setMedicalHistoryText] = useState('');
  const [summaryText, setSummaryText] = useState('');
  const [insightActions, setInsightActions] = useState<
    Record<string, { action: 'accept' | 'dismiss' | 'edit'; note: string }>
  >({});

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const [exportResult, setExportResult] = useState<ExportView | null>(null);
  const [finalizationConfirmed, setFinalizationConfirmed] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!consultationId) {
      return;
    }

    void (async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [detailResponse, reviewResponse] = await Promise.all([
          getConsultationDetail(consultationId),
          getReview(consultationId),
        ]);

        setConsultation(detailResponse);
        setReview(reviewResponse);
        setMedicalHistoryText(toPrettyJson(reviewResponse.medical_history.content));
        setSummaryText(toPrettyJson(reviewResponse.summary.content));
      } catch (requestError) {
        if (requestError instanceof ApiError) {
          setError(requestError.message);
        } else {
          setError('Nao foi possivel carregar os dados de revisao.');
        }
      } finally {
        setIsLoading(false);
      }
    })();
  }, [consultationId]);

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

  async function reloadReviewState() {
    if (!consultationId) {
      return;
    }

    const [detailResponse, reviewResponse] = await Promise.all([
      getConsultationDetail(consultationId),
      getReview(consultationId),
    ]);

    setConsultation(detailResponse);
    setReview(reviewResponse);
    setMedicalHistoryText(toPrettyJson(reviewResponse.medical_history.content));
    setSummaryText(toPrettyJson(reviewResponse.summary.content));
  }

  async function handleSaveChanges(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consultationId) {
      return;
    }

    setError(null);
    setFeedback(null);
    setIsSaving(true);

    try {
      const payload = buildReviewUpdatePayload(medicalHistoryText, summaryText, insightActions);
      const response = await updateReview(consultationId, payload);
      setReview(response);
      setFeedback('Alteracoes salvas com sucesso.');
      await reloadReviewState();
    } catch (requestError) {
      if (requestError instanceof SyntaxError) {
        setError('Historia clinica invalida. Use um JSON valido.');
      } else if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel salvar as alteracoes.');
      }
    } finally {
      setIsSaving(false);
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
    setIsFinalizing(true);

    try {
      await finalizeConsultation(consultationId);
      setFeedback('Consulta finalizada com sucesso.');
      await reloadReviewState();
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel finalizar a consulta.');
      }
    } finally {
      setIsFinalizing(false);
    }
  }

  async function handleExport() {
    if (!consultationId) {
      return;
    }

    setError(null);
    setFeedback(null);
    setIsExporting(true);

    try {
      const response = await exportConsultation(consultationId);
      setExportResult(response);
      setFeedback('Exportacao gerada com sucesso.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel gerar a exportacao.');
      }
    } finally {
      setIsExporting(false);
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

  return (
    <div className="page-grid review-layout">
      <aside className="stack page-sidebar">
        <section className="panel">
          <header className="panel-header">
            <h2>{uiConfig?.labels.review_title ?? 'Revisao da consulta'}</h2>
            <Link to={`/consultations/${consultationId}/live`}>Voltar para sessao ao vivo</Link>
          </header>

          {isLoading ? <p>Carregando revisao...</p> : null}

          {!isLoading ? (
            <>
              <p>
                <strong>Status:</strong> {statusLabel}
              </p>
              <p className="hint">{uiConfig?.labels.ai_disclaimer ?? 'Conteudo gerado por IA e sempre revisavel.'}</p>
              {completenessWarning ? (
                <p className="warning-banner">
                  {uiConfig?.labels.completeness_warning ??
                    'Alguns campos podem estar incompletos. Revise com atencao.'}
                </p>
              ) : null}
              {feedback ? <p className="inline-success">{feedback}</p> : null}
              {error ? (
                <p className="inline-error" role="alert">
                  {error}
                </p>
              ) : null}
            </>
          ) : null}
        </section>

        <section className="panel">
          <h2>Finalizacao e exportacao</h2>

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
            <button
              type="button"
              className="primary-button"
              onClick={() => void handleFinalize()}
              disabled={!canFinalize || isFinalizing}
            >
              {isFinalizing ? 'Finalizando...' : uiConfig?.labels.finalize_button ?? 'Finalizar'}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => void handleExport()}
              disabled={!canExport || isExporting}
            >
              {isExporting ? 'Gerando exportacao...' : uiConfig?.labels.export_button ?? 'Exportar'}
            </button>
          </div>

          {exportResult ? (
            <p>
              Exportacao pronta: <a href={exportResult.export_url}>baixar PDF</a>
            </p>
          ) : null}
        </section>
      </aside>

      {!isLoading && review ? (
        <form className="panel stack page-main-panel" onSubmit={handleSaveChanges}>
          {sectionOrder.map((sectionKey) => {
            if (!sectionConfig[sectionKey].visible) {
              return null;
            }

            if (sectionKey === 'transcript') {
              return (
                <section key={sectionKey} className="nested-panel">
                  <h3>{sectionConfig.transcript.title}</h3>
                  {transcriptRows.length === 0 ? (
                    <p className="hint">Transcricao indisponivel no payload atual.</p>
                  ) : (
                    <ul className="transcript-list">
                      {transcriptRows.map((segment, index) => (
                        <li key={`${segment.speaker}-${index}`}>
                          <strong>{segment.speaker}:</strong> {segment.text}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              );
            }

            if (sectionKey === 'medical_history') {
              return (
                <section key={sectionKey} className="nested-panel">
                  <h3>{sectionConfig.medical_history.title}</h3>
                  <textarea
                    value={medicalHistoryText}
                    onChange={(event) => setMedicalHistoryText(event.target.value)}
                    rows={12}
                    disabled={!canSave}
                  />
                </section>
              );
            }

            if (sectionKey === 'summary') {
              return (
                <section key={sectionKey} className="nested-panel">
                  <h3>{sectionConfig.summary.title}</h3>
                  <textarea
                    value={summaryText}
                    onChange={(event) => setSummaryText(event.target.value)}
                    rows={8}
                    disabled={!canSave}
                  />
                </section>
              );
            }

            return (
              <section key={sectionKey} className="nested-panel">
                <h3>{sectionConfig.insights.title}</h3>
                {review.insights.length === 0 ? (
                  <p className="hint">Nenhum insight disponivel.</p>
                ) : (
                  <ul className="insight-list">
                    {review.insights.map((insight) => {
                      const categoryLabel = uiConfig?.insight_categories[insight.category]?.label;
                      const action = insightActions[insight.insight_id]?.action;
                      const note = insightActions[insight.insight_id]?.note ?? insight.physician_note ?? '';

                      return (
                        <li key={insight.insight_id}>
                          <p>
                            <strong>{categoryLabel ?? insight.category}</strong>
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
                            <button
                              type="button"
                              className={action === 'accept' ? 'chip-button selected' : 'chip-button'}
                              onClick={() => updateInsightAction(insight, 'accept')}
                              disabled={!canSave}
                            >
                              Aceitar
                            </button>
                            <button
                              type="button"
                              className={action === 'dismiss' ? 'chip-button selected' : 'chip-button'}
                              onClick={() => updateInsightAction(insight, 'dismiss')}
                              disabled={!canSave}
                            >
                              Descartar
                            </button>
                            <button
                              type="button"
                              className={action === 'edit' ? 'chip-button selected' : 'chip-button'}
                              onClick={() => updateInsightAction(insight, 'edit')}
                              disabled={!canSave}
                            >
                              Editar
                            </button>
                          </div>

                          <textarea
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
              </section>
            );
          })}

          <div className="inline-row">
            <button type="submit" className="primary-button" disabled={isSaving || !canSave}>
              {isSaving ? 'Salvando...' : 'Salvar alteracoes'}
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
