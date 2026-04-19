# Task 023: Implement Realtime Consultation Data Feed

## 1. Overview

### Objective
Replace the stub live transcript with a real realtime consultation data feed, decouple post-session finalization from the `session.stop` Lambda invocation, add backend-owned event contracts for pause/resume and provisional updates, and close the remaining multi-container chunk accumulation bug.

### Why This Matters
The consultation workspace is the core product experience. Doctors need live transcript and session state that reflect the actual consultation, not placeholder text. This task resolves the stub transcript gap (OI-016) before the consultation workspace is redesigned in Task 024, resolves the synchronous finalization risk (OI-015), and closes the remaining audio chunk collision bug so recordings produce the correct audio on `session.stop`.

### Task Type
- Full Stack

### Priority
- Critical

## 2. Context

### Product Context
During a consultation, the doctor should see live transcript progress as the patient and doctor speak. Pause/resume should be deliberate UI state. Provisional AI/autofill events will be emitted from a later task, but their contract must be defined here so Task 024 can build the workspace without contract drift.

### Technical Context
- Task 008 added WebSocket session transport.
- Task 009 integrated the ElevenLabs Scribe v2 transcription provider (HTTP batch upload at finalization).
- Task 010 added the AI processing pipeline.
- `handlers/websocket/audio_chunk_handler.py` still sends a placeholder `transcript.partial` event (`"[stub transcript]"`) for every audio chunk. Real transcription only happens in a synchronous batch POST inside `session.stop`, which risks Lambda timeouts for anything longer than a short recording.
- `ElevenLabsScribeProvider` now persists audio chunks to S3 via `S3Client.put_bytes` (partial fix landed on `main`), but `_SessionEntry.chunk_count` lives in the Lambda container. When audio chunks spread across concurrent warm containers they all write `000000.bin`, `000001.bin`, … and **overwrite each other's keys**. `session.stop` reassembles only a subset of the audio.
- The AI pipeline is currently triggered inline from `session.stop` (best effort, exceptions swallowed to a log line).

### Related Systems
- Backend API
- WebSocket API
- Transcription provider (ElevenLabs Scribe v2 Realtime)
- AI pipeline / Step Functions
- EventBridge
- Frontend app
- Storage (S3 for audio, artifacts)
- Observability

### Dependencies
- `008-implement-realtime-consultation-session-transport.md`
- `009-integrate-transcription-provider-and-normalization.md`
- `010-build-ai-processing-pipeline-and-artifacts.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/04-failure-behavior-matrix.md`
- `contracts/websocket/session.yaml`
- `contracts/websocket/events.yaml`

## 3. Scope

### In Scope

**Realtime transcript path (decided: client-side direct streaming — Path A).**
- Browser opens a direct WebSocket to ElevenLabs Scribe v2 Realtime (`wss://api.elevenlabs.io/v1/speech-to-text/realtime`).
- Backend exposes a short-lived token endpoint `POST /v1/consultations/{id}/transcription-token` that returns a provider token with least-privilege scope and a short TTL. The long-lived ElevenLabs API key stays in Secrets Manager.
- Frontend streams mic audio directly to ElevenLabs, receives `partial_transcript` and `committed_transcript` events from the provider, and forwards committed segments (and a small curated set of partials, if we decide to persist them) to the backend for durable persistence through the existing app WebSocket.
- The app WebSocket `audio.chunk` route no longer carries audio bytes to the backend. Option: retire the route entirely, or keep it behind a feature flag for the legacy path. Decision must be captured in the task's decision log.
- `[stub transcript]` events must be fully removed.
- `transcript.partial` / `transcript.final` contracts stay the physician-facing shape; frontend may derive them from provider events or receive them back through the backend if we persist committed segments in near real time.

**Async post-session finalization (OI-015).**
- `session.stop` (both HTTP `session/end` and WebSocket `session.stop`) must:
  1. Transition session + consultation state (already done).
  2. Emit a domain event — `consultation.session.stopped` — via `EventBridgePublisher`.
  3. Return success to the client.
