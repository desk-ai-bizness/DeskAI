# Contract Inventory

## Purpose

This document inventories all API contracts, WebSocket message contracts, UI configuration schemas, and feature flag schemas for the MVP. It defines ownership, location, and the expected shape of each contract.

---

## 1. Contract Locations

All contract schemas live in the `contracts/` directory at the repository root.

```
contracts/
├── http/                          # HTTP API contracts (OpenAPI 3.1)
├── websocket/                     # WebSocket message contracts (JSON Schema)
├── ui-config/                     # UI configuration schemas (JSON Schema)
└── feature-flags/                 # Feature flag definitions (JSON Schema)
```

### Ownership Rules

| Contract Type | Schema Owner | Consumers |
|---------------|-------------|-----------|
| HTTP API | Backend (BFF defines response shape) | Frontend app |
| WebSocket Messages | Backend (session management) | Frontend app |
| UI Config | Backend (BFF assembles config) | Frontend app |
| Feature Flags | Backend (BFF evaluates flags) | Frontend app, BFF, Backend |

---

## 2. HTTP API Contracts

### Auth Endpoints

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `POST` | `/v1/auth/session` | `{ email, password }` | `{ access_token, refresh_token, expires_in }` | `handlers/http/auth_handler.py` |
| `DELETE` | `/v1/auth/session` | None | `204 No Content` | `handlers/http/auth_handler.py` |

### User Endpoints

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `GET` | `/v1/me` | None | `UserProfileView` | `handlers/http/me_handler.py` |

#### UserProfileView

```json
{
  "user": {
    "doctor_id": "uuid",
    "name": "string",
    "email": "string",
    "plan_type": "free_trial | plus | pro",
    "clinic_id": "uuid",
    "clinic_name": "string"
  },
  "entitlements": {
    "can_create_consultation": true,
    "consultations_remaining": 42,
    "consultations_used_this_month": 8,
    "max_duration_minutes": 60,
    "export_enabled": true,
    "trial_expired": false,
    "trial_days_remaining": 6
  }
}
```

### Patient Endpoints

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `POST` | `/v1/patients` | `CreatePatientRequest` | `PatientView` | `handlers/http/patient_handler.py` |
| `GET` | `/v1/patients` | Query: `?search=` | `PatientListView` | `handlers/http/patient_handler.py` |
| `GET` | `/v1/patients/{patient_id}` | None | `PatientDetailView` | `handlers/http/patient_handler.py` |

#### CreatePatientRequest

```json
{
  "name": "string",
  "cpf": "string (digits or punctuated CPF)",
  "date_of_birth": "YYYY-MM-DD | null (optional)"
}
```

#### PatientView

```json
{
  "patient_id": "uuid",
  "name": "string",
  "cpf": "masked CPF string",
  "date_of_birth": "YYYY-MM-DD | null",
  "clinic_id": "uuid",
  "created_at": "ISO 8601"
}
```

#### PatientDetailView

```json
{
  "patient": "PatientView",
  "history": [
    {
      "consultation_id": "uuid",
      "status": "started | recording | in_processing | processing_failed | draft_generated | under_physician_review | finalized",
      "scheduled_date": "YYYY-MM-DD",
      "finalized_at": "ISO 8601 | null",
      "preview": {
        "summary": "string"
      } | null
    }
  ]
}
```

Patient history is filtered to consultations owned by the current doctor. CPF is stored normalized as digits and returned masked for display.

### Consultation Endpoints

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `POST` | `/v1/consultations` | `CreateConsultationRequest` | `ConsultationView` | `handlers/http/consultation_handler.py` |
| `GET` | `/v1/consultations` | Query: `?status=&from=&to=` | `ConsultationListView` | `handlers/http/consultation_handler.py` |
| `GET` | `/v1/consultations/{id}` | None | `ConsultationDetailView` | `handlers/http/consultation_handler.py` |

#### CreateConsultationRequest

