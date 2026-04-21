import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryTestProvider } from '../test/query-wrapper';
import { ConsultationEntryPage } from './ConsultationEntryPage';

const listPatientsMock = vi.fn();
const createPatientMock = vi.fn();
const createConsultationMock = vi.fn();
const useAuthMock = vi.fn();
const navigateMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  listPatients: (...args: unknown[]) => listPatientsMock(...args),
  createPatient: (...args: unknown[]) => createPatientMock(...args),
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

describe('ConsultationEntryPage', () => {
  beforeEach(() => {
    listPatientsMock.mockReset();
    createPatientMock.mockReset();
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
        labels: {
          new_consultation_button: 'Nova consulta',
        },
      },
    });

    listPatientsMock.mockResolvedValue({ patients: [] });
  });

  it('renders the staged patient-first choices and empty search state', async () => {
    render(
      <QueryTestProvider>
        <MemoryRouter>
          <ConsultationEntryPage />
        </MemoryRouter>
      </QueryTestProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Nova consulta' })).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Selecionar paciente existente' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Novo paciente' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Selecionar paciente existente' }));

    expect(await screen.findByLabelText('Buscar paciente por nome ou CPF')).toBeInTheDocument();
    expect(await screen.findByText('Nenhum paciente encontrado para a busca informada.')).toBeInTheDocument();
  });

  it('searches existing patients by name or CPF and links to patient detail', async () => {
    listPatientsMock.mockImplementation(async (term?: string) => {
      if (term === '529.982') {
        return {
          patients: [
            {
              patient_id: 'pat-1',
              name: 'Maria da Silva',
              cpf: '529.***.***-25',
              date_of_birth: null,
              clinic_id: 'clinic-1',
              created_at: '2026-04-20T10:00:00Z',
            },
          ],
        };
      }

      return { patients: [] };
    });

    render(
      <QueryTestProvider>
        <MemoryRouter>
          <ConsultationEntryPage />
        </MemoryRouter>
      </QueryTestProvider>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Selecionar paciente existente' }));
    await userEvent.type(screen.getByLabelText('Buscar paciente por nome ou CPF'), '529.982');

    await waitFor(() => expect(listPatientsMock).toHaveBeenLastCalledWith('529.982'));

    const patientLink = await screen.findByRole('link', { name: /Abrir paciente Maria da Silva/i });
    expect(patientLink).toHaveAttribute('href', '/patients/pat-1');
    expect(screen.getByText('529.***.***-25')).toBeInTheDocument();
  });

  it('creates a new patient and immediately starts a consultation with today as the scheduled date', async () => {
    createPatientMock.mockResolvedValue({
      patient_id: 'pat-9',
      name: 'Paciente Novo',
      cpf: '390.***.***-05',
      date_of_birth: null,
      clinic_id: 'clinic-1',
      created_at: '2026-04-20T10:00:00Z',
    });
    createConsultationMock.mockResolvedValue({
      consultation_id: 'cons-9',
      patient: { patient_id: 'pat-9', name: 'Paciente Novo' },
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
        <MemoryRouter>
          <ConsultationEntryPage />
        </MemoryRouter>
      </QueryTestProvider>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Novo paciente' }));
    await userEvent.type(screen.getByLabelText('Nome do paciente'), 'Paciente Novo');
    await userEvent.type(screen.getByLabelText('CPF'), '390.533.447-05');
    await userEvent.click(screen.getByRole('button', { name: 'Salvar e iniciar consulta' }));

    await waitFor(() =>
      expect(createPatientMock.mock.calls[0]?.[0]).toEqual({
        name: 'Paciente Novo',
        cpf: '390.533.447-05',
      }),
    );
    await waitFor(() =>
      expect(createConsultationMock.mock.calls[0]?.[0]).toEqual({
        patient_id: 'pat-9',
        specialty: 'general_practice',
        scheduled_date: '2026-04-21',
      }),
    );
    expect(navigateMock).toHaveBeenCalledWith('/consultations/cons-9/live');
  });
});
