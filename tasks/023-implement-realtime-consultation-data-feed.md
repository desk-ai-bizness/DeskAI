# Task 023: Implement Realtime Consultation Data Feed

## 1. Overview

### Objective
Replace stub live transcript behavior with a real realtime consultation data feed and add backend-owned event contracts for transcript updates, pause/resume state, and provisional AI/autofill updates where available.

### Why This Matters
The consultation workspace is the core product experience. Doctors need live transcript and session state that reflect the actual consultation, not placeholder text. This task resolves the known stub transcript gap before the consultation workspace is redesigned.

### Task Type
- Full Stack

### Priority
- Critical

## 2. Context

### Product Context
During a consultation, the doctor should be able to see live transcript progress and, when technically available, provisional AI-generated field candidates. All live content must be clearly draft/provisional until the backend completes processing and the doctor reviews it.

### Technical Context
Task 008 added WebSocket session transport, Task 009 integrated the transcription provider, and Task 010 added the AI processing pipeline. OI-016 remains open because `audio.chunk` still sends a stub `transcript.partial` placeholder while actual transcription occurs later in batch finalization.

### Related Systems
- Backend API
- WebSocket API
- Transcription provider
- AI pipeline
- Frontend app
- Storage
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

## 3. Scope

### In Scope
- Remove the current `[stub transcript]` event path.
- Implement a real realtime transcript path, or an explicit provider-token/browser streaming path consistent with the serverless architecture.
- Add or update backend-owned WebSocket event contracts for live transcript updates.
- Add session pause/resume state events and controls at the contract/backend level.
- Add provisional AI/autofill candidate event contracts where technically available.
- Persist final transcript and AI artifacts exactly as the current review/finalization flow requires.
- Mark live transcript, insight, and autofill updates as draft/provisional until backend processing completes.
- Add PHI-safe logging and event schema tests.
- Update frontend WebSocket handling to consume the new event shapes.

### Out of Scope
- Redesigning the full consultation workspace; that belongs to Task 024.
- Changing final review, finalization, or export business rules.
- Adding automatic diagnoses, automatic prescriptions, or authoritative clinical suggestions.
- Adding post-consultation upload as a primary workflow.

## 4. Requirements

### Functional Requirements
- Frontend must receive real live transcript updates during a recording session.
- Pause/resume must be represented deliberately in backend/session state and WebSocket events.
- Live AI/autofill updates, if implemented, must be clearly provisional and tied to explicit transcript evidence or marked incomplete.
- Final persisted transcript and AI artifacts must remain compatible with the review/finalization/export pipeline.
- No placeholder `[stub transcript]` events may remain.

### Non-Functional Requirements
- The realtime path must be resilient to disconnects and provider failures.
- Logs must not contain raw audio, raw transcript, CPF, or unnecessary patient-identifiable data.
- Event contracts must be versioned or documented clearly enough to prevent frontend/backend drift.
- Provider failures must surface as actionable session warnings without silently hiding failures.

### Business Rules
- The system reports what was said; it must never interpret what it means as a clinical decision.
- The system must not fabricate symptoms, diagnoses, medications, allergies, findings, plans, or follow-up instructions.
- Insights are review flags, not conclusions.
- Clinical attention flags must never be presented as diagnoses.
- AI-generated output is not final until physician review and explicit finalization.

### Technical Rules
- Keep provider-specific logic in adapters, not the domain core.
- Keep WebSocket event shapes in shared contracts.
- Follow strict TDD for event schemas, session state, provider integration behavior, and frontend event rendering.
- Prefer event-driven/asynchronous handling where it improves resilience and Lambda timeout safety.

## 5. Implementation Notes

### Proposed Approach
First write failing tests proving stub transcript events are not emitted and real event schemas are enforced. Then choose the lowest-risk realtime provider path compatible with ElevenLabs Scribe v2 Realtime and the existing API Gateway WebSocket setup. Keep final transcript persistence and AI artifact generation aligned with the existing batch/finalization pipeline.

### AWS / Infrastructure Notes
- Review WebSocket API, Lambda timeout, IAM permissions, and connection management needs.
- If provider direct browser streaming is used, add a short-lived token endpoint with least-privilege scope and no long-lived secret exposure.
- If backend streaming is used, ensure Lambda runtime limits and connection lifecycle are acceptable or introduce an event-driven worker path.

### Backend Notes
- Update WebSocket contracts in `contracts/websocket`.
- Add session pause/resume use cases or state transitions if needed.
- Ensure `session.stop` and HTTP `session/end` continue to converge on the same finalization behavior.
- Consider whether OI-015 should be addressed together if realtime finalization still risks Lambda timeout.

### Frontend Notes
- Update WebSocket parser/types to handle real transcript events and session pause/resume states.
- Render provisional transcript/AI updates distinctly from finalized review data.
- Keep reconnect behavior and microphone permission handling explicit.

## 6. Deliverables

The task should produce:
- Updated WebSocket contracts
- Backend realtime transcript integration or provider-token streaming path
- Pause/resume event/state support
- Frontend event handling updates
- Updated tests for schemas, handlers, adapters, and frontend rendering
- Documentation updates and OI-016 resolution notes

## 7. Acceptance Criteria

- [ ] No `[stub transcript]` event is emitted or rendered.
- [ ] Frontend receives and renders real live transcript updates during recording.
- [ ] Pause/resume is represented deliberately in backend state/events and frontend UI state.
- [ ] Provisional AI/autofill updates, if emitted, are marked draft/incomplete and evidence-aware.
- [ ] Final transcript and AI artifacts remain compatible with review/finalization/export.
- [ ] PHI-safe logging tests cover realtime event handling.
- [ ] OI-016 is updated or resolved in the task manager.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- WebSocket schema tests for transcript, pause/resume, warning, and provisional update events.
- Backend handler tests proving stub transcript events are removed.
- Provider adapter tests for realtime transcript behavior or token issuance.
- Session use case tests for pause/resume transitions.
- Frontend tests for rendering live transcript events and session state.
- PHI/PII logging tests for audio/transcript/CPF safety.

### Manual Verification
Start a local or dev consultation session, stream audio, confirm live transcript updates appear without stub content, pause and resume the session, end the session, and verify final processing still produces reviewable artifacts.

## 9. Risks and Edge Cases

### Risks
- Provider realtime behavior may require a different connection lifecycle than API Gateway WebSocket supports directly.
- Long-running backend streaming could conflict with Lambda timeout limits.
- Provisional AI/autofill could be misread as final if visual treatment is weak.

### Edge Cases
- Provider connection drops while browser WebSocket remains connected.
- Browser reconnects after pause.
- Audio chunks arrive out of order or after session end.
- Transcript partials are revised by later final transcript segments.
- Insufficient audio produces incomplete final artifacts.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
