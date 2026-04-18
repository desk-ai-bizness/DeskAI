import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ReviewPage } from './ReviewPage';

const getConsultationDetailMock = vi.fn();
const getReviewMock = vi.fn();
const updateReviewMock = vi.fn();
const finalizeConsultationMock = vi.fn();
const exportConsultationMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock('../api/endpoints', () => ({
  getConsultationDetail: (...args: unknown[]) => getConsultationDetailMock(...args),
  getReview: (...args: unknown[]) => getReviewMock(...args),
  updateReview: (...args: unknown[]) => updateReviewMock(...args),
  finalizeConsultation: (...args: unknown[]) => finalizeConsultationMock(...args),
  exportConsultation: (...args: unknown[]) => exportConsultationMock(...args),
}));

vi.mock('../auth/use-auth', () => ({
  useAuth: () => useAuthMock(),
}));

describe('ReviewPage', () => {
  beforeEach(() => {
    getConsultationDetailMock.mockReset();
    getReviewMock.mockReset();
    updateReviewMock.mockReset();
    finalizeConsultationMock.mockReset();
    exportConsultationMock.mockReset();

    useAuthMock.mockReturnValue({
      uiConfig: {
        labels: {
          review_title: 'Revisao da consulta',
          ai_disclaimer: 'Conteudo gerado por IA — sujeito a revisao medica.',
          completeness_warning: 'Alguns campos podem estar incompletos. Revise antes de finalizar.',
          finalize_button: 'Finalizar',
          export_button: 'Exportar',
        },
        review_screen: {
          section_order: ['transcript', 'medical_history', 'summary', 'insights'],
          sections: {
            transcript: { title: 'Transcricao', editable: false, visible: true },
            medical_history: { title: 'Historia Clinica', editable: true, visible: true },
            summary: { title: 'Resumo da Consulta', editable: true, visible: true },
            insights: { title: 'Insights', editable: true, visible: true },
          },
        },
        insight_categories: {
          documentation_gap: { label: 'Lacuna de Documentacao', icon: 'info', severity: 'low' },
          consistency_issue: { label: 'Problema de Consistencia', icon: 'warning', severity: 'medium' },
          clinical_attention: { label: 'Atencao Clinica', icon: 'alert', severity: 'high' },
        },
        status_labels: {
          started: 'Iniciada',
          recording: 'Gravando',
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
      status: 'under_physician_review',
      scheduled_date: '2026-04-11',
      created_at: '2026-04-11T00:00:00Z',
      updated_at: '2026-04-11T00:00:00Z',
      session: {
        session_id: 'sess-1',
        started_at: '2026-04-11T00:00:00Z',
        ended_at: '2026-04-11T01:00:00Z',
        duration_seconds: 3600,
      },
      processing: {
        started_at: '2026-04-11T01:00:00Z',
        completed_at: '2026-04-11T01:10:00Z',
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
      medical_history: {
        content: {
          chief_complaint: 'Dor abdominal ha 2 dias',
        },
        edited_by_physician: false,
        completeness_warning: true,
      },
      summary: {
        content: 'Resumo inicial da consulta.',
        edited_by_physician: false,
        completeness_warning: true,
      },
      insights: [
        {
          insight_id: 'ins-1',
          category: 'documentation_gap',
          description: 'Nao ha registro da duracao dos sintomas.',
          evidence: [{ text: 'Paciente relata dor abdominal.', start_time: 2, end_time: 5 }],
          status: 'pending',
          physician_note: null,
        },
      ],
    });
  });

  it('renders disclaimer, warning and transcript fallback', async () => {
    render(
      <MemoryRouter initialEntries={['/consultations/cons-1/review']}>
        <Routes>
          <Route path="/consultations/:consultationId/review" element={<ReviewPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText('Conteudo gerado por IA — sujeito a revisao medica.')).toBeInTheDocument();
    expect(
      screen.getByText('Alguns campos podem estar incompletos. Revise antes de finalizar.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Transcricao indisponivel no payload atual.')).toBeInTheDocument();
  });
});