- Finalization runs in a separate Lambda triggered by EventBridge:
  - Collect committed transcript segments (if persisted) or reassemble audio and request a final transcript.
  - Persist raw + normalized transcripts.
  - Enqueue or trigger the AI pipeline Step Function.
- Finalization failures must surface as session warnings to the client (via `session.warning` on the next connection or through consultation detail warnings) and as CloudWatch alarms — never silent.

**Pause/Resume.**
- Add client→server actions `session.pause` and `session.resume` (or equivalent) in `contracts/websocket/session.yaml`.
- Add server→client event `session.status` with new status values `paused` and (already existing) `recording`.
- Add session state transitions `RECORDING ↔ PAUSED` with explicit validation and audit trail.
- Pause must stop forwarding audio chunks; resume must allow them again.

**Provisional update contracts (schema only; emitter ships in Task 024).**
- Add server→client event `insight.provisional` with a draft/incomplete flag and required evidence excerpt reference.
- Add server→client event `autofill.candidate` with field key, candidate value, and evidence reference.
- These events must be marked clearly as provisional in the contract and must not be presented as authoritative clinical content.
- Emitter implementation and frontend rendering belong to Task 024. This task only adds the schemas, TypeScript types, and (optionally) an internal helper for emitting them.

**Chunk concurrency bug fix.**
- Make the S3 audio chunk key globally unique across concurrent Lambda containers. Option A: embed client-provided `chunk_index` (already present in the `audio.chunk` schema). Option B: use `{timestamp}-{uuid4}.bin`. Prefer A when the schema enforces monotonic indices; otherwise B.
- If the legacy backend `audio.chunk` path is retired with Path A, this bug becomes moot. The fix still applies to any transitional period or legacy fallback.
- Finalization must reassemble chunks in the client-issued order, not S3 lexicographic order, when the order matters.

**Safety and observability.**
- PHI-safe logging tests covering realtime event handlers (no raw transcript, audio, or CPF in logs).
- Version the WebSocket event schemas (bump header or add `event_version` field, whichever is already in place) to prevent frontend/backend drift.
- Provider failures must surface as actionable session warnings.

### Out of Scope
- Redesigning the consultation workspace UI. That belongs to Task 024.
- Emitting `insight.provisional` / `autofill.candidate` events at runtime. Schemas only in this task.
- Changing final review, finalization, or export business rules.
- Adding automatic diagnoses, automatic prescriptions, or authoritative clinical suggestions.
- Adding post-consultation upload as a primary workflow.
- Changing the long-lived ElevenLabs API key management (stays in Secrets Manager).
- Migrating authentication token delivery (tracked by Task 025).

## 4. Requirements

### Functional Requirements
- Frontend receives and renders real live transcript updates during a recording session.
- The `[stub transcript]` placeholder is gone from every code path and test fixture.
- Pause/resume is represented in backend state and WebSocket events; the frontend can pause and resume audio streaming accordingly.
- `POST /v1/consultations/{id}/transcription-token` returns a short-lived token scoped to the current consultation and doctor.
- `session.stop` returns a successful response in constant time (no awaiting of ElevenLabs or the LLM pipeline).
- Post-session finalization (transcript persistence, AI pipeline trigger) runs in a separate Lambda invocation triggered by EventBridge.
- Finalization failures are observable and recoverable (retries, DLQ, and a session warning channel).
- Final persisted transcript and AI artifacts remain compatible with the review/finalization/export pipeline.
- Provisional update contracts exist and are documented, even though emission is deferred to Task 024.

### Non-Functional Requirements
- Realtime path is resilient to browser reconnects and provider disconnects.
- Logs do not contain raw audio, raw transcript, CPF, or patient-identifiable data.
- Event contracts are versioned.
- Provider failures surface as actionable session warnings without silently hiding failures.
- The transcription token endpoint enforces authentication, ownership (doctor owns the consultation), and a short TTL.

### Business Rules
- The system reports what was said; it must never interpret what it means as a clinical decision.
- The system must not fabricate symptoms, diagnoses, medications, allergies, findings, plans, or follow-up instructions.
- Insights are review flags, not conclusions.
- Clinical attention flags must never be presented as diagnoses.
- AI-generated output is not final until physician review and explicit finalization.

