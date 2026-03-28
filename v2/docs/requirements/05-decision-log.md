# Decision Log

## Purpose

This document records decisions made during requirements refinement and flags items that remain open for product or technical approval.

Each decision includes the context, the chosen option, the reasoning, and the reversibility assessment.

---

## Resolved Decisions

### DEC-001: Transcription Provider Selection

| Field | Value |
|-------|-------|
| **Context** | The MVP needs a pt-BR transcription provider for real-time medical consultation audio. Candidates listed in business rules: Google Cloud Speech-to-Text, Azure AI Speech, Deepgram. |
| **Decision** | **Deepgram** (Nova-2 Medical model) is the recommended first provider. |
| **Reasoning** | (1) Nova-2 Medical is purpose-built for medical vocabulary. (2) Deepgram offers a real-time streaming WebSocket API that maps directly to the MVP architecture. (3) pt-BR is a supported language. (4) Deepgram's pricing is competitive for low-volume MVP usage. (5) The provider adapter pattern means switching is low-cost if Deepgram underperforms. |
| **Alternatives Considered** | Google Cloud Speech-to-Text (strong pt-BR, but no medical-specific model, higher complexity for streaming). Azure AI Speech (good accuracy, but heavier SDK, less direct WebSocket integration). |
| **Reversibility** | High. The internal provider interface (`start_realtime_session`, `send_audio_chunk`, etc.) abstracts the provider. Switching requires only a new adapter implementation. |
| **Resolves** | Open Issue OI-001 |
| **Impact on Tasks** | Task 009 can proceed with Deepgram adapter as the first implementation. |

### DEC-002: MVP Plan Entitlement Defaults

| Field | Value |
|-------|-------|
| **Context** | Plan differences for `free_trial`, `plus`, and `pro` were undefined (OI-002). Backend authorization and feature flags need concrete values. |
| **Decision** | All three plans share the same core features. Differentiation is by usage limits only: consultation count, session duration, and audio retention. See `03-plan-entitlements.md` for the full matrix. |
| **Reasoning** | (1) MVP goal is reliability and reviewability, not feature segmentation. (2) Minimal differentiation reduces backend complexity. (3) Usage limits can be adjusted via configuration without code changes. (4) Billing integration is post-MVP, so complex feature gating adds no revenue value yet. |
| **Reversibility** | High. Limits are feature-flag-driven and can be changed at any time. |
| **Resolves** | Open Issue OI-002 |
| **Impact on Tasks** | Task 005 implements plan enforcement. Task 007 exposes entitlements via BFF. |

### DEC-003: Audio Retention Defaults

| Field | Value |
|-------|-------|
| **Context** | Clinic audio retention defaults and deletion timing were not defined (OI-003). S3 lifecycle rules need concrete values. |
| **Decision** | Audio retention is plan-based: `free_trial` = 7 days, `plus` = 30 days, `pro` = 90 days. After the retention period, audio is automatically deleted via S3 lifecycle rules. Finalized notes and AI artifacts are retained independently of audio deletion. |
| **Reasoning** | (1) Plan-based retention aligns with plan value differentiation. (2) Decoupling audio from finalized notes respects the business rule that clinics may retain notes even after audio deletion. (3) S3 lifecycle rules are low-maintenance. (4) Shorter defaults for lower plans reduce storage costs. |
| **Reversibility** | High. S3 lifecycle rules can be updated. Retention periods are configuration values. |
| **Resolves** | Open Issue OI-003 |
| **Impact on Tasks** | Task 004 sets up S3 lifecycle rules. Task 014 implements retention automation. |

### DEC-004: Export Scope

| Field | Value |
|-------|-------|
| **Context** | Export output scope beyond the finalized note was not specified (OI-004). |
| **Decision** | MVP export generates a single PDF containing: (1) consultation metadata (date, physician, patient, specialty), (2) finalized medical history, (3) finalized summary, (4) accepted insights with evidence excerpts. The transcript is NOT included in the export by default. |
| **Reasoning** | (1) The finalized note is the primary output physicians need. (2) Including the raw transcript would make the export very long and less useful for clinical records. (3) Transcript access remains available in-app. (4) Future: optional transcript inclusion can be a feature flag. |
| **Reversibility** | High. Adding transcript to export is additive. Feature flag can control inclusion. |
| **Resolves** | Open Issue OI-004 |
| **Impact on Tasks** | Task 011 implements export generation. |

### DEC-005: Consultation State Machine Extensions

