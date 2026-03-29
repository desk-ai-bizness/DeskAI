# Consultation Lifecycle and State Machine

## Purpose

This document defines the complete consultation lifecycle, all allowed state transitions, guard conditions, side effects, and failure paths.

This is the canonical reference for backend state machine implementation (Task 006) and frontend status rendering (Task 012).

---

## 1. Consultation States

| State | Code Value | Description | Editable by Physician | AI Output Available |
|-------|-----------|-------------|----------------------|-------------------|
| Started | `started` | Consultation created, session not yet active or audio not yet received | No | No |
| Recording | `recording` | Real-time audio session is active and streaming | No | No |
| In Processing | `in_processing` | Audio session ended, backend is consolidating transcript and running AI pipeline | No | No |
| Processing Failed | `processing_failed` | Transcript consolidation or AI generation failed | No | No (partial may exist) |
| Draft Generated | `draft_generated` | AI pipeline completed, all artifacts stored, ready for review | No (not yet opened) | Yes |
| Under Physician Review | `under_physician_review` | Physician has opened the review screen and may be editing | Yes | Yes |
| Finalized | `finalized` | Physician has explicitly confirmed and locked the record | No (read-only) | Yes (final version) |

### Notes on New States

The business rules document (Section 16) lists five states: `started`, `in processing`, `draft generated`, `under physician review`, `finalized`.

This lifecycle adds two clarifying states for implementation precision:

- **`recording`**: Distinguishes "consultation created" from "audio session is actively streaming." This is needed for session management, WebSocket lifecycle, and UI feedback.
- **`processing_failed`**: Required by the failure behavior matrix. Without this state, the system cannot distinguish "still processing" from "processing has failed and needs retry or intervention."

**Decision:** These two additions are implementation refinements that do not change business semantics. The original five business states map directly:
- Business `started` → Implementation `started` + `recording`
- Business `in processing` → Implementation `in_processing` + `processing_failed`

---

## 2. State Transition Diagram

```
                 ┌──────────┐
                 │  started  │
                 └─────┬─────┘
                       │ session.start
                       ▼
                 ┌──────────┐
                 │ recording │
                 └─────┬─────┘
                       │ session.end
                       ▼
              ┌──────────────────┐
              │  in_processing   │
              └────┬─────────┬───┘
                   │         │
          success  │         │ failure
                   ▼         ▼
        ┌────────────────┐  ┌─────────────────────┐
        │ draft_generated │  │  processing_failed   │
        └───────┬────────┘  └──────────┬────────────┘
                │                      │ retry
                │ physician opens      │ (back to in_processing)
                │ review               │
                ▼                      │
  ┌──────────────────────────────┐     │
  │  under_physician_review      │◄────┘
  └──────────┬───────────────────┘     (only after successful retry
             │                          regenerates draft)
             │ physician confirms
             ▼
        ┌───────────┐
        │ finalized  │
        └───────────┘
```

---

## 3. Allowed Transitions

| From | To | Trigger | Guard Conditions | Side Effects |
|------|----|---------|-----------------|-------------|
| `started` | `recording` | `POST /v1/consultations/{id}/session/start` | Consultation exists, belongs to requesting physician, status is `started` | WebSocket session created, audio ingestion begins |
| `recording` | `in_processing` | `POST /v1/consultations/{id}/session/end` or WebSocket `session.stop` message | Active session exists for this consultation | WebSocket closed, transcript consolidation triggered, Step Functions workflow started |
| `in_processing` | `draft_generated` | Step Functions workflow completion | All required artifacts generated and stored | Artifacts stored in S3, metadata updated in DynamoDB, notification sent to BFF |
| `in_processing` | `processing_failed` | Step Functions workflow failure | Any required artifact failed to generate after retries | Error details stored, DynamoDB status updated, alert triggered |
| `processing_failed` | `in_processing` | Retry action (manual or automatic) | Previous failure recorded, retry budget not exhausted | Step Functions workflow re-triggered |
| `draft_generated` | `under_physician_review` | `GET /v1/consultations/{id}/review` (first access) | Status is `draft_generated`, requesting user is the owning physician | `review_opened_at` timestamp recorded, audit event created |
| `under_physician_review` | `under_physician_review` | `PUT /v1/consultations/{id}/review` | Status is `under_physician_review`, requesting user is the owning physician | Physician edits stored, audit event for each edit |
| `under_physician_review` | `finalized` | `POST /v1/consultations/{id}/finalize` | Status is `under_physician_review`, requesting user is the owning physician | Final version stored, record locked, `finalized_at` and `finalized_by` set, audit event created |

