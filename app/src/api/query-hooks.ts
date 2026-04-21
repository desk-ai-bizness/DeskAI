import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import {
  createConsultation,
  createPatient,
  endSession,
  exportConsultation,
  finalizeConsultation,
  getConsultationDetail,
  getCurrentUser,
  getPatientDetail,
  getReview,
  getTranscriptionToken,
  getUiConfig,
  listConsultations,
  listPatients,
  startSession,
  updateReview,
} from './endpoints';
import type { UpdateReviewRequest } from '../types/contracts';

export const queryKeys = {
  currentUser: () => ['current-user'] as const,
  uiConfig: () => ['ui-config'] as const,
  patients: {
    all: ['patients'] as const,
    list: (search = '') => ['patients', 'list', search] as const,
    detail: (patientId: string) => ['patients', 'detail', patientId] as const,
  },
  consultations: {
    all: ['consultations'] as const,
    list: () => ['consultations', 'list'] as const,
    detail: (consultationId: string) => ['consultations', 'detail', consultationId] as const,
  },
  review: (consultationId: string) => ['consultations', 'review', consultationId] as const,
};

export function createAppQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        gcTime: 5 * 60_000,
        retry: false,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export function useCurrentUserQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.currentUser(),
    queryFn: getCurrentUser,
    enabled,
  });
}

export function useUiConfigQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.uiConfig(),
    queryFn: getUiConfig,
    enabled,
    staleTime: 60_000,
  });
}

export function usePatientsQuery(search = '', enabled = true) {
  return useQuery({
    queryKey: queryKeys.patients.list(search),
    queryFn: () => listPatients(search),
    enabled,
  });
}

export function usePatientDetailQuery(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.detail(patientId),
    queryFn: () => getPatientDetail(patientId),
    enabled: Boolean(patientId),
  });
}

export function useConsultationsQuery() {
  return useQuery({
    queryKey: queryKeys.consultations.list(),
    queryFn: listConsultations,
  });
}

export function useConsultationDetailQuery(consultationId: string) {
  return useQuery({
    queryKey: queryKeys.consultations.detail(consultationId),
    queryFn: () => getConsultationDetail(consultationId),
    enabled: Boolean(consultationId),
  });
}

export function useReviewQuery(consultationId: string) {
  return useQuery({
    queryKey: queryKeys.review(consultationId),
    queryFn: () => getReview(consultationId),
    enabled: Boolean(consultationId),
  });
}

export function useCreatePatientMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPatient,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.patients.all });
    },
  });
}

export function useCreateConsultationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createConsultation,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.consultations.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.currentUser() });
    },
  });
}

export function useStartSessionMutation(consultationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => startSession(consultationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.consultations.all });
    },
  });
}

export function useEndSessionMutation(consultationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => endSession(consultationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.consultations.all });
    },
  });
}

export function useUpdateReviewMutation(consultationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateReviewRequest) => updateReview(consultationId, payload),
    onSuccess: (review) => {
      queryClient.setQueryData(queryKeys.review(consultationId), review);
      void queryClient.invalidateQueries({ queryKey: queryKeys.consultations.detail(consultationId) });
    },
  });
}

export function useFinalizeConsultationMutation(consultationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => finalizeConsultation(consultationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.consultations.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.consultations.detail(consultationId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.review(consultationId) });
    },
  });
}

export function useExportConsultationMutation(consultationId: string) {
  return useMutation({
    mutationFn: () => exportConsultation(consultationId),
  });
}

export function useTranscriptionTokenMutation(consultationId: string) {
  return useMutation({
    mutationFn: () => getTranscriptionToken(consultationId),
  });
}
