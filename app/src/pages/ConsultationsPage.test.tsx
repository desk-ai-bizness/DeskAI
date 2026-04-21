import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryTestProvider } from '../test/query-wrapper';
import { ConsultationsPage } from './ConsultationsPage';

const listConsultationsMock = vi.fn();
const listPatientsMock = vi.fn();
const createConsultationMock = vi.fn();
const createPatientMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  listConsultations: (...args: unknown[]) => listConsultationsMock(...args),
  listPatients: (...args: unknown[]) => listPatientsMock(...args),
  createConsultation: (...args: unknown[]) => createConsultationMock(...args),
  createPatient: (...args: unknown[]) => createPatientMock(...args),
}));

vi.mock('../auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

describe('ConsultationsPage', () => {
  beforeEach(() => {
    listConsultationsMock.mockReset();
    listPatientsMock.mockReset();
    createConsultationMock.mockReset();
    createPatientMock.mockReset();

    useAuthMock.mockReturnValue({
      profile: {
        user: {
          doctor_id: 'doc-1',
          name: 'Dra. Maria',
          email: 'maria@example.com',
          plan_type: 'free_trial',
          clinic_id: 'clinic-1',
          clinic_name: 'Clínica Centro',
        },
        entitlements: {
          can_create_consultation: true,
          consultations_remaining: 10,
          consultations_used_this_month: 0,
          max_duration_minutes: 30,
          export_enabled: true,
          trial_expired: false,
          trial_days_remaining: 12,
        },
      },
      uiConfig: {
        labels: {
          consultation_list_title: 'Consultas',
          new_consultation_button: 'Nova consulta',
        },
      },
    });

    listConsultationsMock.mockResolvedValue({
      consultations: [],
      total_count: 0,
      page: 1,
      page_size: 20,
    });
    listPatientsMock.mockResolvedValue({ patients: [] });
  });

  it('shows empty state when there are no consultations', async () => {
    render(
      <QueryTestProvider>
        <MemoryRouter>
          <ConsultationsPage />
        </MemoryRouter>
      </QueryTestProvider>,
    );

    expect(await screen.findByText('Nenhuma consulta encontrada para este médico.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Atualizar' })).toHaveClass('ds-button');
    expect(screen.getByRole('heading', { name: 'Consultas', level: 2 }).closest('.ds-card')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Nenhuma consulta', level: 2 })).toBeInTheDocument();
    expect(screen.queryByLabelText('Paciente')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Criar consulta' })).not.toBeInTheDocument();
  });

  it('renders consultation history links without using the legacy review route as the primary path', async () => {
    listConsultationsMock.mockResolvedValue({
      consultations: [
        {
          consultation_id: 'cons-1',
          patient: { patient_id: 'pat-1', name: 'Paciente A', cpf: '529.***.***-25' },
          doctor_id: 'doc-1',
          clinic_id: 'clinic-1',
          specialty: 'general_practice',
          status: 'started',
          scheduled_date: '2026-04-20',
          created_at: '2026-04-20T10:00:00Z',
          updated_at: '2026-04-20T11:00:00Z',
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 20,
    });

    render(
      <QueryTestProvider>
        <MemoryRouter>
          <ConsultationsPage />
        </MemoryRouter>
      </QueryTestProvider>,
    );

    expect(await screen.findByText('Paciente A')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Abrir consulta' })).toHaveAttribute(
      'href',
      '/consultations/cons-1/live',
    );
    expect(screen.queryByRole('link', { name: 'Revisão' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Paciente')).not.toBeInTheDocument();
    expect(screen.queryByText('Cadastrar novo paciente')).not.toBeInTheDocument();
  });
});