### Explicitly Forbidden Transitions

| From | To | Reason |
|------|----|--------|
| `started` | `in_processing` | Cannot skip recording; audio session must occur |
| `started` | `finalized` | Cannot finalize without processing and review |
| `recording` | `draft_generated` | Cannot skip processing |
| `in_processing` | `finalized` | Cannot finalize without physician review |
| `draft_generated` | `finalized` | Cannot finalize without entering review |
| `processing_failed` | `finalized` | Cannot finalize failed processing |
| `processing_failed` | `draft_generated` | Must go through `in_processing` again |
| `finalized` | any state | Finalized is a terminal state; no further transitions allowed |

### Session End Mechanisms

Two mechanisms can end an active recording session. Both trigger the same backend logic and produce the same state transition (`recording` → `in_processing`):

- **HTTP endpoint**: `POST /v1/consultations/{id}/session/end` — used by the frontend as a direct API call.
- **WebSocket message**: `session.stop` — sent by the frontend through the active WebSocket connection.

Both mechanisms invoke the same application use case (`EndSession`). The backend treats them as equivalent triggers. The frontend may use whichever is more convenient for the current context. If the WebSocket is disconnected, the HTTP endpoint serves as a reliable fallback.

---

## 4. Guard Conditions Detail

### Ownership Guards

- **Physician ownership**: Only the physician who created the consultation can start a session, review, edit, or finalize.
- **Clinic context**: All operations validate that the physician belongs to the clinic associated with the consultation.
- **Plan authorization**: Plan-based feature access is checked before allowing consultation creation, session start, and export.

### Idempotency Rules

- **Session start**: If a session is already active (`recording` state), a duplicate `session/start` call returns the existing session details (idempotent).
- **Session end**: If the session is already ended (state is `in_processing` or later), a duplicate `session/end` call returns success (idempotent).
- **Finalization**: If already finalized, a duplicate `finalize` call returns the finalized record (idempotent). It does not create a second audit event.

---

## 5. Minimum Required Fields

### Consultation Creation (POST /v1/consultations)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `patient_id` | string (UUID) | Yes | Must reference an existing patient in the clinic |
| `clinic_id` | string (UUID) | Yes | Derived from authenticated physician's context |
| `doctor_id` | string (UUID) | Yes | Derived from authenticated user |
| `specialty` | string (enum) | Yes | Single specialty per consultation |
| `scheduled_date` | ISO 8601 date | Yes | Date of the consultation |
| `notes` | string | No | Optional pre-consultation notes |

### System-Generated Fields

| Field | Type | Set When | Notes |
|-------|------|----------|-------|
| `consultation_id` | string (UUID) | On creation | Immutable |
| `status` | string (enum) | On creation, updated on transitions | See state machine |
| `created_at` | ISO 8601 datetime | On creation | Immutable |
| `updated_at` | ISO 8601 datetime | On every status change | |
| `session_started_at` | ISO 8601 datetime | On session start | |
| `session_ended_at` | ISO 8601 datetime | On session end | |
| `processing_started_at` | ISO 8601 datetime | On processing start | |
| `processing_completed_at` | ISO 8601 datetime | On draft generation | |
| `review_opened_at` | ISO 8601 datetime | On first review access | |
| `finalized_at` | ISO 8601 datetime | On finalization | |
| `finalized_by` | string (doctor_id) | On finalization | |
| `error_details` | object | On processing failure | Contains error type and message |

