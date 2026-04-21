export const CURRENT_EVENT_VERSION = '2';

export type ConsultationStatus =
  | 'started'
  | 'recording'
  | 'paused'
  | 'in_processing'
  | 'processing_failed'
  | 'draft_generated'
  | 'under_physician_review'
  | 'finalized';

export type PlanType = 'free_trial' | 'plus' | 'pro';

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
}

export interface UserProfileView {
  user: {
    doctor_id: string;
    name: string;
    email: string;
    plan_type: PlanType;
    clinic_id: string;
    clinic_name: string;
  };
  entitlements: {
    can_create_consultation: boolean;
    consultations_remaining: number;
    consultations_used_this_month: number;
    max_duration_minutes: number;
    export_enabled: boolean;
    trial_expired: boolean;
    trial_days_remaining: number;
  };
  feature_flags?: {
    export_enabled: boolean;
    insights_enabled: boolean;
    audio_playback_enabled: boolean;
  };
}

export interface PatientView {
  patient_id: string;
  name: string;
  cpf: string;
  date_of_birth: string | null;
  clinic_id: string;
  created_at: string;
}

export interface PatientListView {
  patients: PatientView[];
}

export interface PatientHistoryItemView {
  consultation_id: string;
  status: ConsultationStatus;
  scheduled_date: string;
  finalized_at: string | null;
  preview: {
    summary?: string;
  } | null;
}

export interface PatientDetailView {
  patient: PatientView;
  history: PatientHistoryItemView[];
}

export interface ConsultationView {
  consultation_id: string;
  patient: {
      patient_id: string;
      name: string;
      cpf?: string;
  };
  doctor_id: string;
  clinic_id: string;
  specialty: string;
  status: ConsultationStatus;
  scheduled_date: string;
  created_at: string;
  updated_at: string;
}

export interface ConsultationDetailView extends ConsultationView {
  session: {
    session_id: string | null;
    started_at: string | null;
    ended_at: string | null;
    duration_seconds: number | null;
  };
  processing: {
    started_at: string | null;
    completed_at: string | null;
    error_details: Record<string, unknown> | null;
  };
  has_draft: boolean;
  finalized_at: string | null;
  finalized_by: string | null;
  actions: {
    can_start_recording: boolean;
    can_stop_recording: boolean;
    can_retry_processing: boolean;
    can_open_review: boolean;
    can_edit_review: boolean;
    can_finalize: boolean;
    can_export: boolean;
  };
  warnings: Array<{
    type: string;
    message: string;
  }>;
}

export interface ConsultationListView {
  consultations: ConsultationView[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface SessionStartView {
  session_id: string;
  websocket_url: string;
  connection_token: string;
  max_duration_minutes: number;
  started_at: string;
}

export interface SessionEndView {
  session_id: string;
  ended_at: string;
  duration_seconds: number;
  status: ConsultationStatus;
}

export interface UiConfigView {
  version: string;
  locale: 'pt-BR';
  labels: {
    consultation_list_title: string;
    new_consultation_button: string;
    start_recording_button: string;
    stop_recording_button: string;
    review_title: string;
    finalize_button: string;
    export_button: string;
    ai_disclaimer: string;
    completeness_warning: string;
    live_session_header: string;
  };
  review_screen: {
    section_order: Array<'transcript' | 'medical_history' | 'summary' | 'insights'>;
    sections: Record<
      'transcript' | 'medical_history' | 'summary' | 'insights',
      {
        title: string;
        editable: boolean;
        visible: boolean;
      }
    >;
  };
  insight_categories: Record<
    'documentation_gap' | 'consistency_issue' | 'clinical_attention',
    {
      label: string;
      icon: 'info' | 'warning' | 'alert';
      severity: 'low' | 'medium' | 'high';
    }
  >;
  status_labels: Record<ConsultationStatus, string>;
  feature_flags: {
    export_enabled: boolean;
    insights_enabled: boolean;
    audio_playback_enabled: boolean;
  };
}

export interface TranscriptSegment {
  speaker: 'doctor' | 'patient' | 'unknown';
  text: string;
  start_time?: number;
  end_time?: number;
}

export interface ReviewInsight {
  insight_id: string;
  category: 'documentation_gap' | 'consistency_issue' | 'clinical_attention';
  description: string;
  evidence: Array<{
    text: string;
    start_time?: number;
    end_time?: number;
    context?: string;
  }>;
  status: 'pending' | 'accepted' | 'dismissed' | 'edited';
  physician_note: string | null;
}

export interface ReviewView {
  consultation_id: string;
  status: 'under_physician_review' | 'finalized';
  transcript?: {
    segments: TranscriptSegment[];
  };
  medical_history: {
    content: Record<string, unknown>;
    edited_by_physician: boolean;
    completeness_warning: boolean;
  };
  summary: {
    content: string | Record<string, unknown>;
    edited_by_physician: boolean;
    completeness_warning: boolean;
  };
  insights: ReviewInsight[];
  ui_config?: {
    labels?: Record<string, string>;
    section_order?: string[];
    warnings?: string[];
  };
}

export interface FinalizeView {
  consultation_id: string;
  status: 'finalized';
  finalized_at: string;
  finalized_by: string;
}

export interface ExportView {
  consultation_id: string;
  export_url: string;
  expires_at: string;
  format: 'pdf';
}

export interface UpdateReviewRequest {
  medical_history?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  insights?: Array<{
    insight_id: string;
    action: 'accept' | 'dismiss' | 'edit';
    physician_note?: string;
  }>;
}

export interface TranscriptionTokenView {
  token: string;
  websocket_url: string;
  model_id: string;
  language_code: string;
  expires_at: string;
  expires_in_seconds: number;
}

export interface CommittedSegment {
  speaker: string;
  text: string;
  start_time: number | null;
  end_time: number | null;
  confidence: number | null;
  is_final: boolean;
}

export type SessionClientMessage =
  | {
      action: 'session.init';
      data: {
        consultation_id: string;
        session_id: string;
        event_version: string;
      };
    }
  | {
      action: 'transcript.commit';
      data: {
        consultation_id: string;
        segments: CommittedSegment[];
        timestamp: string;
        event_version: string;
      };
    }
  | {
      action: 'session.pause';
      data: {
        consultation_id: string;
        timestamp: string;
        event_version: string;
      };
    }
  | {
      action: 'session.resume';
      data: {
        consultation_id: string;
        timestamp: string;
        event_version: string;
      };
    }
  | {
      action: 'session.stop';
      data: {
        consultation_id: string;
        event_version: string;
      };
    }
  | {
      action: 'client.ping';
      data: {
        timestamp: string;
        event_version: string;
      };
    };

export interface SessionServerEvent {
  event:
    | 'transcript.partial'
    | 'transcript.final'
    | 'session.status'
    | 'session.warning'
    | 'session.ended'
    | 'insight.provisional'
    | 'autofill.candidate'
    | 'server.pong';
  data: Record<string, unknown>;
  event_version?: string;
}
