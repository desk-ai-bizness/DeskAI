import { useMemo } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { ApiError } from '../api/client';
import { useConsultationsQuery } from '../api/query-hooks';
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
import type { ConsultationView } from '../types/contracts';
import { toPtBrDate, toPtBrDateTime } from '../utils/format';

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  return fallback;
}

function getWorkspaceLinkLabel(status: string): string {
  if (status === 'recording' || status === 'paused') {
    return 'Sessão ao vivo';
  }

  return 'Abrir consulta';
}

export function ConsultationsPage() {
  const { profile, uiConfig } = useAuth();

  const statusLabels = uiConfig?.status_labels;
  const consultationsQuery = useConsultationsQuery();

  const consultations: ConsultationView[] = consultationsQuery.data?.consultations ?? [];
  const queryError = consultationsQuery.error
    ? getRequestErrorMessage(consultationsQuery.error, 'Não foi possível carregar as consultas.')
    : null;
  const isLoading = consultationsQuery.isPending;

  const trialStateMessage = useMemo(() => {
    if (!profile) {
      return null;
    }

    if (profile.entitlements.trial_expired) {
      return 'Seu período de teste expirou. Você ainda pode revisar consultas já criadas.';
    }

    if (profile.user.plan_type === 'free_trial') {
      return `Dias restantes no teste: ${profile.entitlements.trial_days_remaining}.`;
    }

    return null;
  }, [profile]);

  return (
    <div className="page-grid">
      <Card
        className="page-span-2"
        title={uiConfig?.labels.consultation_list_title ?? 'Consultas'}
        actions={(
          <div className="inline-row">
            <RouterLink className="ds-link" to="/nova-consulta">
              Nova consulta
            </RouterLink>
            <Button
              type="button"
              variant="secondary"
              isLoading={consultationsQuery.isFetching}
              onClick={() => {
                void consultationsQuery.refetch();
              }}
            >
              Atualizar
            </Button>
          </div>
        )}
      >
        <div className="stats-grid">
          <article className="stat-tile">
            <h3>Consultas no mês</h3>
            <p>{profile?.entitlements.consultations_used_this_month ?? '--'}</p>
          </article>
          <article className="stat-tile">
            <h3>Consultas restantes</h3>
            <p>{profile?.entitlements.consultations_remaining ?? '--'}</p>
          </article>
          <article className="stat-tile">
            <h3>Duração máxima</h3>
            <p>{profile?.entitlements.max_duration_minutes ?? '--'} min</p>
          </article>
        </div>

        {trialStateMessage ? <Text tone="muted">{trialStateMessage}</Text> : null}
        {queryError ? <Alert tone="danger">{queryError}</Alert> : null}
      </Card>

      <Card className="page-span-2" title="Consultas recentes">
        {isLoading ? <Loader label="Carregando consultas" /> : null}

        {!isLoading && consultations.length === 0 ? (
          <EmptyState
            title="Nenhuma consulta"
            description="Nenhuma consulta encontrada para este médico."
          />
        ) : null}

        {!isLoading && consultations.length > 0 ? (
          <ul className="consultation-list">
            {consultations.map((consultation) => {
              const statusLabel = statusLabels?.[consultation.status] ?? consultation.status;
              return (
                <li key={consultation.consultation_id} className="consultation-item">
                  <div>
                    <strong>{consultation.patient.name || 'Paciente sem nome'}</strong>
                    <p>
                      Consulta em {toPtBrDate(consultation.scheduled_date)} • Atualizada em{' '}
                      {toPtBrDateTime(consultation.updated_at)}
                    </p>
                    <Chip tone="info">{statusLabel}</Chip>
                  </div>
                  <div className="inline-row">
                    <RouterLink className="ds-link" to={`/consultations/${consultation.consultation_id}/live`}>
                      {getWorkspaceLinkLabel(consultation.status)}
                    </RouterLink>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
      </Card>
    </div>
  );
}
