import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryTestProvider } from '../test/query-wrapper';
import { PatientDetailPage } from './PatientDetailPage';

const getPatientDetailMock = vi.fn();
const createConsultationMock = vi.fn();
const useAuthMock = vi.fn();
const navigateMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  getPatientDetail: (...args: unknown[]) => getPatientDetailMock(...args),
  createConsultation: (...args: unknown[]) => createConsultationMock(...args),
}));

vi.mock('../auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe('PatientDetailPage', () => {
  beforeEach(() => {
    getPatientDetailMock.mockReset();
    createConsultationMock.mockReset();
    navigateMock.mockReset();
    useAuthMock.mockReturnValue({
      profile: {
        entitlements: {
          can_create_consultation: true,
          consultations_remaining: 10,
          consultations_used_this_month: 2,
          max_duration_minutes: 30,
          export_enabled: true,
          trial_expired: false,
          trial_days_remaining: 12,
        },
      },
      uiConfig: {
        status_labels: {
          started: 'Iniciada',
          recording: 'Gravando',
          paused: 'Pausada',
          in_processing: 'Em processamento',
          processing_failed: 'Falha no processamento',
          draft_generated: 'Rascunho gerado',
          under_physician_review: 'Em revisão médica',
          finalized: 'Finalizada',
        },
      },
    });
  });

  it('shows patient detail and current-doctor history', async () => {
    getPatientDetailMock.mockResolvedValue({
      patient: {
        patient_id: 'pat-1',
        name: 'Maria da Silva',
        cpf: '529.***.***-25',
        date_of_birth: null,
        clinic_id: 'clinic-1',
        created_at: '2026-04-20T10:00:00Z',
      },
      history: [
        {
          consultation_id: 'cons-1',
          status: 'finalized',
          scheduled_date: '2026-04-20',
          finalized_at: '2026-04-20T12:00:00Z',
          preview: {
            summary: 'Consulta de retorno sem novas queixas.',
          },
        },
      ],
    });

    render(
      <QueryTestProvider>
        <MemoryRouter initialEntries={['/patients/pat-1']}>
          <Routes>
            <Route path="/patients/:patientId" element={<PatientDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryTestProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Maria da Silva' })).toBeInTheDocument();
    expect(screen.getByText('529.***.***-25')).toBeInTheDocument();
    expect(screen.getByText('Consulta de retorno sem novas queixas.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Iniciar nova consulta' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Abrir consulta' })).toHaveAttribute(
      'href',
      '/consultations/cons-1/live',
    );
    expect(screen.queryByRole('link', { name: 'Revisão' })).not.toBeInTheDocument();
  });

  it('starts a new consultation for the selected patient using today as the scheduled date', async () => {
    getPatientDetailMock.mockResolvedValue({
      patient: {
        patient_id: 'pat-1',
        name: 'Maria da Silva',
        cpf: '529.***.***-25',
        date_of_birth: null,
        clinic_id: 'clinic-1',
        created_at: '2026-04-20T10:00:00Z',
      },
      history: [],
    });
    createConsultationMock.mockResolvedValue({
      consultation_id: 'cons-22',
      patient: { patient_id: 'pat-1', name: 'Maria da Silva' },
      doctor_id: 'doc-1',
      clinic_id: 'clinic-1',
      specialty: 'general_practice',
      status: 'started',
      scheduled_date: '2026-04-21',
      created_at: '2026-04-21T10:00:00Z',
      updated_at: '2026-04-21T10:00:00Z',
    });

    render(
      <QueryTestProvider>
        <MemoryRouter initialEntries={['/patients/pat-1']}>
          <Routes>
            <Route path="/patients/:patientId" element={<PatientDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryTestProvider>,
    );

    await userEvent.click(await screen.findByRole('button', { name: 'Iniciar nova consulta' }));

    await waitFor(() =>
      expect(createConsultationMock.mock.calls[0]?.[0]).toEqual({
        patient_id: 'pat-1',
        specialty: 'general_practice',
        scheduled_date: '2026-04-21',
      }),
    );
    expect(navigateMock).toHaveBeenCalledWith('/consultations/cons-22/live');
  });
});