| Field | Value |
|-------|-------|
| **Context** | Business rules define five states. Implementation needs finer-grained states for session management and failure handling. |
| **Decision** | Two implementation states added: `recording` (audio session active) and `processing_failed` (pipeline failed). These are refinements of the business states `started` and `in processing`. See `02-consultation-lifecycle.md`. |
| **Reasoning** | (1) `recording` is needed to manage WebSocket lifecycle, session reconnection, and UI feedback. (2) `processing_failed` is needed to distinguish "still processing" from "failed and retryable." (3) The original five business states remain the canonical business-facing vocabulary. |
| **Reversibility** | High. These states can be collapsed or renamed without business impact. |
| **Impact on Tasks** | Task 006 implements the state machine. Task 012 renders state-appropriate UI. |

### DEC-006: WebSocket Disconnection Grace Period

| Field | Value |
|-------|-------|
| **Context** | No defined behavior for mid-recording WebSocket disconnections. |
| **Decision** | 5-minute configurable grace period. If the physician reconnects within the period, the session resumes. If not, the session auto-ends and processing begins with available audio. |
| **Reasoning** | (1) Brief network interruptions are common in clinic settings. (2) Auto-ending immediately would lose potentially valuable audio. (3) A 5-minute window balances recovery with timely processing. (4) The value is configurable for adjustment. |
| **Reversibility** | High. Configuration change only. |
| **Impact on Tasks** | Task 008 implements session management with grace period. |

### DEC-007: LLM Provider for AI Pipeline

| Field | Value |
|-------|-------|
| **Context** | The technical specs reference "OpenAI Processing Layer" in section 13, but the CLAUDE.md references "Claude API (Anthropic)" as the LLM provider. |
| **Decision** | Use **Claude API (Anthropic)** as the LLM provider for the AI pipeline. The technical specs section 13 title ("OpenAI Processing Layer") is a legacy label and should be read as "AI Processing Layer." |
| **Reasoning** | (1) CLAUDE.md is the latest project guidance and explicitly names Claude API. (2) The provider adapter pattern applies here too — the LLM is abstracted behind an internal interface. (3) Claude's structured output capabilities align well with the schema-strict generation requirements. |
| **Reversibility** | High. LLM provider is behind an adapter interface. |
| **Impact on Tasks** | Task 010 uses Claude API. Technical specs section 13 title should be updated to "AI Processing Layer." |

---

## Open Decisions (Deferred)

### OPEN-001: Billing Integration Provider

| Field | Value |
|-------|-------|
| **Context** | Plan upgrades and downgrades are manual in the MVP. Billing is post-MVP. |
| **Status** | Deferred |
| **Options** | Stripe, Paddle, custom |
| **When to Decide** | Before implementing self-service plan management |
| **Impact if Delayed** | None for MVP. Plan assignment is manual. |

### OPEN-002: Multi-Physician Clinic Access Model

| Field | Value |
|-------|-------|
| **Context** | MVP is single-physician per consultation with no shared access. |
| **Status** | Deferred |
| **Options** | Delegate access, supervisor review, clinic-wide visibility |
| **When to Decide** | When multi-physician clinics become a significant user segment |
| **Impact if Delayed** | None for MVP. Ownership model is simple. |

### OPEN-003: Post-Consultation Upload Flow

| Field | Value |
|-------|-------|
| **Context** | Technical specs mention this as a future secondary flow. |
| **Status** | Deferred |
| **Options** | Direct S3 upload with presigned URL, chunked upload through BFF |
| **When to Decide** | After MVP launch, based on user feedback about connectivity issues |
| **Impact if Delayed** | None for MVP. Real-time streaming is the primary path. |

### OPEN-004: Specialty List and Validation

| Field | Value |
|-------|-------|
| **Context** | The MVP requires a `specialty` field per consultation but the allowed values are not defined. |
| **Status** | Open — needs product input |
| **Options** | (a) Free-text field, (b) Backend-managed enum list, (c) CBO-based specialty codes |
| **Recommended** | Option (b): Backend-managed enum list, initially containing `general_practice` only (matching MVP scope of "general practice/generalist consultations"). Expandable via configuration. |
| **When to Decide** | Before Task 006 (domain model) |
| **Impact if Delayed** | Domain model cannot validate specialty; may need migration later |

### OPEN-005: Patient Creation and Management

| Field | Value |
|-------|-------|
| **Context** | Consultations require a `patient_id`, but no patient CRUD endpoints are defined in the API contract. |
| **Status** | Open — needs product input |
| **Options** | (a) Minimal patient creation endpoint in MVP, (b) Inline patient creation during consultation creation |
| **Recommended** | Option (a): Add minimal `POST /v1/patients` and `GET /v1/patients` endpoints. Keep fields minimal: `name`, `date_of_birth`, `clinic_id`. |
| **When to Decide** | Before Task 006 (domain model) |
| **Impact if Delayed** | Cannot create consultations without hardcoding patient IDs |

---

## Decision Numbering Convention

- `DEC-NNN`: Resolved decisions with a clear outcome
- `OPEN-NNN`: Unresolved decisions that need product or technical input
