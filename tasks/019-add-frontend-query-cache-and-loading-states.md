# Task 019: Add Frontend Query Cache And Loading States

## 1. Overview

### Objective
Add a frontend request caching and async-state layer, preferably TanStack Query, and use it to improve API loading, refetching, mutation, and error handling behavior in the authenticated React app.

### Why This Matters
The functional app currently manages request state manually in page components. A query cache will reduce duplicated loading/error logic, improve perceived performance, and make button and section loaders more consistent.

### Task Type
- Frontend

### Priority
- Medium

## 2. Context

### Product Context
Physicians need responsive feedback while loading consultations, creating records, starting sessions, reviewing AI output, finalizing notes, and exporting PDFs. Loading states should be clear without blocking unrelated reading or review work.

### Technical Context
The app has a small custom API client and page-level fetch/mutation state. The design system will include loader and button loading primitives that can be connected to request states.

### Related Systems
- Frontend app
- Backend API
- Authentication

### Dependencies
- `012-build-authenticated-react-app.md`
- `017-create-authenticated-app-design-system.md`
- `018-apply-authenticated-app-facelift.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/02-consultation-lifecycle.md`

## 3. Scope

### In Scope
- Add TanStack Query or a similarly lightweight query cache library if implementation confirms it is the best fit.
- Wrap the app with a query client provider.
- Convert consultation list/detail/review/user-profile fetches to query hooks where appropriate.
- Convert create consultation, start/end session, update review, finalize, and export actions to mutation hooks where appropriate.
- Use query invalidation or cache updates after mutations.
- Connect query and mutation state to design-system loaders, button loading states, empty states, and error messages.
- Tune cache stale times carefully so clinical documentation data does not feel stale or misleading.
- Update tests and documentation for the new request-state approach.

### Out of Scope
- Offline-first behavior.
- Persisting query cache to storage.
- Caching raw audio, transcripts, or sensitive consultation payloads outside memory.
- Changing backend API response shapes.
- Adding complex global state management unrelated to server state.

## 4. Requirements

### Functional Requirements
- The app must show consistent loading states for page data and action buttons.
- Mutations must invalidate or update affected cached data.
- Authentication changes must clear sensitive cached server state on sign-out.
- Request errors must remain visible and actionable.
- Live WebSocket state must remain separate from HTTP query caching.

### Non-Functional Requirements
- Cached data must stay in memory only unless an explicit security review approves persistence.
- The cache must not mask failed writes, finalization failures, or stale consultation state.
- The implementation must reduce duplicated manual fetch state where practical.
- Bundle size impact from any new dependency must be acceptable for the MVP.

### Business Rules
- A finalized consultation is immutable and locked from further edits.
- Only finalized consultations may be exported.
- If an output cannot be produced reliably, the UI must show it as incomplete or pending review instead of inventing content.
- The frontend must not own business or workflow rules.

### Technical Rules
- Use React + TypeScript + Vite.
- Keep the existing API client as the transport boundary unless a narrower wrapper is needed for query hooks.
- Do not persist sensitive query data to browser storage.
- If adding a durable frontend data-fetching dependency, document the decision as a concise ADR entry in `docs/mvp-technical-specs.md`.

## 5. Implementation Notes

### Proposed Approach
Introduce a query client near `main.tsx`, then add small query and mutation hooks around existing endpoint functions. Convert pages incrementally and keep API endpoint definitions centralized.

### AWS / Infrastructure Notes
- No AWS infrastructure changes are expected.

### Backend Notes
- No backend changes are expected.

### Frontend Notes
- Prefer conservative stale times for consultation and review data.
- Clear the query client when the user signs out or the session becomes invalid.
- Avoid broad global retries for mutations that are not safely idempotent.
- For session and recording flows, keep real-time connection state explicit rather than hiding it behind HTTP query state.

## 6. Deliverables

The task should produce:
- Query cache dependency and provider setup
- Query/mutation hooks or equivalent request-state abstraction
- Updated pages using cache-backed loading/error/mutation state
- Updated tests
- Documentation and ADR updates if a new dependency is introduced

## 7. Acceptance Criteria

- [ ] The app uses a query cache/request-state layer for suitable HTTP API reads and writes.
- [ ] Loading, error, success, and mutation states are consistent with the design system.
- [ ] Sensitive cached data is cleared on sign-out and is not persisted to browser storage.
- [ ] Mutations invalidate or update affected data correctly.
- [ ] Live WebSocket state remains explicit and reliable.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Unit/component tests for query-backed page loading and error states.
- Mutation tests for create consultation, review update, finalization, and export loading states where practical.
- Auth/sign-out test that verifies cached sensitive data is cleared or no longer rendered.
- Existing frontend tests must remain green.

### Manual Verification
Run the app locally, navigate between consultation list, live session, and review pages, perform mutations, and confirm loading indicators, cache refreshes, errors, and sign-out behavior are correct.

## 9. Risks and Edge Cases

### Risks
- Aggressive caching could show stale review or finalized state.
- Automatic retries could duplicate non-idempotent actions.
- Persisted cache would increase sensitive-data exposure risk.

### Edge Cases
- Token expires while cached data exists.
- Finalization succeeds but cache still shows editable draft state.
- Export request fails after finalization.
- Consultation list is refetched while a new consultation is being created.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