```json
{
  "patient_id": "uuid",
  "specialty": "general_practice",
  "scheduled_date": "YYYY-MM-DD",
  "notes": "string (optional)"
}
```

#### ConsultationView

```json
{
  "consultation_id": "uuid",
  "patient": {
    "patient_id": "uuid",
    "name": "string"
  },
  "doctor_id": "uuid",
  "clinic_id": "uuid",
  "specialty": "general_practice",
  "status": "started | recording | in_processing | processing_failed | draft_generated | under_physician_review | finalized",
  "scheduled_date": "YYYY-MM-DD",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

#### ConsultationListView

```json
{
  "consultations": [ "ConsultationView[]" ],
  "total_count": 25,
  "page": 1,
  "page_size": 20
}
```

#### ConsultationDetailView

Extends `ConsultationView` with:

```json
{
  "...ConsultationView fields",
  "session": {
    "session_id": "uuid | null",
    "started_at": "ISO 8601 | null",
    "ended_at": "ISO 8601 | null",
    "duration_seconds": 1234
  },
  "processing": {
    "started_at": "ISO 8601 | null",
    "completed_at": "ISO 8601 | null",
    "error_details": "object | null"
  },
  "has_draft": true,
  "finalized_at": "ISO 8601 | null",
  "finalized_by": "uuid | null"
}
```

### Session Endpoints

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `POST` | `/v1/consultations/{id}/session/start` | None | `SessionStartView` | `handlers/http/session_handler.py` |
| `POST` | `/v1/consultations/{id}/session/end` | None | `SessionEndView` | `handlers/http/session_handler.py` |
| `POST` | `/v1/consultations/{id}/transcription-token` | None | `TranscriptionTokenView` | `handlers/http/transcription_token_handler.py` |

#### SessionStartView

```json
{
  "session_id": "uuid",
  "websocket_url": "wss://...",
  "connection_token": "string",
  "max_duration_minutes": 60,
  "started_at": "ISO 8601"
}
```

#### SessionEndView

```json
{
  "session_id": "uuid",
  "ended_at": "ISO 8601",
  "duration_seconds": 1234,
  "status": "in_processing"
}
```

#### TranscriptionTokenView

```json
{
  "token": "string (ElevenLabs single-use token)",
  "websocket_url": "wss://api.elevenlabs.io/v1/speech-to-text/realtime",
  "model_id": "scribe_v2_realtime",
  "language_code": "pt",
  "expires_at": "ISO 8601",
  "expires_in_seconds": 900
}
```

The token is a single-use ElevenLabs token (15-min TTL) generated server-side. The long-lived ElevenLabs API key never reaches the browser. See ADR-017.

### Review Endpoints

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `GET` | `/v1/consultations/{id}/review` | None | `ReviewView` | `handlers/http/review_handler.py` |
| `PUT` | `/v1/consultations/{id}/review` | `UpdateReviewRequest` | `ReviewView` | `handlers/http/review_handler.py` |

#### ReviewView

```json
{
  "consultation_id": "uuid",
  "status": "under_physician_review",
  "transcript": {
    "segments": [
      {
        "speaker": "doctor | patient",
        "text": "string",
        "start_time": 0.0,
        "end_time": 5.2
      }
    ]
  },
  "medical_history": {
    "content": "structured object",
    "edited_by_physician": false,
    "completeness_warning": false
  },
  "summary": {
    "content": "string",
    "edited_by_physician": false,
    "completeness_warning": false
  },
  "insights": [
    {
      "insight_id": "uuid",
      "category": "documentation_gap | consistency_issue | clinical_attention",
      "description": "string (pt-BR)",
      "evidence": [
        {
          "text": "string",
          "start_time": 0.0,
          "end_time": 5.2
        }
      ],
      "status": "pending | accepted | dismissed | edited",
      "physician_note": "string | null"
    }
  ],
  "ui_config": {
    "labels": {},
    "section_order": [],
    "warnings": []
  }
}
```

#### UpdateReviewRequest

```json
{
  "medical_history": "structured object (optional)",
  "summary": "string (optional)",
  "insights": [
    {
      "insight_id": "uuid",
      "action": "accept | dismiss | edit",
      "physician_note": "string (optional)"
    }
  ]
}
```

### Finalize Endpoint

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `POST` | `/v1/consultations/{id}/finalize` | None | `FinalizeView` | `handlers/http/finalize_handler.py` |

#### FinalizeView

```json
{
  "consultation_id": "uuid",
  "status": "finalized",
  "finalized_at": "ISO 8601",
  "finalized_by": "uuid"
}
```

### Export Endpoint

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `POST` | `/v1/consultations/{id}/export` | None | `ExportView` | `handlers/http/export_handler.py` |

#### ExportView

```json
{
  "consultation_id": "uuid",
  "export_url": "string (presigned S3 URL)",
  "expires_at": "ISO 8601",
  "format": "pdf"
}
```

### UI Config Endpoint

| Method | Path | Request Body | Response Body | Owner |
|--------|------|-------------|---------------|-------|
| `GET` | `/v1/ui-config` | None | `UIConfigView` | `handlers/http/ui_config_handler.py` |

See section 4 for the `UIConfigView` schema.

### Error Response Contract

All error responses follow a consistent shape:

```json
{
  "error": {
    "code": "string",
    "message": "string (pt-BR, user-facing)",
    "details": "object (optional, for debugging)"
  }
}
```

Standard error codes:

| Code | HTTP Status | Description |
|------|------------|-------------|
| `validation_error` | 400 | Request body or parameters are invalid |
| `unauthorized` | 401 | Missing or invalid authentication |
| `forbidden` | 403 | Authenticated but not authorized |
| `not_found` | 404 | Resource does not exist |
| `conflict` | 409 | State conflict (e.g., invalid status transition) |
| `plan_limit_exceeded` | 403 | Monthly consultation limit reached |
| `trial_expired` | 403 | Free trial has expired |
| `session_duration_exceeded` | 403 | Session exceeded plan duration limit |
| `feature_not_available` | 403 | Feature not available on current plan |
| `service_unavailable` | 503 | Upstream service temporarily unavailable (retry with backoff) |
| `export_expired` | 410 | Export download link has expired (regenerate) |
| `internal_error` | 500 | Unexpected server error |

For the complete failure behavior, retry budgets, and user-facing error messages per operation, see `docs/requirements/04-failure-behavior-matrix.md`.

---

## 3. WebSocket Message Contracts

### Connection

| Route | Direction | Purpose |
|-------|-----------|---------|
| `$connect` | Client → Server | Establish WebSocket connection (auth token in query string) |
| `$disconnect` | Server-detected | Client disconnected |

### Client-to-Server Messages

#### session.init

Sent by client to initialize the audio session after WebSocket connection.

```json
{
  "action": "session.init",
  "data": {
    "consultation_id": "uuid",
    "session_id": "uuid"
  }
}
```

#### transcript.commit

Sent by client to persist committed transcript segments received from the ElevenLabs Realtime provider. Added in Task 023 (replaces `audio.chunk`).

```json
{
  "action": "transcript.commit",
  "data": {
    "consultation_id": "uuid",
    "segments": [
      {
        "speaker": "doctor | patient | unknown",
        "text": "string",
        "start_time": 0.0,
        "end_time": 5.2,
        "confidence": 0.95,
        "is_final": true
      }
    ],
    "timestamp": "ISO 8601",
    "event_version": "2"
  }
}
```

#### session.pause

Sent by client to pause the recording session. Frontend stops audio capture. Backend transitions session to PAUSED state.

```json
{
  "action": "session.pause",
  "data": {
    "consultation_id": "uuid",
    "timestamp": "ISO 8601",
    "event_version": "2"
  }
}
```

#### session.resume

Sent by client to resume a paused recording session. Frontend restarts audio capture. Backend transitions session back to RECORDING.

```json
{
  "action": "session.resume",
  "data": {
    "consultation_id": "uuid",
    "timestamp": "ISO 8601",
    "event_version": "2"
  }
}
```

#### session.stop

Sent by client to end the audio session.

```json
{
  "action": "session.stop",
  "data": {
    "consultation_id": "uuid"
  }
}
```

**Note:** `session.stop` triggers the same backend logic as `POST /v1/consultations/{id}/session/end`. Both end the recording session and transition the consultation to `in_processing`. See `docs/requirements/02-consultation-lifecycle.md` for details.

#### client.ping

Sent by client for keep-alive.

```json
{
  "action": "client.ping",
  "data": {
    "timestamp": "ISO 8601"
  }
}
```

### Server-to-Client Messages

#### transcript.partial

Partial transcript update during recording.

```json
{
  "event": "transcript.partial",
  "data": {
    "text": "string",
    "speaker": "doctor | patient | unknown",
    "is_final": false,
    "start_time": 0.0,
    "end_time": 5.2,
    "confidence": 0.95
  }
}
```

#### transcript.final

Final segment from transcription provider.

```json
{
  "event": "transcript.final",
  "data": {
    "text": "string",
    "speaker": "doctor | patient | unknown",
    "is_final": true,
    "start_time": 0.0,
    "end_time": 5.2,
    "confidence": 0.98
  }
}
```

#### session.status

Session state changes.

```json
{
  "event": "session.status",
  "data": {
    "status": "connected | recording | paused | processing | error",
    "message": "string (pt-BR)",
    "event_version": "2"
  }
}
```

#### session.warning

Duration warning before auto-end.

```json
{
  "event": "session.warning",
  "data": {
    "type": "duration_limit_approaching",
    "remaining_minutes": 5,
    "message": "string (pt-BR)"
  }
}
```

#### session.ended

Session auto-ended (duration limit or grace period expired).

```json
{
  "event": "session.ended",
  "data": {
    "reason": "duration_limit | grace_period_expired | manual",
    "message": "string (pt-BR)"
  }
}
```

#### insight.provisional (schema only — emitter in Task 024)

Provisional insight generated during or shortly after a consultation. Marked as draft and must not be presented as authoritative clinical content.

```json
{
  "event": "insight.provisional",
  "data": {
    "insight_id": "uuid",
    "category": "documentation_gap | consistency_issue | clinical_attention",
    "text": "string (pt-BR)",
    "severity": "low | medium | high",
    "evidence_excerpt": "string",
    "is_draft": true,
    "event_version": "2"
  }
}
```

#### autofill.candidate (schema only — emitter in Task 024)

Candidate value for a medical history field, suggested based on transcript evidence. Must be reviewed by the physician before acceptance.

```json
{
  "event": "autofill.candidate",
  "data": {
    "field_key": "string",
    "candidate_value": "string",
    "evidence_excerpt": "string",
    "confidence": 0.85,
    "event_version": "2"
  }
}
```

#### server.pong

Response to client ping.

```json
{
  "event": "server.pong",
  "data": {
    "timestamp": "ISO 8601"
  }
}
```

---

## 4. UI Configuration Contract

### UIConfigView

Returned by `GET /v1/ui-config` and embedded in review responses.

```json
{
  "version": "1.0",
  "locale": "pt-BR",
  "labels": {
    "consultation_list_title": "Minhas Consultas",
    "new_consultation_button": "Nova Consulta",
    "start_recording_button": "Iniciar Gravacao",
    "stop_recording_button": "Encerrar Gravacao",
    "review_title": "Revisao da Consulta",
    "finalize_button": "Finalizar Consulta",
    "export_button": "Exportar PDF",
    "ai_disclaimer": "Conteudo gerado por IA. Sujeito a revisao medica.",
    "completeness_warning": "Audio insuficiente para documentacao completa. Revise com atencao."
  },
  "review_screen": {
    "section_order": [
      "transcript",
      "medical_history",
      "summary",
      "insights"
    ],
    "sections": {
      "transcript": {
        "title": "Transcricao",
        "editable": false,
        "visible": true
      },
      "medical_history": {
        "title": "Historia Clinica",
        "editable": true,
        "visible": true
      },
      "summary": {
        "title": "Resumo da Consulta",
        "editable": true,
        "visible": true
      },
      "insights": {
        "title": "Observacoes para Revisao",
        "editable": true,
        "visible": true
      }
    }
  },
  "insight_categories": {
    "documentation_gap": {
      "label": "Lacuna de Documentacao",
      "icon": "info",
      "severity": "low"
    },
    "consistency_issue": {
      "label": "Inconsistencia",
      "icon": "warning",
      "severity": "medium"
    },
    "clinical_attention": {
      "label": "Atencao Clinica",
      "icon": "alert",
      "severity": "high"
    }
  },
  "status_labels": {
    "started": "Aguardando",
    "recording": "Gravando",
    "in_processing": "Processando",
    "processing_failed": "Falha no Processamento",
    "draft_generated": "Rascunho Pronto",
    "under_physician_review": "Em Revisao",
    "finalized": "Finalizada"
  },
  "feature_flags": {
    "export_enabled": true,
    "insights_enabled": true,
    "audio_playback_enabled": false
  }
}
```

### Config Storage Strategy

| Config Type | Storage | Reason |
|-------------|---------|--------|
| Labels and static text | DynamoDB (small, fast lookup) | Frequently accessed, small payload |
| Section ordering and visibility | DynamoDB | Small metadata, per-scope |
| Insight category definitions | DynamoDB | Small, rarely changes |
| Large template configs | S3 (versioned JSON) | If config grows beyond DynamoDB item limits |
| Feature flags | DynamoDB | Fast evaluation, per-user context |

---

## 5. Feature Flag Contract

Feature flags are evaluated by the BFF and included in API responses.

### Flag Definitions

| Flag | Type | Scope | Default | Description |
|------|------|-------|---------|-------------|
| `consultation.create.enabled` | boolean | global | `true` | Master switch for consultation creation |
| `consultation.monthly_limit` | integer | plan | Plan-dependent | Max consultations per month |
| `consultation.max_duration_minutes` | integer | plan | Plan-dependent | Max session duration |
| `audio.retention_days` | integer | plan | Plan-dependent | Audio auto-deletion period |
| `export.pdf.enabled` | boolean | global | `true` | PDF export availability |
| `insights.enabled` | boolean | global | `true` | Insight generation |
| `audio.playback.enabled` | boolean | global | `false` | Audio playback in review (future) |
| `trial.duration_days` | integer | global | `14` | Free trial length |

### Flag Evaluation Flow

```
1. Handler receives request with authenticated user context
2. Handler calls BFF layer
3. BFF reads user's plan_type from auth context
4. BFF loads flag values from config repository
5. BFF evaluates flags for the user's plan_type
6. BFF includes evaluated flags in the response
7. Frontend renders based on flag values
```

### Flag Storage Schema (DynamoDB)

```json
{
  "PK": "CONFIG#feature_flags",
  "SK": "VERSION#current",
  "flags": {
    "consultation.create.enabled": {
      "type": "boolean",
      "default": true,
      "overrides": {}
    },
    "consultation.monthly_limit": {
      "type": "integer",
      "default": 10,
      "overrides": {
        "plus": 50,
        "pro": -1
      }
    }
  },
  "updated_at": "ISO 8601",
  "updated_by": "admin"
}
```

`-1` means unlimited.

---

## 6. Contract Versioning Rules

- API paths include a version prefix: `/v1/...`.
- Breaking changes require a new version prefix (`/v2/...`). Non-breaking additions (new optional fields) do not.
- UI config includes a `version` field. The frontend checks it for compatibility.
- WebSocket messages include `action` (client) or `event` (server) as discriminators.
- All WebSocket event payloads include an `event_version` string field (current: `"2"`, introduced in Task 023). Frontend checks version for compatibility.
- Contract changes must update the corresponding YAML schema in `contracts/` and both backend and frontend code.
