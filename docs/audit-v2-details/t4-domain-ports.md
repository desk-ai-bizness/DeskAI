# Phases 3-4: Domain + Ports Audit

**Auditor**: Agent T4
**Commit**: 75715f2
**Files Read**: 55 domain files + 16 port files + 2 requirements docs + 1 shared module

---

## Domain Layer Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| D-01 | LOW | `domain/consultation/test.tmp:1` | Junk test file committed to domain layer | `"x"` | Delete `test.tmp` — does not belong in domain source tree | D1 |
| D-02 | LOW | `domain/session/test.tmp:1` | Junk test file committed to domain layer | `"x"` | Delete `test.tmp` — does not belong in domain source tree | D1 |
| D-03 | HIGH | `domain/consultation/entities.py:19` | Consultation aggregate root is NOT frozen | `@dataclass` (no `frozen=True`) | Consultation is the core aggregate root. It should be immutable with `frozen=True`. Transitions should return new instances, not mutate. | D2 |
| D-04 | HIGH | `domain/session/entities.py:18` | Session aggregate is NOT frozen | `@dataclass` (no `frozen=True`) | Session should be immutable. State changes should produce new instances via copy-with-update pattern. | D2 |
| D-05 | HIGH | `domain/transcription/entities.py:12` | NormalizedTranscript entity is NOT frozen | `@dataclass` (no `frozen=True`) | Should be frozen. Docstring even says "Mutable entity" — this is an anti-pattern in DDD hexagonal. | D2 |
| D-06 | HIGH | `domain/consultation/services.py:48-52` | `transition_consultation()` mutates entity in place via `setattr` | `consultation.status = new_status`; `setattr(consultation, key, value)` | With frozen=True this would fail. Redesign to return new `Consultation` instance via `dataclasses.replace()`. The `setattr` with `**kwargs` also bypasses all type checking — any arbitrary attribute can be set. | D3 |
| D-07 | MEDIUM | `domain/consultation/value_objects.py:27-33` | `ArtifactPointer.s3_key` — infrastructure concept in domain value object | `s3_key: str` | Rename to `storage_key` or `artifact_key`. The domain should not know about S3. | D8 |
| D-08 | HIGH | `domain/consultation/value_objects.py:26-33` | `ArtifactPointer` has NO `__post_init__` validation | `@dataclass(frozen=True)` with no validation | Can create `ArtifactPointer(artifact_type=ArtifactType.TRANSCRIPT_RAW, s3_key="", version="")` — empty key is semantically invalid but accepted. | D6 |
| D-09 | HIGH | `domain/session/value_objects.py:6-13` | `AudioChunk` has NO `__post_init__` validation | `chunk_index: int` with no guard | Can create `AudioChunk(chunk_index=-1, audio_data=b"", timestamp="", session_id="")` — negative index, empty bytes, empty session all accepted. | D6 |
| D-10 | HIGH | `domain/transcription/value_objects.py:22-30` | `SpeakerSegment` has NO `__post_init__` validation | `start_time: float`, `end_time: float` with no guard | Can create `SpeakerSegment(speaker="", text="", start_time=10.0, end_time=5.0, confidence=-1.0)` — start > end, negative confidence all accepted. | D6 |
| D-11 | MEDIUM | `domain/transcription/value_objects.py:33-41` | `PartialTranscript` has NO `__post_init__` validation | `confidence: float` with no guard | Can create `PartialTranscript(text="", speaker="", is_final=False, timestamp="", confidence=-5.0)` — negative confidence accepted. | D6 |
| D-12 | MEDIUM | `domain/session/value_objects.py:16-24` | `ConnectionInfo` has NO `__post_init__` validation | All `str` fields with no guards | Can create `ConnectionInfo(connection_id="", session_id="", doctor_id="", clinic_id="", connected_at="")` — all empty strings accepted. | D6 |
| D-13 | MEDIUM | `domain/auth/value_objects.py:15-22` | `AuthContext` has NO `__post_init__` validation | All `str` fields with no guards | Can create `AuthContext(doctor_id="", email="not-an-email", clinic_id="", plan_type=PlanType.FREE_TRIAL)` — no email format validation. | D6 |
| D-14 | MEDIUM | `domain/auth/value_objects.py:25-35` | `Entitlements` has NO `__post_init__` validation | `consultations_remaining: int` with no guard | Can create `Entitlements(can_create_consultation=True, consultations_remaining=-999, ...)` — negative remaining accepted. | D6 |
| D-15 | HIGH | `domain/session/entities.py:7-15` + `domain/session/services.py` | `SessionState` has NO transition enforcement | 6 states defined: `CONNECTING, ACTIVE, RECORDING, STOPPING, ENDED, DISCONNECTED` — but no `ALLOWED_TRANSITIONS` dict | Unlike `ConsultationStatus` which has `ALLOWED_TRANSITIONS` in `consultation/services.py`, `SessionState` has NO equivalent. Any state can transition to any other state without validation. `SessionService` validates individual operations but doesn't enforce a general state machine. | D7 |
| D-16 | MEDIUM | `domain/auth/entities.py:10-11` | `DoctorProfile` docstring references infrastructure | `"""Doctor identity and clinic context resolved from DynamoDB."""` | Remove "DynamoDB" reference from domain entity docstring. Domain should be storage-agnostic. | — |
| D-17 | MEDIUM | `domain/auth/value_objects.py:17` | `AuthContext` docstring references infrastructure | `"""Authenticated request context resolved from Cognito claims and DynamoDB profile."""` | Remove "Cognito" and "DynamoDB" references from domain value object docstring. | — |
| D-18 | MEDIUM | `domain/consultation/entities.py:40` | `error_details` typed as `dict | None` | `error_details: dict | None = None` | Should be a domain value object (e.g., `ErrorDetails` with `error_type: str`, `error_message: str`) instead of untyped dict. Loses type safety. | — |
| D-19 | LOW | `domain/transcription/entities.py:4,22-23` | `typing.Any` used in domain entity | `timestamps: dict[str, Any] \| None`, `confidence_metadata: dict[str, Any] \| None` | Replace with typed domain value objects. `Any` bypasses type checking entirely. | — |
| D-20 | LOW | `domain/transcription/services.py:3` | `typing.Any` used in domain service | `from typing import Any` — used in multiple method signatures | Internal methods accepting `dict[str, Any]` should use typed value objects or at minimum `dict[str, object]`. | — |
| D-21 | MEDIUM | `domain/consultation/rules.py:6-27` | `validate_consultation_creation` only checks emptiness | `if not patient_id:` | No UUID format validation, no `specialty` enum validation. A string like `specialty="INVALID"` passes validation. Compare with `Specialty` enum in `value_objects.py` — it exists but `rules.py` doesn't use it. | — |
| D-22 | MEDIUM | `domain/consultation/entities.py:28` | `specialty` field is plain `str`, not `Specialty` enum | `specialty: str` | The `Specialty` enum exists in `value_objects.py` but the entity uses plain `str`. No type-safe enforcement. | — |

