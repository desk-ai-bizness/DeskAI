export type ConsultationStatus =
  | 'started'
  | 'recording'
  | 'in_processing'
  | 'processing_failed'
  | 'draft_generated'
  | 'under_physician_review'
  | 'finalized';

export interface ConsultationListItem {
  consultation_id: string;
  patient_name: string;
  status: ConsultationStatus;
  scheduled_date: string;
}

export interface UiConfigView {
  version: string;
  locale: 'pt-BR';
  labels: Record<string, string>;
}
