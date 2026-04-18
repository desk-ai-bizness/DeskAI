import { apiClient } from './client';
import type {
  AuthTokenResponse,
  ConsultationDetailView,
  ConsultationListView,
  ConsultationView,
  ExportView,
  FinalizeView,
  PatientListView,
  PatientView,
  ReviewView,
  SessionEndView,
  SessionStartView,
  UiConfigView,
  UpdateReviewRequest,
  UserProfileView,
} from '../types/contracts';

export async function login(email: string, password: string): Promise<AuthTokenResponse> {
  return apiClient.post<AuthTokenResponse>('/v1/auth/session', { email, password });
}

export async function logout(): Promise<void> {
  return apiClient.delete('/v1/auth/session');
}

export async function getCurrentUser(): Promise<UserProfileView> {
  return apiClient.get<UserProfileView>('/v1/me');
}

export async function getUiConfig(): Promise<UiConfigView> {
  return apiClient.get<UiConfigView>('/v1/ui-config');
}

export async function listPatients(search = ''): Promise<PatientListView> {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  return apiClient.get<PatientListView>(`/v1/patients${query}`);
}

export async function createPatient(input: {
  name: string;
  date_of_birth: string;
}): Promise<PatientView> {
  return apiClient.post<PatientView>('/v1/patients', input);
}

export async function listConsultations(): Promise<ConsultationListView> {
  return apiClient.get<ConsultationListView>('/v1/consultations');
}

export async function createConsultation(input: {
  patient_id: string;
  specialty: 'general_practice';
  scheduled_date: string;
  notes?: string;
}): Promise<ConsultationView> {
  return apiClient.post<ConsultationView>('/v1/consultations', input);
}

export async function getConsultationDetail(consultationId: string): Promise<ConsultationDetailView> {
  return apiClient.get<ConsultationDetailView>(`/v1/consultations/${consultationId}`);
}

export async function startSession(consultationId: string): Promise<SessionStartView> {
  return apiClient.post<SessionStartView>(`/v1/consultations/${consultationId}/session/start`);
}

export async function endSession(consultationId: string): Promise<SessionEndView> {
  return apiClient.post<SessionEndView>(`/v1/consultations/${consultationId}/session/end`);
}

export async function getReview(consultationId: string): Promise<ReviewView> {
  return apiClient.get<ReviewView>(`/v1/consultations/${consultationId}/review`);
}

export async function updateReview(
  consultationId: string,
  payload: UpdateReviewRequest,
): Promise<ReviewView> {
  return apiClient.put<ReviewView>(`/v1/consultations/${consultationId}/review`, payload);
}

export async function finalizeConsultation(consultationId: string): Promise<FinalizeView> {
  return apiClient.post<FinalizeView>(`/v1/consultations/${consultationId}/finalize`);
}

export async function exportConsultation(consultationId: string): Promise<ExportView> {
  return apiClient.post<ExportView>(`/v1/consultations/${consultationId}/export`);
}
