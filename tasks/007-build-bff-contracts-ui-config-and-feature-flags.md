# Task 007: Build BFF Contracts, UI Config, And Feature Flags

## 1. Overview

### Objective
Implement the BFF layer that exposes stable frontend-ready APIs, serves backend-driven UI configuration, and enforces feature flags without pushing business logic into the frontend.

### Why This Matters
The technical specs make the BFF mandatory and the frontend intentionally dumb. The team needs a consistent BFF contract before the authenticated app can be built safely.

### Task Type
- Full Stack

### Priority
- High

## 2. Context

### Product Context
The physician experience depends on stable screen payloads, plan-aware capabilities, and configurable text, sections, and warnings that the backend can control.

### Technical Context
This task formalizes the contract between frontend and backend by shaping domain responses into screen-ready payloads and by centralizing configuration delivery.

### Related Systems
- Backend API
- Frontend app
- Authentication
- Storage

### Dependencies
- `005-implement-authentication-and-plan-access-control.md`
- `006-model-consultation-domain-persistence-and-audit.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/02-backend-architecture.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/03-plan-entitlements.md`

## 3. Scope

### In Scope
- Implement BFF endpoints for `GET /v1/me`, `POST /v1/consultations`, `GET /v1/consultations`, `GET /v1/consultations/{consultation_id}`, and `GET /v1/ui-config`.
- Define response schemas for screen payloads, feature flags, labels, helper text, warnings, section order, and action availability.
- Implement backend-side feature flag evaluation and delivery.
- Implement locale-aware config delivery for `pt-BR`.
- Centralize frontend-safe error payloads and loading contract expectations.

### Out of Scope
- Real-time audio streaming and transcript transport.
- AI generation workflow orchestration.
- Final review editing and export endpoints.

## 4. Requirements

### Functional Requirements
- The BFF must return frontend-ready payloads that minimize client-side data reshaping.
- The frontend must be able to render pages and sections based on backend-delivered configuration.
- Feature flags must support controlled rollout and rollback without requiring a frontend redeploy when practical.
- The BFF must attach action availability based on status, role, and plan.

### Non-Functional Requirements
- BFF responses must be stable, explicit, and versionable.
- Contract changes should be easy to trace and test.
- The BFF must shield the frontend from internal backend representation changes.

### Business Rules
- Frontend copy, warnings, and product content default to `pt-BR`.
- Plan-based access control must be enforced consistently.
- The frontend must not decide which insight types or review states are allowed.

### Technical Rules
- BFF is the frontend-facing API layer.
- Feature flag evaluation belongs in backend or BFF layers.
- Frontend must render backend-provided configuration whenever practical.

## 5. Implementation Notes

### Proposed Approach
Implement dedicated BFF view-model builders that consume backend services and configuration stores. Keep response composition explicit and centrally versioned.

### AWS / Infrastructure Notes
- Decide where active UI config versions live in DynamoDB and where larger config payloads live in S3.

### Backend Notes
- Add configuration retrieval services, view-model mappers, and feature flag resolvers.
- Keep domain services independent from UI shape concerns.

### Frontend Notes
- The React app should consume BFF payloads directly and avoid redefining field order or business logic.

## 6. Deliverables

The task should produce:
- BFF endpoints and response schemas
- UI configuration storage and delivery path
- Feature flag evaluation and exposure
- Contract documentation for frontend consumers

## 7. Acceptance Criteria

- [ ] The BFF exposes frontend-ready consultation, user, and UI config payloads.
- [ ] Feature flags and action availability are delivered from backend-controlled logic.
- [ ] UI configuration supports labels, helper copy, warnings, and section ordering.
- [ ] Frontend consumers do not need to implement core business or workflow rules locally.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for view-model builders and feature flag decisions
- Integration tests for BFF endpoint payloads

### Manual Verification
Call the BFF endpoints and confirm the payloads are screen-ready, locale-aware, and reflect status or plan changes without frontend-specific recomputation.

## 9. Risks and Edge Cases

### Risks
- Thinly specified contracts could leak domain complexity into the frontend.
- Scattered feature flag checks could become inconsistent.

### Edge Cases
- Missing UI config should fall back only to minimal technical defaults.
- Different plans may expose the same screen but with different actions available.
- A consultation payload may include partially generated artifacts that require specific warnings.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
