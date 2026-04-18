import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError } from '../api/client';
import {
  createConsultation,
  createPatient,
  listConsultations,
  listPatients,
} from '../api/endpoints';
import { useAuth } from '../auth/use-auth';
import type { ConsultationView, PatientView } from '../types/contracts';
import { toPtBrDate, toPtBrDateTime } from '../utils/format';

export function ConsultationsPage() {
  const navigate = useNavigate();
  const { profile, uiConfig } = useAuth();

  const [consultations, setConsultations] = useState<ConsultationView[]>([]);
  const [patients, setPatients] = useState<PatientView[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [patientId, setPatientId] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [notes, setNotes] = useState('');
  const [isCreatingConsultation, setIsCreatingConsultation] = useState(false);

  const [showPatientForm, setShowPatientForm] = useState(false);
  const [newPatientName, setNewPatientName] = useState('');
  const [newPatientDob, setNewPatientDob] = useState('');
  const [isCreatingPatient, setIsCreatingPatient] = useState(false);

  const statusLabels = uiConfig?.status_labels;

  async function loadData() {
    setIsLoading(true);
    setError(null);

    try {
      const [consultationResponse, patientResponse] = await Promise.all([
        listConsultations(),
        listPatients(),
      ]);
      setConsultations(consultationResponse.consultations);
      setPatients(patientResponse.patients);
      if (patientResponse.patients.length > 0 && !patientId) {
        setPatientId(patientResponse.patients[0].patient_id);
      }
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Nao foi possivel carregar as consultas.');
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
    // patientId is intentionally excluded to avoid infinite reload loops.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canCreateConsultation = profile?.entitlements.can_create_consultation ?? false;

  const trialStateMessage = useMemo(() => {
    if (!profile) {
      return null;
    }

    if (profile.entitlements.trial_expired) {
      return 'Seu periodo de teste expirou. Voce ainda pode revisar consultas ja criadas.';
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

    if (!patientId) {
      setError('Selecione um paciente antes de criar a consulta.');
      return;
    }

    if (!scheduledDate) {
      setError('Informe a data da consulta.');
      return;
    }

    setIsCreatingConsultation(true);

    try {
      const created = await createConsultation({
        patient_id: patientId,
        specialty: 'general_practice',
        scheduled_date: scheduledDate,
        notes,
      });
      setFeedback('Consulta criada com sucesso.');
      setNotes('');
      await loadData();
      navigate(`/consultations/${created.consultation_id}/live`);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Erro ao criar consulta.');
      }
    } finally {
      setIsCreatingConsultation(false);
    }
  }

  async function handleCreatePatient() {
    setFeedback(null);
    setError(null);
    setIsCreatingPatient(true);

    try {
      const createdPatient = await createPatient({
        name: newPatientName,
        date_of_birth: newPatientDob,
      });
      setPatients((current) => [...current, createdPatient]);
      setPatientId(createdPatient.patient_id);
      setNewPatientName('');
      setNewPatientDob('');
      setShowPatientForm(false);
      setFeedback('Paciente criado com sucesso.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError('Erro ao criar paciente.');
      }
    } finally {
      setIsCreatingPatient(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel page-span-2">
        <header className="panel-header">
          <h2>{uiConfig?.labels.consultation_list_title ?? 'Consultas'}</h2>
          <button type="button" className="secondary-button" onClick={() => void loadData()}>
            Atualizar
          </button>
        </header>

        <div className="stats-grid">
          <article className="stat-tile">
            <h3>Consultas no mes</h3>
            <p>{profile?.entitlements.consultations_used_this_month ?? '--'}</p>
          </article>
          <article className="stat-tile">
            <h3>Consultas restantes</h3>
            <p>{profile?.entitlements.consultations_remaining ?? '--'}</p>
          </article>
          <article className="stat-tile">
            <h3>Duracao maxima</h3>
            <p>{profile?.entitlements.max_duration_minutes ?? '--'} min</p>
          </article>
        </div>

        {trialStateMessage ? <p className="hint">{trialStateMessage}</p> : null}
        {feedback ? <p className="inline-success">{feedback}</p> : null}
        {error ? (
          <p className="inline-error" role="alert">
            {error}
          </p>
        ) : null}
      </section>

      <section className="panel">
        <h2>{uiConfig?.labels.new_consultation_button ?? 'Nova consulta'}</h2>

        {!canCreateConsultation ? (
          <p className="hint">
            A criacao de consultas esta bloqueada para este usuario no momento.
          </p>
        ) : (
          <form className="form-grid" onSubmit={handleCreateConsultation}>
            <label htmlFor="patient-select">Paciente</label>
            <select
              id="patient-select"
              value={patientId}
              onChange={(event) => setPatientId(event.target.value)}
              required
            >
              {patients.length === 0 ? <option value="">Nenhum paciente cadastrado</option> : null}
              {patients.map((patient) => (
                <option value={patient.patient_id} key={patient.patient_id}>
                  {patient.name} ({toPtBrDate(patient.date_of_birth)})
                </option>
              ))}
            </select>

            <div className="inline-row">
              <button
                type="button"
                className="ghost-button"
                onClick={() => setShowPatientForm((current) => !current)}
              >
                {showPatientForm ? 'Cancelar novo paciente' : 'Cadastrar novo paciente'}
              </button>
            </div>

            {showPatientForm ? (
              <div className="nested-form">
                <label htmlFor="new-patient-name">Nome do paciente</label>
                <input
                  id="new-patient-name"
                  value={newPatientName}
                  onChange={(event) => setNewPatientName(event.target.value)}
                  required
                />

                <label htmlFor="new-patient-dob">Data de nascimento</label>
                <input
                  id="new-patient-dob"
                  type="date"
                  value={newPatientDob}
                  onChange={(event) => setNewPatientDob(event.target.value)}
                  required
                />

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void handleCreatePatient()}
                  disabled={isCreatingPatient}
                >
                  {isCreatingPatient ? 'Salvando paciente...' : 'Salvar paciente'}
                </button>
              </div>
            ) : null}

            <label htmlFor="scheduled-date">Data da consulta</label>
            <input
              id="scheduled-date"
              type="date"
              value={scheduledDate}
              onChange={(event) => setScheduledDate(event.target.value)}
              required
            />

            <label htmlFor="notes">Notas (opcional)</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
            />

            <button type="submit" className="primary-button" disabled={isCreatingConsultation}>
              {isCreatingConsultation ? 'Criando consulta...' : 'Criar consulta'}
            </button>
          </form>
        )}
      </section>

      <section className="panel">
        <h2>Consultas recentes</h2>
        {isLoading ? <p>Carregando consultas...</p> : null}

        {!isLoading && consultations.length === 0 ? (
          <p className="hint">Nenhuma consulta encontrada para este medico.</p>
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
                    <span className="badge">{statusLabel}</span>
                  </div>
                  <div className="inline-row">
                    <Link to={`/consultations/${consultation.consultation_id}/live`}>
                      Sessao ao vivo
                    </Link>
                    <Link to={`/consultations/${consultation.consultation_id}/review`}>
                      Revisao
                    </Link>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