---

## Domain Module Inventory

| Subdomain | Real Files | Stub Files | test.tmp? | Notes |
|-----------|-----------|------------|-----------|-------|
| `auth/` | entities.py, exceptions.py, services.py, value_objects.py | None | No | Fully implemented: DoctorProfile, plan entitlements, auth flow |
| `consultation/` | entities.py, events.py, exceptions.py, rules.py, services.py, value_objects.py | None | **YES** | Core aggregate. State machine implemented. Mutable entity is primary concern. |
| `session/` | entities.py, exceptions.py, services.py, value_objects.py | None | **YES** | SessionService has validation logic but no state transition map. |
| `patient/` | entities.py, exceptions.py | services.py, value_objects.py | No | Patient entity is frozen (good). Services and VOs are stubs. |
| `transcription/` | entities.py, exceptions.py, services.py, value_objects.py | None | No | Most complex service (TranscriptionNormalizer). Entity is mutable. |
| `ai_pipeline/` | None | **ALL 4 files** (entities, exceptions, services, value_objects) | No | Completely empty subdomain. Zero implementation. |
| `audit/` | entities.py | exceptions.py, services.py, value_objects.py | No | AuditEvent entity exists. No audit service logic. |
| `review/` | None | **ALL 4 files** | No | Completely empty subdomain. Zero implementation. |
| `export/` | None | **ALL 4 files** | No | Completely empty subdomain. Zero implementation. |
| `config/` | None | **ALL 4 files** | No | Completely empty subdomain. Zero implementation. |

