import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryTestProvider } from '../test/query-wrapper';
import { LiveConsultationPage } from './LiveConsultationPage';

const getConsultationDetailMock = vi.fn();
const startSessionMock = vi.fn();
const endSessionMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  getConsultationDetail: (...args: unknown[]) => getConsultationDetailMock(...args),
  startSession: (...args: unknown[]) => startSessionMock(...args),
  endSession: (...args: unknown[]) => endSessionMock(...args),
}));

vi.mock('../auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

describe('LiveConsultationPage', () => {
  beforeEach(() => {
    getConsultationDetailMock.mockReset();
    startSessionMock.mockReset();
    endSessionMock.mockReset();

    useAuthMock.mockReturnValue({
      uiConfig: {
        labels: {
          live_session_header: 'Sessão ao vivo',
          start_recording_button: 'Iniciar gravação',
          stop_recording_button: 'Parar gravação',
        },
        status_labels: {
          started: 'Iniciada',
          recording: 'Gravando',
          in_processing: 'Em Processamento',
          processing_failed: 'Falha no Processamento',
          draft_generated: 'Rascunho Gerado',
          under_physician_review: 'Em Revisão Médica',
          finalized: 'Finalizada',
        },
      },
    });

    getConsultationDetailMock.mockResolvedValue({
      consultation_id: 'cons-1',
      patient: { patient_id: 'pat-1', name: 'Paciente A' },
      doctor_id: 'doc-1',
      clinic_id: 'clinic-1',
      specialty: 'general_practice',
      status: 'started',
      scheduled_date: '2026-04-11',
      created_at: '2026-04-11T00:00:00Z',
      updated_at: '2026-04-11T00:00:00Z',
      session: {
        session_id: null,
        started_at: null,
        ended_at: null,
        duration_seconds: null,
      },
      processing: {
        started_at: null,
        completed_at: null,
        error_details: null,
      },
      has_draft: false,
      finalized_at: null,
      finalized_by: null,
      actions: {
        can_start_recording: true,
        can_stop_recording: false,
        can_retry_processing: false,
        can_open_review: false,
        can_edit_review: false,
        can_finalize: false,
        can_export: false,
      },
      warnings: [],
    });

    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockRejectedValue(new Error('denied')),
      },
    });
  });

  it('shows microphone denied error when permission is rejected', async () => {
    render(
      <QueryTestProvider>
        <MemoryRouter initialEntries={['/consultations/cons-1/live']}>
          <Routes>
            <Route path="/consultations/:consultationId/live" element={<LiveConsultationPage />} />
          </Routes>
        </MemoryRouter>
      </QueryTestProvider>,
    );

    const button = await screen.findByRole('button', { name: 'Iniciar gravação' });
    expect(button).toHaveClass('ds-button');
    expect(screen.getByRole('heading', { name: 'Sessão ao vivo', level: 2 }).closest('.ds-card')).toBeInTheDocument();

    await userEvent.click(button);

    expect(await screen.findByText('Permissão de microfone negada.')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('ds-alert');
    expect(startSessionMock).not.toHaveBeenCalled();
  });
});
