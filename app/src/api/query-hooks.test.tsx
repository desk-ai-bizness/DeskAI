import { QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createAppQueryClient,
  queryKeys,
  useCreateConsultationMutation,
  useExportConsultationMutation,
  useFinalizeConsultationMutation,
  useUpdateReviewMutation,
} from './query-hooks';

const createConsultationMock = vi.fn();
const updateReviewMock = vi.fn();
const finalizeConsultationMock = vi.fn();
const exportConsultationMock = vi.fn();

vi.mock('./endpoints', () => ({
  createConsultation: (...args: unknown[]) => createConsultationMock(...args),
  updateReview: (...args: unknown[]) => updateReviewMock(...args),
  finalizeConsultation: (...args: unknown[]) => finalizeConsultationMock(...args),
  exportConsultation: (...args: unknown[]) => exportConsultationMock(...args),
}));

describe('query hooks', () => {
  beforeEach(() => {
    createConsultationMock.mockReset();
    updateReviewMock.mockReset();
    finalizeConsultationMock.mockReset();
    exportConsultationMock.mockReset();
  });

  it('uses conservative in-memory query defaults', () => {
    const queryClient = createAppQueryClient();

    expect(queryClient.getDefaultOptions().queries?.staleTime).toBe(15_000);
    expect(queryClient.getDefaultOptions().queries?.retry).toBe(false);
    expect(queryClient.getDefaultOptions().mutations?.retry).toBe(false);
  });

  it('invalidates consultation and profile cache after consultation creation', async () => {
    const queryClient = createAppQueryClient();
    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

    createConsultationMock.mockResolvedValue({
      consultation_id: 'cons-1',
      patient: { patient_id: 'pat-1', name: 'Paciente A' },
      doctor_id: 'doc-1',
      clinic_id: 'clinic-1',
      specialty: 'general_practice',
      status: 'started',
      scheduled_date: '2026-04-18',
      created_at: '2026-04-18T00:00:00Z',
      updated_at: '2026-04-18T00:00:00Z',
    });

    function wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useCreateConsultationMutation(), { wrapper });

    result.current.mutate({
      patient_id: 'pat-1',
      specialty: 'general_practice',
      scheduled_date: '2026-04-18',
      notes: 'Retorno',
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: queryKeys.consultations.all });
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: queryKeys.currentUser() });
  });

  it('updates review cache and invalidates consultation detail after review save', async () => {
    const queryClient = createAppQueryClient();
    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');
    const reviewResponse = {
      consultation_id: 'cons-1',
      status: 'under_physician_review',
      medical_history: {
        content: { chief_complaint: 'Dor abdominal' },
        edited_by_physician: true,
        completeness_warning: false,
      },
      summary: {
        content: 'Resumo revisado.',
        edited_by_physician: true,
        completeness_warning: false,
      },
      insights: [],
    };

    updateReviewMock.mockResolvedValue(reviewResponse);

    function wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useUpdateReviewMutation('cons-1'), { wrapper });

    result.current.mutate({
      medical_history: { chief_complaint: 'Dor abdominal' },
      summary: 'Resumo revisado.',
      insights: [],
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(queryClient.getQueryData(queryKeys.review('cons-1'))).toEqual(reviewResponse);
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: queryKeys.consultations.detail('cons-1'),
    });
  });

  it('invalidates finalized consultation and review cache after finalization', async () => {
    const queryClient = createAppQueryClient();
    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

    finalizeConsultationMock.mockResolvedValue({
      consultation_id: 'cons-1',
      status: 'finalized',
      finalized_at: '2026-04-18T12:00:00Z',
      finalized_by: 'doc-1',
    });

    function wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useFinalizeConsultationMutation('cons-1'), { wrapper });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: queryKeys.consultations.all });
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: queryKeys.consultations.detail('cons-1'),
    });
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: queryKeys.review('cons-1') });
  });

  it('uses mutation state for export requests without persisting export data globally', async () => {
    const queryClient = createAppQueryClient();

    exportConsultationMock.mockResolvedValue({
      consultation_id: 'cons-1',
      export_url: 'https://example.test/export.pdf',
      expires_at: '2026-04-18T12:10:00Z',
      format: 'pdf',
    });

    function wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useExportConsultationMutation('cons-1'), { wrapper });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(exportConsultationMock).toHaveBeenCalledWith('cons-1');
    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
    expect(result.current.data?.export_url).toBe('https://example.test/export.pdf');
  });
});