**Summary**: 4 of 10 subdomains are complete stubs (ai_pipeline, review, export, config). 1 subdomain (audit) is mostly stub. 2 subdomains (patient) are partially stub.

---

## State Machine Analysis

### ConsultationStatus — Implementation vs Requirements

**States defined** (entities.py:7-16):

| State | In Code | In Lifecycle Doc (02) | In Business Rules (16) | Match? |
|-------|---------|----------------------|----------------------|--------|
| `started` | YES | YES | YES | PASS |
| `recording` | YES | YES | YES | PASS |
| `in_processing` | YES | YES | YES (as "in processing") | PASS |
| `processing_failed` | YES | YES | YES | PASS |
| `draft_generated` | YES | YES | YES | PASS |
| `under_physician_review` | YES | YES | YES | PASS |
| `finalized` | YES | YES | YES | PASS |

**All 7 states match.** No missing or extra states.

**Transitions defined** (services.py:7-21):

| From | To | In Code | In Lifecycle Doc | Match? |
|------|----|---------|-----------------|--------|
| started | recording | YES | YES | PASS |
| recording | in_processing | YES | YES | PASS |
| in_processing | draft_generated | YES | YES | PASS |
| in_processing | processing_failed | YES | YES | PASS |
| processing_failed | in_processing | YES | YES | PASS |
| draft_generated | under_physician_review | YES | YES | PASS |
| under_physician_review | under_physician_review | YES | YES (edits) | PASS |
| under_physician_review | finalized | YES | YES | PASS |
| finalized | (none) | YES (empty set) | YES (terminal) | PASS |

**All 9 transitions match.** No missing or extra transitions.

**Forbidden transitions** (per lifecycle doc Section 3): All forbidden transitions are correctly blocked because `ALLOWED_TRANSITIONS` is a whitelist — anything not in the set is rejected. Verified:
- started -> in_processing: NOT in set. BLOCKED.
- started -> finalized: NOT in set. BLOCKED.
- recording -> draft_generated: NOT in set. BLOCKED.
- in_processing -> finalized: NOT in set. BLOCKED.
- draft_generated -> finalized: NOT in set. BLOCKED.
- processing_failed -> finalized: NOT in set. BLOCKED.
- processing_failed -> draft_generated: NOT in set. BLOCKED.
- finalized -> any: empty set. ALL BLOCKED.

**Double finalization**: `validate_transition(FINALIZED, FINALIZED)` returns `False` because `FINALIZED` maps to `set()`. This correctly rejects double finalization at the domain level. However, the idempotency rule (lifecycle doc Section 4) says duplicate finalize should "return the finalized record" — this must be handled at the application layer, not domain.

**CRITICAL GAP**: `transition_consultation()` mutates the entity in place (D-06). If the consultation were frozen, this function would need to return a new instance. The current design works only because the entity is mutable, which is itself the problem.

### SessionState — NO State Machine

**States defined** (session/entities.py:7-15):
- CONNECTING, ACTIVE, RECORDING, STOPPING, ENDED, DISCONNECTED

**Transition enforcement**: NONE. There is no `ALLOWED_TRANSITIONS` equivalent. `SessionService` validates individual operations (e.g., "can only accept audio in RECORDING or ACTIVE state") but does not define a general state machine. Any code with a reference to a Session can set `session.state = SessionState.ENDED` from `SessionState.CONNECTING` without any guard.

**Expected transitions** (inferred from lifecycle doc + session service logic):
- CONNECTING -> ACTIVE (connection established)
- ACTIVE -> RECORDING (audio starts flowing)
- RECORDING -> STOPPING (end requested)
- STOPPING -> ENDED (stop confirmed)
- RECORDING -> DISCONNECTED (WebSocket drops)
- ACTIVE -> DISCONNECTED (WebSocket drops)
- DISCONNECTED -> ACTIVE (reconnection within grace period)
- DISCONNECTED -> ENDED (grace period expired)

None of these are enforced as a map.

---

## Business Rule Enforcement Mapping

