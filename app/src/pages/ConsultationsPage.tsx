import { FormEvent, useMemo, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { ApiError } from '../api/client';
import {
  useConsultationsQuery,
  useCreateConsultationMutation,
  useCreatePatientMutation,
  usePatientsQuery,
} from '../api/query-hooks';
import { useAuth } from '../auth/use-auth';
import {
  Alert,
  Button,
  Card,
  Chip,
  EmptyState,
  Loader,
  SelectField,
  Text,
  TextAreaField,
  TextField,
} from '../components/ui';
import type { ConsultationView, PatientView } from '../types/contracts';
import { toPtBrDate, toPtBrDateTime } from '../utils/format';

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  return fallback;
}

export function ConsultationsPage() {
  const navigate = useNavigate();
  const { profile, uiConfig } = useAuth();

  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [patientId, setPatientId] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [notes, setNotes] = useState('');

  const [showPatientForm, setShowPatientForm] = useState(false);
  const [newPatientName, setNewPatientName] = useState('');
  const [newPatientCpf, setNewPatientCpf] = useState('');
  const [newPatientDob, setNewPatientDob] = useState('');

  const statusLabels = uiConfig?.status_labels;
  const consultationsQuery = useConsultationsQuery();
  const patientsQuery = usePatientsQuery();
  const createConsultationMutation = useCreateConsultationMutation();
  const createPatientMutation = useCreatePatientMutation();

  const consultations: ConsultationView[] = consultationsQuery.data?.consultations ?? [];
  const patients: PatientView[] = patientsQuery.data?.patients ?? [];
  const selectedPatientId = patientId || patients[0]?.patient_id || '';
  const queryError =
    consultationsQuery.error || patientsQuery.error
      ? getRequestErrorMessage(
        consultationsQuery.error ?? patientsQuery.error,
        'Não foi possível carregar as consultas.',
      )
      : null;
  const isLoading = consultationsQuery.isPending || patientsQuery.isPending;

  const canCreateConsultation = profile?.entitlements.can_create_consultation ?? false;

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

  async function handleCreateConsultation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    setError(null);

    if (!selectedPatientId) {
      setError('Selecione um paciente antes de criar a consulta.');
      return;
    }

    if (!scheduledDate) {
      setError('Informe a data da consulta.');
      return;
    }

    try {
      const created = await createConsultationMutation.mutateAsync({
        patient_id: selectedPatientId,
        specialty: 'general_practice',
        scheduled_date: scheduledDate,
        notes,
      });
      setFeedback('Consulta criada com sucesso.');
      setNotes('');
      navigate(`/consultations/${created.consultation_id}/live`);
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError, 'Erro ao criar consulta.'));
    }
  }

  async function handleCreatePatient() {
    setFeedback(null);
    setError(null);

    try {
      const createdPatient = await createPatientMutation.mutateAsync({
        name: newPatientName,
        cpf: newPatientCpf,
        date_of_birth: newPatientDob || null,
      });
      setPatientId(createdPatient.patient_id);
      setNewPatientName('');
      setNewPatientCpf('');
      setNewPatientDob('');
      setShowPatientForm(false);
      setFeedback('Paciente criado com sucesso.');
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError, 'Erro ao criar paciente.'));
    }
  }

  return (
    <div className="page-grid">
      <Card
        className="page-span-2"
        title={uiConfig?.labels.consultation_list_title ?? 'Consultas'}
        actions={(
          <Button
            type="button"
            variant="secondary"
            isLoading={consultationsQuery.isFetching || patientsQuery.isFetching}
            onClick={() => {
              void consultationsQuery.refetch();
              void patientsQuery.refetch();
            }}
          >
            Atualizar
          </Button>
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
        {feedback ? <Alert tone="success">{feedback}</Alert> : null}
        {queryError ? <Alert tone="danger">{queryError}</Alert> : null}
        {error ? (
          <Alert tone="danger">
            {error}
          </Alert>
        ) : null}
      </Card>

      <Card title={uiConfig?.labels.new_consultation_button ?? 'Nova consulta'}>

        {!canCreateConsultation ? (
          <Alert tone="warning">
            A criação de consultas está bloqueada para este usuário no momento.
          </Alert>
        ) : (
          <form className="form-grid" onSubmit={handleCreateConsultation}>
            <SelectField
              id="patient-select"
              label="Paciente"
              value={selectedPatientId}
              onChange={(event) => setPatientId(event.target.value)}
              required
            >
              {patients.length === 0 ? <option value="">Nenhum paciente cadastrado</option> : null}
              {patients.map((patient) => (
                <option value={patient.patient_id} key={patient.patient_id}>
                  {patient.name} ({patient.cpf})
                </option>
              ))}
            </SelectField>

            <div className="inline-row">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setShowPatientForm((current) => !current)}
              >
                {showPatientForm ? 'Cancelar novo paciente' : 'Cadastrar novo paciente'}
              </Button>
            </div>

            {showPatientForm ? (
              <div className="nested-form">
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

                <TextField
                  id="new-patient-dob"
                  label="Data de nascimento (opcional)"
                  type="date"
                  value={newPatientDob}
                  onChange={(event) => setNewPatientDob(event.target.value)}
                />

                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void handleCreatePatient()}
                  isLoading={createPatientMutation.isPending}
                >
                  {createPatientMutation.isPending ? 'Salvando paciente...' : 'Salvar paciente'}
                </Button>
              </div>
            ) : null}

            <TextField
              id="scheduled-date"
              label="Data da consulta"
              type="date"
              value={scheduledDate}
              onChange={(event) => setScheduledDate(event.target.value)}
              required
            />

            <TextAreaField
              id="notes"
              label="Notas (opcional)"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
            />

            <Button type="submit" isLoading={createConsultationMutation.isPending}>
              {createConsultationMutation.isPending ? 'Criando consulta...' : 'Criar consulta'}
            </Button>
          </form>
        )}
      </Card>

      <Card title="Consultas recentes">
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
                      Sessão ao vivo
                    </RouterLink>
                    <RouterLink className="ds-link" to={`/consultations/${consultation.consultation_id}/review`}>
                      Revisão
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
