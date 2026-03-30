import type { ConsultationListItem } from '../types/contracts';
import { apiGet } from './client';

interface ConsultationListResponse {
  consultations: ConsultationListItem[];
}

export async function fetchConsultations(): Promise<ConsultationListItem[]> {
  const payload = await apiGet<ConsultationListResponse>('/v1/consultations');
  return payload.consultations;
}
