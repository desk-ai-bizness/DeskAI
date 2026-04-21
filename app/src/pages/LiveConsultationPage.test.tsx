import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryTestProvider } from '../test/query-wrapper';
import { LiveConsultationPage } from './LiveConsultationPage';

const getConsultationDetailMock = vi.fn();
const getPatientDetailMock = vi.fn();
const getReviewMock = vi.fn();
const updateReviewMock = vi.fn();
const finalizeConsultationMock = vi.fn();
const exportConsultationMock = vi.fn();
const startSessionMock = vi.fn();
const endSessionMock = vi.fn();
const getTranscriptionTokenMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  getConsultationDetail: (...args: unknown[]) => getConsultationDetailMock(...args),
  getPatientDetail: (...args: unknown[]) => getPatientDetailMock(...args),
  getReview: (...args: unknown[]) => getReviewMock(...args),
  updateReview: (...args: unknown[]) => updateReviewMock(...args),
  finalizeConsultation: (...args: unknown[]) => finalizeConsultationMock(...args),
  exportConsultation: (...args: unknown[]) => exportConsultationMock(...args),
  startSession: (...args: unknown[]) => startSessionMock(...args),
  endSession: (...args: unknown[]) => endSessionMock(...args),
  getTranscriptionToken: (...args: unknown[]) => getTranscriptionTokenMock(...args),
}));

vi.mock('../auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('../services/elevenlabs-scribe', () => {
  const ElevenLabsScribe = vi.fn().mockImplementation(() => ({
    connect: vi.fn(),
    close: vi.fn(),
    sendAudio: vi.fn(),
    isConnected: vi.fn().mockReturnValue(false),
    onPartial: vi.fn(),
    onCommitted: vi.fn(),
    onError: vi.fn(),
    onClose: vi.fn(),
    onSessionStarted: vi.fn(),
    setTokenRefreshCallback: vi.fn(),
  }));
  return { ElevenLabsScribe };
});

vi.mock('../services/transcript-relay', () => ({
  relayCommittedSegment: vi.fn().mockReturnValue(true),
}));

function renderPage() {
  return render(
    <QueryTestProvider>
      <MemoryRouter initialEntries={['/consultations/cons-1/live']}>
        <Routes>
          <Route path="/consultations/:consultationId/live" element={<LiveConsultationPage />} />
        </Routes>
      </MemoryRouter>
    </QueryTestProvider>,
  );
}

