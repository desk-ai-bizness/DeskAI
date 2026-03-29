# Task 008: Implement Real-Time Consultation Session Transport

## 1. Overview

### Objective
Implement the real-time consultation session lifecycle, WebSocket transport, and audio-ingestion path that powers the MVP’s primary live-consultation workflow.

### Why This Matters
The MVP is explicitly real-time-first. Without session transport, audio chunk ingestion, and transcript event delivery, the core physician workflow cannot operate.

### Task Type
- Backend

### Priority
- Critical

## 2. Context

### Product Context
The physician starts a consultation, streams audio during the encounter, receives transcript updates, and ends the session so the downstream processing pipeline can begin.

### Technical Context
This task connects the React app, WebSocket API, BFF session endpoints, backend session services, and later provider integrations.

### Related Systems
- AWS
- Backend API
- Frontend app
- Observability

### Dependencies
- `006-model-consultation-domain-persistence-and-audit.md`
- `007-build-bff-contracts-ui-config-and-feature-flags.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/02-backend-architecture.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/04-failure-behavior-matrix.md`
- `docs/requirements/05-decision-log.md`

## 3. Scope

### In Scope
- Implement `POST /v1/consultations/{consultation_id}/session/start` and `POST /v1/consultations/{consultation_id}/session/end`.
- Implement WebSocket routes for `$connect`, `$disconnect`, `session.init`, `audio.chunk`, `session.stop`, and `client.ping`.
- Implement session lifecycle management and connection binding to consultation context.
- Validate audio chunk ownership, ordering assumptions, and session validity.
- Emit session and transcript-related events needed by the frontend.

### Out of Scope
- Provider-specific transcript generation logic.
- AI generation orchestration.
- Final review editing flows.

## 4. Requirements

### Functional Requirements
- The system must allow an authenticated physician to start and end a live consultation session.
- Audio chunks must only be accepted for valid active sessions tied to the correct consultation and clinic context.
- The frontend must receive session and transcript update events through a stable real-time channel.
- When a session ends, the backend must transition the consultation into processing and trigger downstream work safely.

### Non-Functional Requirements
- The transport must handle disconnects, retries, and duplicate events deliberately.
- Session operations should be idempotent where reasonable.
- Logging must include enough context to diagnose failures without exposing raw audio content.

### Business Rules
- The primary MVP workflow is live consultation streaming.
- The consultation is processed as a single encounter tied to a specific patient and physician.
- If processing fails or remains incomplete, the consultation must not be treated as finalized.

### Technical Rules
- Use API Gateway WebSocket API for real-time transport.
- Use backend-owned session lifecycle logic.
- Use bounded retries only for transient failures.

## 5. Implementation Notes

### Proposed Approach
Create a session service that owns active-session validation, connection state, and event emission. Keep provider-specific audio forwarding behind an adapter boundary so the session layer does not depend on one transcription vendor.

### AWS / Infrastructure Notes
- Configure WebSocket route integrations, permissions, and logging.
- Use queues or async fan-out where needed to avoid blocking the live path.

### Backend Notes
- Validate consultation status before allowing session start.
- Record audit or operational events for start, stop, disconnect, and critical failures.

### Frontend Notes
- The frontend should receive explicit connection state and actionable errors, not infer them from low-level socket behavior.

## 6. Deliverables

The task should produce:
- Session start and end endpoints
- WebSocket route handlers
- Real-time session service
- Operational event and error handling logic
- Documentation for the live session contract

## 7. Acceptance Criteria

- [ ] Authenticated users can start and end consultation sessions through supported APIs.
- [ ] Audio chunks are accepted only for valid active sessions.
- [ ] WebSocket events provide stable session and transcript update delivery.
- [ ] Session end transitions the consultation into backend processing safely.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for session validation and state handling
- Integration tests for HTTP and WebSocket session flows

### Manual Verification
Start a consultation, open a session, stream test audio chunks, observe connection and transcript event flow, then end the session and confirm processing begins.

## 9. Risks and Edge Cases

### Risks
- Weak session validation could allow cross-consultation data leakage.
- Blocking work in the live path could harm responsiveness.

### Edge Cases
- The browser disconnects and reconnects mid-consultation.
- Duplicate audio chunks arrive.
- A stop request arrives after the session has already been closed.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