| Business Rule (from mvp-business-rules.md) | Domain Code? | Notes |
|---------------------------------------------|-------------|-------|
| Section 4: Email+password auth only, no social login | auth/exceptions.py has `AuthenticationError` | Enforcement is in AuthProvider port, not domain. Domain has no "reject social login" rule. |
| Section 5: Plan types (free_trial, plus, pro) | auth/value_objects.py `PlanType` enum | PASS — 3 types match exactly. |
| Section 5: Plan-based access control | auth/services.py `compute_entitlements()` | PASS — monthly limits, trial expiry, duration limits all computed. |
| Section 7: Required outputs (transcript, history, summary, insights, evidence) | consultation/value_objects.py `ArtifactType` enum | Enum has 8 types including TRANSCRIPT_RAW, TRANSCRIPT_NORMALIZED, MEDICAL_HISTORY, SUMMARY, INSIGHTS. Evidence is NOT a separate artifact type. |
| Section 8-10: AI content rules (no fabrication, evidence required) | **NONE** | No domain enforcement. These are prompt-level rules, not coded in domain. Acceptable for MVP. |
| Section 11: Physician must review before finalization | consultation/rules.py `can_finalize()` + services.py transition map | PASS — `can_finalize` checks `UNDER_PHYSICIAN_REVIEW`. Transition map only allows `UNDER_PHYSICIAN_REVIEW -> FINALIZED`. |
| Section 15: Clinic-scoped access | patient/entities.py has `clinic_id`, consultation/entities.py has `clinic_id` | Data model supports it. Enforcement is at application/port layer. |
| Section 16: Finalized is immutable | consultation/services.py `FINALIZED: set()` | PASS — empty transition set means no transitions out of FINALIZED. |
| Section 16: Cannot finalize before review | consultation/services.py transition map | PASS — no path from any pre-review state to FINALIZED. |
| Section 17: Only finalized consultations may be exported | **NONE** | No domain rule for this. Export subdomain is completely stub. Must be enforced elsewhere. |
| Section 13: pt-BR transcription | transcription/value_objects.py `TranscriptionLanguage.PT_BR` | Enum exists but normalizer hardcodes `"pt"` -> `"pt-BR"` mapping. No enforcement that ONLY pt-BR is used. |

---

## Ports Layer Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| P-01 | HIGH | `ports/doctor_repository.py:12` | Infrastructure concept "cognito" leaks into port interface | `def find_by_cognito_sub(self, cognito_sub: str) -> DoctorProfile \| None:` | Rename to `find_by_identity_provider_id(self, provider_id: str)` or `find_by_external_sub(self, sub: str)`. The port should not name a specific identity provider. | P1 |
| P-02 | MEDIUM | `ports/artifact_repository.py:17,27` | Returns/accepts raw `dict` instead of domain objects | `data: dict` / `-> dict \| None` | Should accept/return `ArtifactPointer` or typed domain value objects. Raw dicts bypass type safety. | P2 |
| P-03 | MEDIUM | `ports/transcript_repository.py:14,23,32` | All methods use raw `dict` for transcript data | `raw_response: dict`, `normalized: dict`, `-> dict \| None` | Should use `NormalizedTranscript` domain entity for normalized, and a typed VO for raw. | P2 |
| P-04 | MEDIUM | `ports/llm_provider.py:10-14` | Returns/accepts raw `dict[str, object]` | `payload: dict[str, object]` / `-> dict[str, object]` | Should use typed domain value objects (e.g., `GenerationRequest`, `GenerationResult`). | P2 |
| P-05 | MEDIUM | `ports/transcription_provider.py:11,19,23` | Returns raw `dict[str, Any]` | `-> dict[str, Any]` | Should return typed domain value objects instead of untyped dicts. | P2 |
| P-06 | HIGH | `ports/config_repository.py` | Stub — 34 bytes, `# Placeholder` equivalent | `"""Port interface placeholder."""` | Architecture docs reference config management. This port is needed for feature flags, plan config, etc. | P3 |
| P-07 | HIGH | `ports/event_publisher.py` | Stub — 34 bytes | `"""Port interface placeholder."""` | Required for domain events (ConsultationCreated, ConsultationStatusChanged from events.py). Events exist but no port to publish them. | P3 |
| P-08 | HIGH | `ports/export_generator.py` | Stub — 34 bytes | `"""Port interface placeholder."""` | Business rules (Section 17) require PDF export of finalized consultations. No port exists. | P3 |
| P-09 | MEDIUM | `ports/storage_provider.py` | Stub — 34 bytes | `"""Port interface placeholder."""` | Needed for audio chunk storage and general blob storage. Currently artifact_repository partially covers this. | P3 |
| P-10 | MEDIUM | `ports/consultation_repository.py:26-29` | `update_status` uses `**kwargs: object` | `def update_status(self, consultation_id: str, new_status: ConsultationStatus, **kwargs: object) -> None:` | Same `**kwargs` anti-pattern from domain service bleeds into port. Should accept explicit fields (e.g., `finalized_at`, `error_details`). | — |
| P-11 | LOW | `ports/audit_repository.py:12-16` | Missing `query_events` with filtering | Only `append` and `find_by_consultation` | No way to query by actor, date range, or event type. Audit query requirements (lifecycle doc Section 7) suggest richer query API needed. | — |
| P-12 | LOW | `ports/auth_provider.py` | Missing `refresh_token` operation | Only `authenticate`, `sign_out`, `forgot_password`, `confirm_forgot_password` | No token refresh capability. Frontend will need this for long sessions. | — |
| P-13 | LOW | `ports/consultation_repository.py` | Missing `delete` operation | Only `save`, `find_by_id`, `find_by_doctor_and_date_range`, `update_status` | No deletion capability, even for cleanup/retention policies. | — |
| P-14 | MEDIUM | All ports | Zero async ports | All methods are synchronous `def`, none are `async def` | Transcription streaming, WebSocket operations, and S3 I/O are inherently async. At minimum `TranscriptionProvider` and `ConnectionRepository` should be async. | — |
| P-15 | MEDIUM | (missing) | No notification port | — | Business rules mention notifications to physician when draft is ready. No port exists for push notifications, email, or in-app alerts. | — |
| P-16 | LOW | (missing) | No metrics/observability port | — | No port for business metrics (consultations created, processing times, failure rates). | — |
| P-17 | LOW | (missing) | No health check port | — | No port for dependency health checks (Cognito, DynamoDB, S3, transcription provider). | — |

