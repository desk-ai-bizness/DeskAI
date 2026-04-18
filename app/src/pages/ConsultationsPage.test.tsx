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
  });

  it('shows create-locked message when entitlement denies creation', async () => {
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
          can_create_consultation: false,
          consultations_remaining: 0,
          consultations_used_this_month: 10,
          max_duration_minutes: 30,
          export_enabled: true,
          trial_expired: false,
          trial_days_remaining: 0,
        },
      },
      uiConfig: {
        labels: {
          consultation_list_title: 'Consultas',
          new_consultation_button: 'Nova consulta',
        },
      },
    });

    render(
      <QueryTestProvider>
        <MemoryRouter>
          <ConsultationsPage />
        </MemoryRouter>
      </QueryTestProvider>,
    );

    expect(
      await screen.findByText('A criação de consultas está bloqueada para este usuário no momento.'),
    ).toBeInTheDocument();
  });
});
