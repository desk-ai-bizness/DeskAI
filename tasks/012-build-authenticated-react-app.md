# Task 012: Build Authenticated React App

## 1. Overview

### Objective
Build the authenticated physician-facing React application for sign-in, consultation creation, live consultation handling, review, editing, and finalization.

### Why This Matters
The authenticated web app is where physicians experience the product. It must present the core workflow clearly, keep the user in control, and remain faithful to the backend-driven architecture.

### Task Type
- Frontend

### Priority
- Critical

## 2. Context

### Product Context
The physician needs a practical product flow: log in, create a consultation, capture microphone audio, monitor transcript progress, review AI outputs, edit them, and finalize the note.

### Technical Context
The React app consumes BFF APIs and real-time session endpoints. It must remain thin, using backend-provided configuration and business decisions rather than embedding product rules locally.

### Related Systems
- Frontend app
- Backend API
- Authentication
- Observability

### Dependencies
- `005-implement-authentication-and-plan-access-control.md`
- `007-build-bff-contracts-ui-config-and-feature-flags.md`
- `008-implement-realtime-consultation-session-transport.md`
- `011-implement-review-finalization-and-export-workflows.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/03-plan-entitlements.md`

## 3. Scope

### In Scope
- Implement sign-in, session restoration, and sign-out flows.
- Implement consultation list and consultation creation UI.
- Implement live consultation screen with microphone permission handling, connection state, and transcript updates.
- Implement review screen for transcript, draft history, summary, insights, evidence, edits, and finalization.
- Implement plan-aware and status-aware UI based on backend payloads.
- Implement loading, empty, success, and failure states across core screens.

### Out of Scope
- Public marketing website.
- Client-side ownership of business logic, review rules, or feature flags.
- Native mobile applications.

## 4. Requirements

### Functional Requirements
- The app must support the full MVP workflow for authenticated physicians.
- UI text inside the product must default to `pt-BR`.
- The app must clearly indicate that AI-generated content is draft content subject to medical review.
- The app must allow physicians to edit generated outputs and explicitly confirm finalization.
- The app must render backend-provided UI configuration and action availability.

### Non-Functional Requirements
- The UI must handle real-time connection interruptions gracefully.
- Accessibility, responsiveness, and basic performance must be considered from the start.
- Sensitive data must be handled carefully in browser storage and logs.

### Business Rules
- The frontend must never present AI outputs as final before physician confirmation.
- Clinical attention flags must appear as reviewable observations, not diagnoses.
- The app must stay within the MVP scope of one specialty per consultation and no social login.

### Technical Rules
- Use React + TypeScript + Vite.
- Keep the frontend intentionally dumb.
- Use BFF-shaped data and backend-provided configuration whenever practical.

## 5. Implementation Notes

### Proposed Approach
Build a route-based React application with clear page-level states and thin API clients. Centralize transport, auth session handling, and UI config consumption, but keep domain decisions on the server.

### AWS / Infrastructure Notes
- Ensure the app is compatible with the CloudFront hosting and API origin setup defined earlier.

### Backend Notes
- Frontend behavior should depend on action availability and payload state from the BFF rather than raw business-rule logic.

### Frontend Notes
- Include microphone permission prompts, connection warnings, retry affordances, empty states, and explicit review banners.
- Keep only minimal fallback strings for technical failure states that cannot be loaded from the backend.

## 6. Deliverables

The task should produce:
- Authenticated React app screens and routes
- API and WebSocket integration layer
- Real-time consultation UI
- Review and finalization UI
- Frontend documentation

## 7. Acceptance Criteria

- [ ] Physicians can complete the MVP workflow in the authenticated app from sign-in to finalization.
- [ ] Product-facing UI content is presented in `pt-BR`.
- [ ] The app renders backend-driven configuration, statuses, and action availability.
- [ ] The UI clearly distinguishes draft content from finalized records.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Component and integration tests for major screens and states
- End-to-end tests for the primary physician workflow where practical

### Manual Verification
Use the app as a physician, start a consultation, review live transcript updates, edit generated outputs, finalize the record, and verify error handling around disconnects and incomplete generation.

## 9. Risks and Edge Cases

### Risks
- Frontend shortcuts could accidentally reintroduce business logic into the client.
- Weak failure handling could make the live flow feel unreliable.

### Edge Cases
- Microphone access is denied.
- A consultation is in processing and review data is not ready yet.
- Some outputs are incomplete and need explicit warning banners.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