---

## Port Completeness Matrix

| Port | Methods | Return Types | Async? | Domain Objects? | Notes |
|------|---------|-------------|--------|----------------|-------|
| `artifact_repository.py` | `save_artifact`, `get_artifact` | `None`, `dict \| None` | No | NO — raw dict | Missing: delete, list by consultation, version management |
| `audit_repository.py` | `append`, `find_by_consultation` | `None`, `list[AuditEvent]` | No | YES | Missing: query by actor/date/type, pagination |
| `auth_provider.py` | `authenticate`, `sign_out`, `forgot_password`, `confirm_forgot_password` | `Tokens`, `None`, `None`, `None` | No | YES (Tokens) | Missing: refresh_token, change_password, verify_email |
| `config_repository.py` | **STUB** | — | — | — | 34 bytes, placeholder |
| `connection_repository.py` | `save`, `find_by_connection_id`, `remove` | `None`, `ConnectionInfo \| None`, `None` | No | YES | Adequate for WebSocket lifecycle |
| `consultation_repository.py` | `save`, `find_by_id`, `find_by_doctor_and_date_range`, `update_status` | `None`, `Consultation \| None`, `list[Consultation]`, `None` | No | YES | Missing: delete, count, paginated list |
| `doctor_repository.py` | `find_by_cognito_sub`, `count_consultations_this_month` | `DoctorProfile \| None`, `int` | No | YES | "cognito" in method name leaks infra |
| `event_publisher.py` | **STUB** | — | — | — | 34 bytes, placeholder |
| `export_generator.py` | **STUB** | — | — | — | 34 bytes, placeholder |
| `llm_provider.py` | `generate_structured_output` | `dict[str, object]` | No | NO — raw dict | Missing: batch generation, prompt selection |
| `patient_repository.py` | `save`, `find_by_id`, `find_by_clinic` | `None`, `Patient \| None`, `list[Patient]` | No | YES | Good — clinic-scoped access present |
| `session_repository.py` | `save`, `find_by_id`, `find_active_by_consultation_id`, `update`, `delete` | `None`, `Session \| None`, `Session \| None`, `None`, `None` | No | YES | Full CRUD. Good coverage. |
| `storage_provider.py` | **STUB** | — | — | — | 34 bytes, placeholder |
| `transcript_repository.py` | `save_raw_transcript`, `save_normalized_transcript`, `get_normalized_transcript` | `None`, `None`, `dict \| None` | No | NO — raw dict | Missing: get_raw, delete, domain object returns |
| `transcription_provider.py` | `start_realtime_session`, `send_audio_chunk`, `finish_realtime_session`, `fetch_final_transcript`, `get_session_state` | `dict[str, Any]`, `None`, `dict[str, Any]`, `dict[str, Any]`, `str` | No | NO — raw dict | Good method coverage but all returns are untyped dicts |

