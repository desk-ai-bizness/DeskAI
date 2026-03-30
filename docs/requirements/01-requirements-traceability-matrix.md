# Requirements Traceability Matrix

## Purpose

This document maps every major business rule from `mvp-business-rules.md` to the concrete system behaviors, API endpoints, data entities, and UI flows that must implement it.

Each row traces a business rule through the system layers so that every requirement has at least one verifiable implementation point.

---

## 1. Authentication and Access

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| AUTH-01 | Users must log in with email and password | Cognito User Pool configured for native email/password only | `POST /v1/auth/session` | Cognito user record | Login screen with email + password fields | 005 |
| AUTH-02 | No social login or SSO in MVP | Cognito social/federated providers disabled | N/A | N/A | No social login buttons rendered | 005 |
| AUTH-03 | Email verification required | Cognito sends verification email on signup | Cognito hosted UI or BFF signup flow | Cognito user attribute `email_verified` | Verification prompt after registration | 005 |
| AUTH-04 | Password reset supported | Cognito forgot-password flow | Cognito hosted UI or BFF forgot-password flow | Cognito user attribute | Forgot password link on login screen | 005 |

## 2. Plan and Access Control

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| PLAN-01 | Each doctor must belong to one plan type | Plan type stored on doctor record, enforced on every protected request | `GET /v1/me` returns plan info | DynamoDB `DOCTOR#<id>` record with `plan_type` attribute | Plan badge or indicator in dashboard | 005, 007 |
| PLAN-02 | Available plan types: `free_trial`, `plus`, `pro` | Backend validates plan type against allowed enum | All protected endpoints check plan | `plan_type` enum field on doctor entity | Plan-specific UI gating via BFF feature flags | 005, 007 |
| PLAN-03 | Access rules may vary by plan type | BFF and backend enforce plan-based feature gating | Feature flag evaluation in BFF responses | Plan entitlement matrix (see `03-plan-entitlements.md`) | Features disabled/hidden per plan | 007 |

## 3. Consultation Lifecycle

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| CONS-01 | Each consultation belongs to one physician, one patient, one clinic, one specialty | Validated on creation; immutable after creation | `POST /v1/consultations` | DynamoDB consultation record with `doctor_id`, `patient_id`, `clinic_id`, `specialty` | Consultation creation form with required fields | 006, 012 |
| CONS-02 | Consultation states: started, recording, in_processing, processing_failed, draft_generated, under_physician_review, finalized | State machine enforced in backend domain layer. See `docs/requirements/02-consultation-lifecycle.md` for full state machine. | State transitions via session and review endpoints | `status` field on consultation record + audit events | Status indicator on consultation detail screen | 006 |
| CONS-03 | Cannot finalize before physician review | Backend rejects finalization if status is not `under_physician_review` | `POST /v1/consultations/{id}/finalize` returns 409 if precondition not met | Guard on status transition | Finalize button disabled until review state | 006, 011 |
| CONS-04 | Finalized consultation must have a responsible physician | Backend validates physician attribution on finalization | `POST /v1/consultations/{id}/finalize` | `finalized_by` field on consultation record | Physician name shown on finalized record | 006, 011 |
| CONS-05 | Failed or incomplete processing must not be treated as finalized | Backend blocks finalization for non-draft-generated states | Status guards in domain layer | `status` field remains pre-finalization | Error state shown in UI with retry option | 006 |

## 4. Consultation Inputs

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| INP-01 | MVP accepts consultation audio captured during consultation | Audio streamed via WebSocket, stored in S3 | WebSocket `audio.chunk` route | S3 `audio/raw.<ext>` object | Microphone capture in live consultation screen | 008 |
| INP-02 | Consultation is a single encounter tied to patient and physician | Enforced at creation time | `POST /v1/consultations` | Consultation record keys | Consultation form links patient and physician | 006 |
| INP-03 | System may use consultation metadata (date, time, specialty, patient ID, physician ID) | Stored as consultation attributes | `POST /v1/consultations` | DynamoDB consultation attributes | Pre-filled or selected on consultation creation | 006 |