### Technical Rules
- Keep provider-specific logic in adapters, not the domain core.
- Keep WebSocket event shapes in `contracts/websocket/`.
- Follow strict TDD for event schemas, session state transitions, provider integration behavior, token endpoint, async finalization worker, and frontend event rendering.
- Prefer event-driven handling for finalization; keep handler code paths small and Lambda-timeout-safe.

## 5. Implementation Notes

### Proposed Approach
1. Write failing contract tests asserting: `[stub transcript]` events are no longer emitted, pause/resume schemas exist, provisional schemas exist, and `session.stop` does not invoke the provider or finalize use cases directly.
2. Add the transcription token HTTP endpoint, use case, and BFF view. Keep tokens short-lived and bound to `{consultation_id, doctor_id}`.
3. Modify `audio_chunk_handler.py` to remove the stub event. Decide legacy vs retired (see "Transitional Behavior" below).
4. Add `session.pause`/`session.resume` actions, update `SessionService`, repo state, audit events, and `events.yaml`.
5. Add `EventBridgePublisher` emit in `session.stop` and HTTP `session/end`. Remove inline `fetch_final_transcript` / AI pipeline calls.
6. Build a new finalization Lambda triggered by EventBridge. Move the existing finalize + pipeline orchestration into it. Wire retries and DLQ.
7. Fix the chunk key collision: include `chunk_index` or uuid in the S3 key, and have the reader sort by client-issued order.
8. Add provisional update contract definitions (`insight.provisional`, `autofill.candidate`) with a clear "emitter in Task 024" note in the schema description.
9. Update frontend to parse real provider events, drive pause/resume UI, consume the token endpoint, and forward committed segments to the backend.
10. Update docs: contract inventory, decision log, task manager, and an ADR entry for the client-side streaming decision.

### Transitional Behavior
If we cannot confidently ship Path A in one pass, gate it behind a feature flag and keep the backend `audio.chunk` path as a fallback. The chunk-key fix must still land in the fallback path. The flag must default to the legacy path until end-to-end verification passes in `dev`.

### AWS / Infrastructure Notes
- Add the transcription token endpoint to the HTTP API (API Gateway + Lambda route) with Cognito auth.
- Add an EventBridge rule → finalization Lambda. Add a DLQ and retry policy. Wire IAM least-privilege.
- Continue to keep the ElevenLabs long-lived API key in Secrets Manager.
- Update CDK monitoring/alarms to cover finalization failures and token endpoint errors.

### Backend Notes
- Update WebSocket contracts in `contracts/websocket/session.yaml` and `events.yaml`.
- Update `SessionService` and `domain/session` for pause/resume transitions, and `session_repository` to persist new states.
- Add `ConsultationEvent` value object or reuse existing event publishing helpers.
- Add async-safe variants if needed under `ports/async_transcription_provider.py` and `ports/async_ai_pipeline.py` (these ports already exist; wire them here).
- Ensure `session.stop` and HTTP `session/end` both converge on the same `EventBridge` emission.
- Consider backpressure: do not enqueue multiple finalization events per consultation (idempotency key = `session_id`).

### Frontend Notes
- Add a `transcription` module to `app/src/api/` for the token endpoint.
- In `LiveConsultationPage.tsx`, open a second WebSocket to ElevenLabs and bridge its events into the existing transcript state.
- Render `recording`, `paused`, `processing`, `warning`, and `disconnected` states distinctly.
- Keep microphone permission handling explicit. Surface token acquisition failures clearly.
- Keep reconnect behavior tolerant to both the backend WebSocket and the provider WebSocket.

### Security Considerations
- The transcription token endpoint is an authorization boundary. Validate ownership and reject expired sessions.
- Token TTL ≤ the maximum consultation duration for the plan.
- Do not log the token value. Do not log the provider response bodies in full.

## 6. Deliverables

