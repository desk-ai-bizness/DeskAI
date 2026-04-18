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

- [x] Physicians can complete the MVP workflow in the authenticated app from sign-in to finalization.
- [x] Product-facing UI content is presented in `pt-BR`.
- [x] The app renders backend-driven configuration, statuses, and action availability.
- [x] The UI clearly distinguishes draft content from finalized records.
- [x] Relevant tests are added or updated
- [x] Documentation is updated if behavior or setup changed

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

- [x] Implementation is complete
- [x] Acceptance criteria are met
- [x] Tests pass
- [x] No obvious regressions were introduced
- [x] Logs, metrics, and error handling were considered
- [x] Security and permissions were reviewed if relevant
- [x] Task is ready for review or merge

## 11. Implementation Summary (2026-04-11)

- Implemented authenticated route-based React app with sign-in, session restoration, and sign-out.
- Implemented consultation list and creation flow with patient helper creation form.
- Implemented live consultation screen with microphone permission handling, WebSocket connection state, transcript partial rendering, and reconnect controls.
- Implemented review/edit/finalization/export flow with explicit physician confirmation and draft warning banners.
- Implemented backend-driven UI rendering for labels, status labels, review section order, insight category labels, and action availability.
- Added frontend test stack (`vitest` + Testing Library) and component/integration tests covering auth session handling, API client behavior, consultation list states, live microphone denial handling, and review rendering.
- Updated app documentation (`app/README.md`) with routes, environment variables, and commands.

## 12. Post-Completion Fixes (2026-04-11)

- Fixed local login CORS failures by adding Vite dev proxy support (`/api` → AWS dev API target) and documenting local env setup.
- Updated local app env defaults to use proxy-first API base URL for localhost development.
- Updated HTTP API Gateway CORS allowed headers to include `X-Contract-Version` and added synthesis test coverage for this header.
- Refined login page UX/UI for production-readiness: upgraded layout and visual hierarchy, improved page copy, and removed developer-facing authentication note text.
- Applied advanced login motion and interaction polish: ambient animated background layers, staggered content entrance, improved hover/focus transitions, animated CTA button, and reduced-motion accessibility fallback.
- Fixed desktop layout composition by restoring side-by-side block rendering for login and applying the same responsive two-column pattern to consultations, live session, and review screens.