## 5. Required Outputs

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| OUT-01 | Raw transcript | Transcription provider output normalized and stored | `GET /v1/consultations/{id}/review` includes transcript | S3 `transcripts/normalized.json` | Transcript panel in review screen | 009 |
| OUT-02 | Draft structured medical history | AI pipeline generates from normalized transcript | Part of review payload | S3 `ai/medical_history.json` | Editable medical history section in review screen | 010 |
| OUT-03 | Consultation summary | AI pipeline generates from transcript + medical history | Part of review payload | S3 `ai/summary.json` | Editable summary section in review screen | 010 |
| OUT-04 | Flagged insights for review | AI pipeline generates insight list with evidence | Part of review payload | S3 `ai/insights.json` | Insight cards with evidence excerpts in review screen | 010 |
| OUT-05 | Evidence excerpts linking insights to dialogue | Each insight includes source excerpt references | Part of review payload | Embedded in `ai/insights.json` | Clickable evidence links from insight to transcript | 010 |
| OUT-06 | Incomplete items marked as such, never fabricated | AI pipeline marks items with confidence; incomplete items flagged | Review payload includes completeness indicators | `completeness_status` per artifact | Visual indicator for incomplete/uncertain items | 010 |

## 6. Medical History Rules

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| MH-01 | Must reflect only consultation content | System prompt enforces report-only behavior | N/A (prompt design) | Validated against schema | N/A | 010 |
| MH-02 | Missing/unclear info marked as absent or unknown | Schema includes `status` field per section (confirmed, absent, unclear, needs_confirmation) | Part of review payload | `status` fields in `medical_history.json` | Visual distinction for uncertain vs confirmed data | 010 |
| MH-03 | Separate confirmed facts from uncertain info | Schema differentiates fact status | Part of review payload | Status categorization in JSON | Color-coded or labeled sections | 010, 012 |
| MH-04 | Preserve clinically relevant negatives only when explicitly stated | System prompt rule | N/A (prompt design) | Negative findings with `explicitly_stated: true` | Shown with "patient denied" phrasing | 010 |
| MH-05 | Must not fabricate symptoms, diagnoses, medications, allergies, findings, or plans | System prompt hard constraint + schema validation | N/A | Output validated against schema | N/A | 010 |

## 7. Summary Rules

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| SUM-01 | Summary in concise clinical language | System prompt enforces style | N/A (prompt design) | `summary.json` | Summary panel in review screen | 010 |
| SUM-02 | Faithful to transcript and medical history | Cross-referenced during generation | N/A | Evidence references in summary | N/A | 010 |
| SUM-03 | No new facts beyond consultation | System prompt constraint | N/A | Schema validation | N/A | 010 |
| SUM-04 | Follow-up items are reviewable drafts, not final direction | Labeled as "draft" in schema | Part of review payload | `draft_status: true` on follow-up items | "Draft" badge on follow-up items | 010, 012 |

## 8. Insight Rules

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| INS-01 | Only three insight categories: documentation_gap, consistency_issue, clinical_attention_flag | Schema enum restricts categories | Part of review payload | `category` enum in `insights.json` | Category labels on insight cards | 010 |
| INS-02 | Every insight includes supporting evidence | Schema requires `evidence_excerpts` array | Part of review payload | Evidence references in `insights.json` | Evidence shown below each insight | 010 |
| INS-03 | Insights are reviewable by physician | Physician can accept/dismiss each insight | `PUT /v1/consultations/{id}/review` | `physician_action` field per insight | Accept/dismiss buttons per insight | 011, 012 |
| INS-04 | Clinical attention flags are not diagnoses | System prompt + schema labeling | N/A | `disclaimer` field in insight schema | Disclaimer text on clinical flags | 010 |
| INS-05 | No treatment recommendations or prescriptions | System prompt hard constraint | N/A | Schema validation | N/A | 010 |