---

## 6. Data Mutability Rules

| Data Element | Mutable During Review | Mutable After Finalization | Notes |
|-------------|----------------------|---------------------------|-------|
| Consultation metadata (patient, clinic, specialty, date) | No | No | Immutable after creation |
| Raw audio | No | No (deletable per retention policy) | Never modified, only stored or deleted |
| Raw transcript | No | No | Provider output, immutable once stored |
| Normalized transcript | No | No | Immutable after consolidation |
| AI-generated medical history (draft) | Yes (physician edits) | No | Physician edits create a new version, original preserved |
| AI-generated summary (draft) | Yes (physician edits) | No | Same versioning as medical history |
| AI-generated insights (draft) | Yes (physician accept/dismiss/edit) | No | Physician actions recorded per insight |
| Physician-edited versions | Yes (until finalization) | No | Locked on finalization |
| Final confirmed record | No | No | Terminal, immutable, auditable |
| Audit events | No | No | Append-only, never modified or deleted |

---

## 7. Audit Events

Every state transition and physician action generates an audit event.

| Action | Audit Event Type | Required Fields |
|--------|-----------------|-----------------|
| Consultation created | `consultation.created` | `consultation_id`, `doctor_id`, `clinic_id`, `patient_id` |
| Session started | `session.started` | `consultation_id`, `doctor_id`, `session_id` |
| Session ended | `session.ended` | `consultation_id`, `doctor_id`, `session_id` |
| Processing started | `processing.started` | `consultation_id` |
| Processing completed | `processing.completed` | `consultation_id`, `artifact_types` |
| Processing failed | `processing.failed` | `consultation_id`, `error_type`, `error_message` |
| Review opened | `review.opened` | `consultation_id`, `doctor_id` |
| Physician edit | `review.edited` | `consultation_id`, `doctor_id`, `edited_field`, `edit_timestamp` |
| Insight action | `insight.actioned` | `consultation_id`, `doctor_id`, `insight_id`, `action` (accepted/dismissed/edited) |
| Finalization | `consultation.finalized` | `consultation_id`, `doctor_id`, `finalized_at` |
| Export generated | `export.generated` | `consultation_id`, `doctor_id`, `export_format` |

---

## 8. Edge Cases

### Consultation with insufficient audio

- If the audio session is very short (e.g., under 30 seconds) or contains no detectable speech, the transcription provider may return an empty or near-empty transcript.
- The AI pipeline receives minimal input and may produce incomplete artifacts.
- **Behavior**: Mark all artifacts as `incomplete`. Set consultation status to `draft_generated` with a `completeness_warning` flag. The physician sees the review screen with a warning: "Insufficient audio for complete documentation. Please review carefully."

### AI generation returns partial artifacts

- If some artifacts succeed but others fail (e.g., medical history generated but summary failed):
- **Behavior**: Status moves to `processing_failed`. Error details specify which artifacts failed. Retry reprocesses only the failed artifacts. If retry succeeds, status moves to `draft_generated`.

### Physician edits some outputs but not others

- The physician may edit the medical history but leave the summary and insights untouched.
- **Behavior**: On finalization, the system stores the physician-edited version for edited fields and the AI-generated version for unedited fields. All are included in the finalized record. The audit log records which fields were edited.

### Session disconnected unexpectedly

- WebSocket drops during recording.
- **Behavior**: Backend detects disconnect via `$disconnect` route. Audio received so far is preserved. Consultation remains in `recording` state for a grace period (configurable, default 5 minutes). If the physician reconnects within the grace period, the session resumes. If not, the session is auto-ended and processing begins with available audio.

### Duplicate finalization request

- Physician clicks "Finalize" twice.
- **Behavior**: Idempotent. Second request returns the existing finalized record. No duplicate audit event.
