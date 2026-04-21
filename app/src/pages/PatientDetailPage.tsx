import { useMemo, useState } from 'react';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { useCreateConsultationMutation, usePatientDetailQuery } from '../api/query-hooks';
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
import { getLocalDateString } from '../utils/date';
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

export function PatientDetailPage() {
  const navigate = useNavigate();
  const { patientId = '' } = useParams();
  const { profile, uiConfig } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const patientDetailQuery = usePatientDetailQuery(patientId);
  const createConsultationMutation = useCreateConsultationMutation();
  const patientDetail = patientDetailQuery.data ?? null;
  const statusLabels = uiConfig?.status_labels;
  const canCreateConsultation = profile?.entitlements.can_create_consultation ?? false;

  const historyTitle = useMemo(() => {
    if (!patientDetail) {
      return 'Histórico do paciente';
    }

    return `Histórico com ${patientDetail.patient.name}`;
  }, [patientDetail]);

  async function handleStartConsultation() {
    if (!patientDetail) {
      return;
    }

    setError(null);

    try {
      const consultation = await createConsultationMutation.mutateAsync({
        patient_id: patientDetail.patient.patient_id,
        specialty: 'general_practice',
        scheduled_date: getLocalDateString(),
      });
      navigate(`/consultations/${consultation.consultation_id}/live`);
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError, 'Não foi possível iniciar a consulta.'));
    }
  }

  return (
    <div className="page-grid">
      <Card
        title="Paciente"
        actions={(
          <RouterLink className="ds-link" to="/nova-consulta">
            Voltar para nova consulta
          </RouterLink>
        )}
      >
        {patientDetailQuery.isPending ? <Loader label="Carregando paciente" /> : null}
        {patientDetailQuery.error ? (
          <Alert tone="danger">
            {getRequestErrorMessage(patientDetailQuery.error, 'Não foi possível carregar o paciente.')}
          </Alert>
        ) : null}

        {!patientDetailQuery.isPending && patientDetail ? (
          <div className="stack">
            <div>
              <Text tone="muted">Paciente selecionado</Text>
              <h2>{patientDetail.patient.name}</h2>
              <Text tone="muted">{patientDetail.patient.cpf}</Text>
            </div>

            {error ? <Alert tone="danger">{error}</Alert> : null}
            {!canCreateConsultation ? (
              <Alert tone="warning">
                A criação de consultas está bloqueada para este usuário no momento.
              </Alert>
            ) : (
              <Button
                type="button"
                isLoading={createConsultationMutation.isPending}
                onClick={() => void handleStartConsultation()}
              >
                Iniciar nova consulta
              </Button>
            )}
          </div>
        ) : null}
      </Card>

      <Card title={historyTitle}>
        {patientDetailQuery.isPending ? <Loader label="Carregando histórico" /> : null}

        {!patientDetailQuery.isPending && patientDetail && patientDetail.history.length === 0 ? (
          <EmptyState
            title="Sem consultas anteriores"
            description="Este paciente ainda não tem histórico de consultas com o médico atual."
          />
        ) : null}

        {!patientDetailQuery.isPending && patientDetail && patientDetail.history.length > 0 ? (
          <ul className="consultation-list">
            {patientDetail.history.map((item) => (
              <li key={item.consultation_id} className="consultation-item">
                <div>
                  <strong>{toPtBrDate(item.scheduled_date)}</strong>
                  <p>
                    Status: <Chip tone="info">{statusLabels?.[item.status] ?? item.status}</Chip>
                  </p>
                  {item.finalized_at ? <p>Finalizada em {toPtBrDateTime(item.finalized_at)}</p> : null}
                  {item.preview?.summary ? <p>{item.preview.summary}</p> : null}
                </div>
                <div className="inline-row">
                  <RouterLink className="ds-link" to={`/consultations/${item.consultation_id}/live`}>
                    {getWorkspaceLinkLabel(item.status)}
                  </RouterLink>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </Card>
    </div>
  );
}