## 9. Physician Review and Finalization

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| REV-01 | No AI output is final until physician review | Status must reach `under_physician_review` before finalization | State machine guards | `status` field | "Draft" labels on all AI output | 006, 011 |
| REV-02 | Physician can edit medical history, summary, and insights | Backend accepts partial edits, stores physician version | `PUT /v1/consultations/{id}/review` | `physician_edits` object in DynamoDB + S3 | Editable text fields in review screen | 011 |
| REV-03 | Final record requires explicit physician confirmation | Finalization is a deliberate action, not automatic | `POST /v1/consultations/{id}/finalize` | `finalized_at`, `finalized_by` fields | Explicit "Finalize" button with confirmation dialog | 011, 012 |
| REV-04 | All AI content labeled as subject to medical review | BFF injects disclaimer text | BFF response includes disclaimer metadata | UI config | Persistent disclaimer banner during review | 007, 012 |
| REV-05 | Only the confirmed version is considered complete | Backend marks `status=finalized` and locks edits | Finalization endpoint | `status` + `is_locked` flags | Read-only view after finalization | 011 |

## 10. Privacy and Retention

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| PRIV-01 | Consultation data is sensitive health information | KMS encryption at rest, TLS in transit, least-privilege IAM | All endpoints | All consultation data | N/A (infrastructure) | 004, 014 |
| PRIV-02 | Access limited to authorized users within clinic context | Tenant-aware authorization; clinic_id checked on every request | All protected endpoints | `clinic_id` on consultation records | Only own-clinic consultations visible | 005, 006 |
| PRIV-03 | Support retaining or deleting audio per clinic policy | Configurable retention policy; S3 lifecycle rules | Future admin endpoint or config | `audio_retention_policy` on clinic record | N/A (admin config, not physician-facing in MVP) | 014 |
| PRIV-04 | Clinic may retain final note even if audio deleted | Audio deletion does not cascade to finalized artifacts | Deletion logic in backend | S3 objects decoupled per artifact type | N/A | 014 |
| PRIV-05 | Logs must avoid unnecessary PII exposure | Structured logs with masked PII, no raw audio or transcript in logs | N/A (operational) | N/A | N/A | 014 |

## 11. Evidence and Audit

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| AUD-01 | Insights traceable to consultation excerpts | Evidence array per insight with transcript offsets | Part of review payload | `evidence_excerpts` in `insights.json` | Clickable links from insight to transcript position | 010 |
| AUD-02 | Clear distinction between source content and generated summaries | Artifact types separated in storage and API | Separate fields in review payload | Separate S3 objects per artifact type | Visually distinct sections | 010, 012 |
| AUD-03 | Edits and approvals attributable to human user | Audit events with `actor_id`, `action`, `timestamp` | Recorded on every edit and finalization | DynamoDB audit events `CONSULTATION#<id> / AUDIT#<ts>` | Audit trail visible to authorized users (future) | 006 |

## 12. Transcription Provider

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| ASR-01 | Provider must support pt-BR | Provider adapter validates language support | N/A (infrastructure) | `provider_name` and `language` in transcript record | N/A | 009 |
| ASR-02 | English-only providers excluded | Provider selection logic rejects non-pt-BR providers | N/A | N/A | N/A | 009 |
| ASR-03 | Provider abstracted behind internal interface | Adapter pattern with port interface | Internal service layer | Provider-agnostic normalized transcript model | N/A | 009 |

## 13. MVP Boundaries

| ID | Business Rule | Backend Behavior | API Endpoint | Data Entity | UI Flow | Task |
|----|---------------|-----------------|--------------|-------------|---------|------|
| BND-01 | No automatic diagnoses | System prompt + schema validation block diagnostic output | N/A | N/A | N/A | 010 |
| BND-02 | No automatic prescriptions | System prompt + schema validation block prescription output | N/A | N/A | N/A | 010 |
| BND-03 | No multi-specialty within same consultation | Single `specialty` field enforced at creation | `POST /v1/consultations` validates single specialty | `specialty` field on consultation record | Single specialty selector | 006 |
| BND-04 | No deep EHR integration | No external system writes | N/A | N/A | N/A | N/A |
| BND-05 | Documentation tool only, not clinical decision-maker | All output labeled as draft/review, no authoritative clinical actions | Disclaimer in all review payloads | N/A | Disclaimers throughout review screens | 007, 010, 012 |