---

## Pre-Investigation Verification

| Pre-Inv # | Status | Notes |
|-----------|--------|-------|
| D1 | **CONFIRMED** | Two `test.tmp` files found: `domain/consultation/test.tmp` and `domain/session/test.tmp`. Both contain `"x"` (1 line). |
| D2 | **CONFIRMED** (expanded) | Pre-inv mentioned mutable entities. Found 3: `Consultation` (line 19), `Session` (line 18), `NormalizedTranscript` (line 12). All `@dataclass` without `frozen=True`. |
| D3 | **CONFIRMED** | `transition_consultation()` at services.py:48 uses `consultation.status = new_status` and lines 51-52 use `setattr(consultation, key, value)` for arbitrary attribute injection. |
| D6 | **CONFIRMED** (expanded) | Zero `__post_init__` methods in the ENTIRE domain layer. Verified via grep. Affects ALL frozen dataclasses: `ArtifactPointer`, `AudioChunk`, `SpeakerSegment`, `PartialTranscript`, `ConnectionInfo`, `AuthContext`, `Entitlements`, `Tokens`, `ConsultationCreated`, `ConsultationStatusChanged`, `AuditEvent`, `DoctorProfile`, `Patient`. |
| D7 | **CONFIRMED** | `SessionState` enum defines 6 states but has NO `ALLOWED_TRANSITIONS` dict and no transition validation function. Contrast with `ConsultationStatus` which has a complete transition map. |
| D8 | **CONFIRMED** | `ArtifactPointer.s3_key` at value_objects.py:31. S3 is an infrastructure concept that should not appear in domain. |
| D10 | **CONFIRMED (PASS)** | Zero imports from `boto3`, `botocore`, `aws_cdk`, `aws_lambda_powertools`, `fastapi`, `flask`, `django` in entire domain layer. Verified via grep. The domain is clean of infrastructure imports. Note: docstring references to DynamoDB/Cognito exist (D-16, D-17) but no actual import violations. |
| P1 | **CONFIRMED** | `doctor_repository.py:12`: `find_by_cognito_sub(self, cognito_sub: str)`. "cognito" is an infrastructure concept (AWS Cognito) that should not appear in a port interface name. |
| P2 | **CONFIRMED** (expanded) | 4 ports return raw `dict` instead of domain objects: `artifact_repository.py` (lines 17, 27), `transcript_repository.py` (lines 14, 23, 32), `llm_provider.py` (lines 13-14), `transcription_provider.py` (lines 11, 19, 23). |
| P3 | **NEW** | 4 ports are 34-byte stubs: `config_repository.py`, `event_publisher.py`, `export_generator.py`, `storage_provider.py`. |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Domain files read | 55 |
| Port files read | 16 |
| Total findings (domain) | 22 |
| Total findings (ports) | 17 |
| HIGH severity (domain) | 7 |
| HIGH severity (ports) | 4 |
| MEDIUM severity (domain) | 8 |
| MEDIUM severity (ports) | 7 |
| LOW severity (domain) | 3 |
| LOW severity (ports) | 4 |
| Stub subdomains (all files placeholder) | 4 (ai_pipeline, review, export, config) |
| Stub ports (34 bytes) | 4 (config, event_publisher, export_generator, storage) |
| Mutable entities (should be frozen) | 3 |
| Value objects missing `__post_init__` | 13 (ALL frozen dataclasses) |
| Ports returning raw dict | 4 |
| Zero hexagonal import violations | CONFIRMED |
| State machine match (consultation) | 7/7 states, 9/9 transitions |
| State machine match (session) | 6 states defined, 0 transitions enforced |
