import { FormEvent, useMemo, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { ApiError } from '../api/client';
import {
  useCreateConsultationMutation,
  useCreatePatientMutation,
  usePatientsQuery,
} from '../api/query-hooks';
import { useAuth } from '../auth/use-auth';
import {
  Alert,
  Button,
  Card,
  EmptyState,
  Loader,
  Text,
  TextField,
} from '../components/ui';
import type { PatientView } from '../types/contracts';
import { getLocalDateString } from '../utils/date';

type EntryStage = 'idle' | 'existing' | 'new';

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  return fallback;
}

export function ConsultationEntryPage() {
  const navigate = useNavigate();
  const { profile, uiConfig } = useAuth();

  const [stage, setStage] = useState<EntryStage>('idle');
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [newPatientName, setNewPatientName] = useState('');
  const [newPatientCpf, setNewPatientCpf] = useState('');

  const patientsQuery = usePatientsQuery(search, stage === 'existing');
  const createPatientMutation = useCreatePatientMutation();
  const createConsultationMutation = useCreateConsultationMutation();

  const patients: PatientView[] = patientsQuery.data?.patients ?? [];
  const canCreateConsultation = profile?.entitlements.can_create_consultation ?? false;
  const trialStateMessage = useMemo(() => {
    if (!profile) {
      return null;
    }

    if (profile.entitlements.trial_expired) {
      return 'Seu período de teste expirou. Você ainda pode revisar consultas já criadas.';
    }

    if (profile.user?.plan_type === 'free_trial') {
      return `Dias restantes no teste: ${profile.entitlements.trial_days_remaining}.`;
    }

    return null;
  }, [profile]);

  async function startConsultationForPatient(patientId: string) {
    const created = await createConsultationMutation.mutateAsync({
      patient_id: patientId,
      specialty: 'general_practice',
      scheduled_date: getLocalDateString(),
    });

    navigate(`/consultations/${created.consultation_id}/live`);
  }

  async function handleNewPatientSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      const patient = await createPatientMutation.mutateAsync({
        name: newPatientName,
        cpf: newPatientCpf,
      });
      await startConsultationForPatient(patient.patient_id);
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError, 'Não foi possível iniciar a nova consulta.'));
    }
  }

  return (
    <div className="page-grid">
      <Card
        className="page-span-2"
        eyebrow="Fluxo principal"
        title={uiConfig?.labels.new_consultation_button ?? 'Nova consulta'}
        actions={(
          <RouterLink className="ds-link" to="/consultations">
            Ver histórico
          </RouterLink>
        )}
      >
        <Text tone="muted">
          Escolha um paciente existente ou cadastre um novo paciente para iniciar a consulta.
        </Text>

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
        {error ? <Alert tone="danger">{error}</Alert> : null}
        {!canCreateConsultation ? (
          <Alert tone="warning">
            A criação de consultas está bloqueada para este usuário no momento.
          </Alert>
        ) : null}
      </Card>

      <Card title="1. Escolha o caminho">
        <div className="stack">
          <Button
            type="button"
            variant={stage === 'existing' ? 'secondary' : 'primary'}
            onClick={() => {
              setStage('existing');
              setError(null);
            }}
          >
            Selecionar paciente existente
          </Button>
          <Button
            type="button"
            variant={stage === 'new' ? 'secondary' : 'primary'}
            onClick={() => {
              setStage('new');
              setError(null);
            }}
          >
            Novo paciente
          </Button>
        </div>
      </Card>

      {stage === 'idle' ? (
        <Card title="2. Próximo passo">
          <EmptyState
            title="Escolha como deseja começar"
            description="Selecione um paciente existente ou cadastre um novo paciente para avançar."
          />
        </Card>
      ) : null}

      {stage === 'existing' ? (
        <Card title="2. Buscar paciente">
          <div className="stack">
            <TextField
              id="patient-search"
              label="Buscar paciente por nome ou CPF"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Ex.: Maria ou 529.982.247-25"
            />

            {patientsQuery.isPending ? <Loader label="Buscando pacientes" /> : null}
            {patientsQuery.error ? (
              <Alert tone="danger">
                {getRequestErrorMessage(patientsQuery.error, 'Não foi possível carregar os pacientes.')}
              </Alert>
            ) : null}

            {!patientsQuery.isPending && !patientsQuery.error && patients.length === 0 ? (
              <EmptyState
                title="Nenhum paciente encontrado"
                description="Nenhum paciente encontrado para a busca informada."
              />
            ) : null}

            {!patientsQuery.isPending && patients.length > 0 ? (
              <ul className="consultation-list">
                {patients.map((patient) => (
                  <li key={patient.patient_id} className="consultation-item">
                    <div>
                      <strong>{patient.name}</strong>
                      <p>{patient.cpf}</p>
                    </div>
                    <RouterLink className="ds-link" to={`/patients/${patient.patient_id}`}>
                      Abrir paciente {patient.name}
                    </RouterLink>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </Card>
      ) : null}

      {stage === 'new' ? (
        <Card title="2. Cadastrar paciente">
          <form className="form-grid" onSubmit={handleNewPatientSubmit}>
            <TextField
              id="new-patient-name"
              label="Nome do paciente"
              value={newPatientName}
              onChange={(event) => setNewPatientName(event.target.value)}
              required
            />
            <TextField
              id="new-patient-cpf"
              label="CPF"
              value={newPatientCpf}
              onChange={(event) => setNewPatientCpf(event.target.value)}
              required
            />
            <Button
              type="submit"
              isLoading={createPatientMutation.isPending || createConsultationMutation.isPending}
            >
              Salvar e iniciar consulta
            </Button>
          </form>
        </Card>
      ) : null}
    </div>
  );
}