- Updated WebSocket contracts (pause/resume, provisional schemas, real transcript event clarification)
- `POST /v1/consultations/{id}/transcription-token` endpoint + BFF view
- Domain updates for `session.pause` / `session.resume`
- Async finalization worker Lambda wired through EventBridge + DLQ
- `session.stop` / HTTP `session/end` emit a domain event and return immediately
- Stub transcript event removed from every code path
- Chunk-key collision fix (or full retirement of the backend `audio.chunk` path)
- Frontend direct provider streaming + pause/resume UI + token flow
- Backend + frontend tests (contract, handler, adapter, use case, schema, PHI logging, UI rendering)
- Documentation updates: contract inventory, decision log (new DEC-nnn for client-side streaming), task manager, and ADR entry
- OI-015 and OI-016 resolved; provisional emitter explicitly deferred to Task 024

## 7. Acceptance Criteria

- [ ] `[stub transcript]` is not emitted or rendered anywhere in the product.
- [ ] Frontend receives and renders real live transcript updates during recording (from the provider stream).
- [ ] Pause and resume actions round-trip between frontend and backend state with audit events.
- [ ] `POST /v1/consultations/{id}/transcription-token` returns a short-lived, scoped token; unauthorized requests are rejected.
- [ ] `session.stop` / HTTP `session/end` return in constant time and emit an EventBridge event; no provider or pipeline calls are awaited inline.
- [ ] Finalization runs in a separate Lambda and completes successfully for normal and slow recordings; failures surface as session warnings and CloudWatch alarms.
- [ ] The S3 audio chunk key scheme produces unique keys across concurrent Lambda containers (or the backend chunk path is retired).
- [ ] `insight.provisional` and `autofill.candidate` contracts exist and are referenced from Task 024.
- [ ] PHI-safe logging tests cover realtime event handling, token issuance, and finalization.
- [ ] OI-015 and OI-016 are marked resolved in `tasks/@task-manager.md`.
- [ ] Documentation and ADR updates are committed.

## 8. Testing

### Required Tests
- Contract tests for updated `session.yaml` and `events.yaml` (pause/resume, provisional, stub removed).
- HTTP contract test for the transcription token endpoint.
- Backend handler tests proving `session.stop` does not call the provider or run the pipeline inline.
- Use case tests for pause/resume state transitions and rejection paths.
- Adapter tests for the short-lived token issuance.
- Finalization worker tests (success, retry, DLQ path, PHI-safe logs).
- Chunk-key uniqueness tests across simulated concurrent containers.
- Frontend tests for provider event parsing, pause/resume UI, token acquisition, and error states.
- PHI/PII logging regression tests.

### Manual Verification
Run the full flow in `dev`:
1. Log in, create a consultation.
2. Start a session; fetch token; confirm browser connects directly to ElevenLabs.
3. Stream at least 2 minutes of audio; observe live partials and committed segments.
4. Pause, resume, pause again, resume.
5. Stop the session; confirm the response returns quickly.
6. Watch EventBridge / Lambda logs for finalization.
7. Open review; confirm full transcript and AI artifacts are present and correct.

## 9. Risks and Edge Cases

### Risks
- Exposing ElevenLabs streaming to the browser could leak the long-lived key if the token adapter is wrong. Mitigation: token issuance tested; long-lived key never returned.
- Async finalization introduces eventual consistency; UI must reflect `in_processing` state correctly.
- Provider event shapes differ from our existing `transcript.partial` / `transcript.final` contracts. Mitigation: frontend maps provider shapes into the existing event contract; contract stays stable.

### Edge Cases
- Browser reconnects mid-session.
- Provider WebSocket disconnects while browser stays connected.
- Audio chunks arrive after a pause.
- Partial transcripts are revised by later committed segments.
- EventBridge event delivery is retried; finalization must be idempotent per `session_id`.
- Short recordings produce very few chunks; finalization must still succeed.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass (`make test`, `make lint`, `npm test` in `app/`).
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, alarms, and error handling were considered.
- [ ] Security and permissions were reviewed.
- [ ] Documentation, decision log, and task manager are updated.
- [ ] Task is ready for review or merge.