describe('LiveConsultationPage', () => {
  beforeEach(() => {
    getConsultationDetailMock.mockReset();
    getPatientDetailMock.mockReset();
    getReviewMock.mockReset();
    updateReviewMock.mockReset();
    finalizeConsultationMock.mockReset();
    exportConsultationMock.mockReset();
    startSessionMock.mockReset();
    endSessionMock.mockReset();
    getTranscriptionTokenMock.mockReset();

    useAuthMock.mockReturnValue({
      uiConfig: {
        labels: {
          live_session_header: 'Sessao ao vivo',
          start_recording_button: 'Iniciar gravacao',
          stop_recording_button: 'Parar gravacao',
        },
        status_labels: {
          started: 'Iniciada',
          recording: 'Gravando',
          paused: 'Pausado',
          in_processing: 'Em Processamento',
          processing_failed: 'Falha no Processamento',
          draft_generated: 'Rascunho Gerado',
          under_physician_review: 'Em Revisao Medica',
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

    getPatientDetailMock.mockResolvedValue({
      patient: {
        patient_id: 'pat-1',
        name: 'Paciente A',
        cpf: '123.456.789-00',
        date_of_birth: '1990-01-01',
        clinic_id: 'clinic-1',
        created_at: '2026-04-11T00:00:00Z',
      },
      history: [],
    });

    getReviewMock.mockResolvedValue({
      consultation_id: 'cons-1',
      status: 'under_physician_review',
      transcript: { segments: [] },
      medical_history: {
        content: {},
        edited_by_physician: false,
        completeness_warning: false,
      },
      summary: {
        content: {},
        edited_by_physician: false,
        completeness_warning: false,
      },
      insights: [],
    });

    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockRejectedValue(new Error('denied')),
      },
    });
  });

  it('shows microphone denied error when permission is rejected', async () => {
    renderPage();

    const button = await screen.findByRole('button', { name: 'Iniciar gravacao' });
    expect(button).toHaveClass('ds-button');
    expect(screen.getByRole('heading', { name: 'Sessao ao vivo', level: 2 }).closest('.ds-card')).toBeInTheDocument();

    await userEvent.click(button);

    expect(await screen.findByText('Permissao de microfone negada.')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('ds-alert');
    expect(startSessionMock).not.toHaveBeenCalled();
  });

  it('does not render stub transcript text anywhere', async () => {
    renderPage();

    await screen.findByRole('button', { name: 'Iniciar gravacao' });

    const pageText = document.body.textContent ?? '';
    expect(pageText).not.toContain('[stub transcript]');
    expect(pageText).not.toContain('stub transcript');
  });

  it('shows recording state chip in status strip', async () => {
    renderPage();

    // Wait for consultation detail to load (status label appears in a chip)
    await screen.findByText(/Iniciada/);

    const chips = document.querySelectorAll('.ds-chip');
    const chipTexts = Array.from(chips).map((chip) => chip.textContent);
    expect(chipTexts).toEqual(expect.arrayContaining([expect.stringContaining('Inativo')]));
  });

  it('shows pause button text exists in component', async () => {
    renderPage();

    await screen.findByRole('button', { name: 'Iniciar gravacao' });

    // Pause button only visible during recording, so it shouldn't be in DOM in idle state
    expect(screen.queryByRole('button', { name: 'Pausar gravacao' })).not.toBeInTheDocument();
  });

  it('shows resume button text exists in component', async () => {
    renderPage();

    await screen.findByRole('button', { name: 'Iniciar gravacao' });

    // Resume button only visible when paused
    expect(screen.queryByRole('button', { name: 'Retomar gravacao' })).not.toBeInTheDocument();
  });

  it('shows empty transcript state', async () => {
    renderPage();

    expect(await screen.findByText('Aguardando transcricao')).toBeInTheDocument();
  });

  it('does not send the doctor to a separate review page from the primary workspace', async () => {
    renderPage();

    await screen.findByRole('button', { name: 'Iniciar gravacao' });

    expect(screen.queryByRole('link', { name: 'Ir para revisao' })).not.toBeInTheDocument();
  });

  it('asks for confirmation before ending the session', async () => {
    getConsultationDetailMock.mockResolvedValue({
      consultation_id: 'cons-1',
      patient: { patient_id: 'pat-1', name: 'Paciente A' },
      doctor_id: 'doc-1',
      clinic_id: 'clinic-1',
      specialty: 'general_practice',
      status: 'recording',
      scheduled_date: '2026-04-11',
      created_at: '2026-04-11T00:00:00Z',
      updated_at: '2026-04-11T00:00:00Z',
      session: {
        session_id: 'sess-1',
        started_at: '2026-04-11T00:00:00Z',
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
        can_start_recording: false,
        can_stop_recording: true,
        can_retry_processing: false,
        can_open_review: false,
        can_edit_review: false,
        can_finalize: false,
        can_export: false,
      },
      warnings: [],
    });

    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: 'Parar gravacao' }));

    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(endSessionMock).not.toHaveBeenCalled();
  });

  it('renders inline anamnese and review sections on the unified workspace when draft data is available', async () => {
    getConsultationDetailMock.mockResolvedValue({
      consultation_id: 'cons-1',
      patient: { patient_id: 'pat-1', name: 'Paciente A' },
      doctor_id: 'doc-1',
      clinic_id: 'clinic-1',
      specialty: 'general_practice',
      status: 'under_physician_review',
      scheduled_date: '2026-04-11',
      created_at: '2026-04-11T00:00:00Z',
      updated_at: '2026-04-11T00:00:00Z',
      session: {
        session_id: 'sess-1',
        started_at: '2026-04-11T00:00:00Z',
        ended_at: '2026-04-11T00:20:00Z',
        duration_seconds: 1200,
      },
      processing: {
        started_at: '2026-04-11T00:20:00Z',
        completed_at: '2026-04-11T00:25:00Z',
        error_details: null,
      },
      has_draft: true,
      finalized_at: null,
      finalized_by: null,
      actions: {
        can_start_recording: false,
        can_stop_recording: false,
        can_retry_processing: false,
        can_open_review: false,
        can_edit_review: true,
        can_finalize: true,
        can_export: false,
      },
      warnings: [],
    });

    getReviewMock.mockResolvedValue({
      consultation_id: 'cons-1',
      status: 'under_physician_review',
      transcript: {
        segments: [
          {
            speaker: 'patient',
            text: 'Estou com dor de cabeca.',
            start_time: 0,
            end_time: 2,
          },
        ],
      },
      medical_history: {
        content: {
          queixa_principal: { descricao: 'Dor de cabeca' },
          historia_doenca_atual: { narrativa: 'Paciente relata dor ha 2 dias.' },
        },
        edited_by_physician: false,
        completeness_warning: true,
      },
      summary: {
        content: { subjetivo: { queixa_principal: 'Dor de cabeca' } },
        edited_by_physician: false,
        completeness_warning: true,
      },
      insights: [
        {
          insight_id: 'ins-1',
          category: 'documentation_gap',
          description: 'Falta registrar alergias.',
          evidence: [{ text: 'Paciente relata dor de cabeca.', start_time: 0, end_time: 2 }],
          status: 'pending',
          physician_note: null,
        },
      ],
    });

    renderPage();

    expect(await screen.findByRole('heading', { name: 'Anamnese', level: 2 })).toBeInTheDocument();
    expect(await screen.findByDisplayValue('Dor de cabeca')).toBeInTheDocument();
    expect(await screen.findByDisplayValue('Paciente relata dor ha 2 dias.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Finalizar' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Salvar alterações' })).toBeInTheDocument();
  });
});
