# Task 002: Design System Architecture And Project Structure

## 1. Overview

### Objective
Define the implementation architecture, domain boundaries, repository layout, and technical contracts that the team will use to build the MVP consistently.

### Why This Matters
The technical specs define the target architecture, but the repo still lacks concrete module boundaries, folder structure, API contracts, and ownership lines. This task turns the high-level architecture into a buildable technical blueprint.

### Task Type
- Full Stack

### Priority
- Critical

## 2. Context

### Product Context
The MVP combines a public website, an authenticated React app, a BFF, a Python core backend, and AWS serverless infrastructure. The architecture must support real-time consultations, post-session AI processing, physician review, and finalization.

### Technical Context
This task converts the technical specs into actual system shape: repository directories, service boundaries, data contracts, interface boundaries, and summarized ADR updates.

### Related Systems
- AWS
- Backend API
- Frontend app
- Authentication
- Storage
- CI/CD

### Dependencies
- `001-refine-mvp-requirements-and-delivery-decisions.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/03-plan-entitlements.md`
- `docs/requirements/04-failure-behavior-matrix.md`
- `docs/requirements/05-decision-log.md`

## 3. Scope

### In Scope
- Define the top-level project structure for public website, authenticated app, BFF, core backend, shared contracts, and CDK.
- Define Hexagonal Architecture boundaries for the Python backend.
- Define BFF responsibilities and view-model ownership.
- Define contract locations for API schemas, WebSocket message schemas, UI config schemas, and feature flag schemas.
- Define environment configuration strategy for `dev` and `prod`.
- Add concise ADR entries when implementation-level architecture choices become fixed.

### Out of Scope
- Full implementation of application logic.
- Deploying cloud resources.
- Building production UI.

## 4. Requirements

### Functional Requirements
- The architecture definition must describe how the frontend, BFF, backend core, and infrastructure interact.
- The project structure must support backend-driven UI configuration and feature flags.
- The structure must support the required backend modules: `auth`, `consultations`, `sessions`, `transcription`, `ai_pipeline`, `artifacts`, `review`, `exports`, `audit`, `config`, and `shared`.
- The architecture must define where prompts, schemas, adapters, domain models, and shared contracts live.

### Non-Functional Requirements
- The structure must favor replaceability, testability, and low-coupling design.
- Folder naming and ownership should minimize accidental mixing of domain, transport, and infrastructure logic.
- The architecture must stay simple enough for a small team to navigate quickly.

### Business Rules
- The frontend must not own business rules or workflow rules.
- AI-generated content remains draft content until physician approval.
- The product must preserve traceability between source conversation content and generated artifacts.

### Technical Rules
- Use Hexagonal Architecture in the backend.
- Keep the BFF mandatory and frontend-focused.
- Use AWS serverless-first assumptions throughout the design.
- Keep code and documentation in English, while user-facing content is `pt-BR`.

## 5. Implementation Notes

### Proposed Approach
Produce an architecture package with a directory map, dependency rules, module responsibilities, request/response contract inventory, data ownership diagram, and a short bootstrap checklist for implementation tasks.

### AWS / Infrastructure Notes
- Define which CDK stacks or constructs will own auth, API ingress, storage, orchestration, observability, and frontend hosting.

### Backend Notes
- Define ports and adapters for storage, provider integrations, AI calls, and event publishing.
- Define where shared schema validation lives so BFF and backend contracts remain aligned.

### Frontend Notes
- Define separate directories for static marketing pages and the React app.
- Define how the frontend consumes UI config without embedding workflow logic.

## 6. Deliverables

The task should produce:
- Architecture and repository layout documentation
- A contract inventory for HTTP, WebSocket, UI config, and feature flags
- Updated ADR summaries when needed
- A folder structure decision ready for repository bootstrap

## 7. Acceptance Criteria

- [ ] The team has a documented top-level folder structure for website, app, BFF, backend, shared contracts, and CDK.
- [ ] Backend module boundaries and adapter boundaries are defined explicitly.
- [ ] API and WebSocket contract ownership is documented.
- [ ] The architecture definition explains how backend-driven UI configuration and feature flags flow to the frontend.
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Architecture review against the technical specs and requirements baseline.

### Manual Verification
Confirm a developer can scaffold the repository from the architecture document without needing to infer major directory or ownership decisions.

## 9. Risks and Edge Cases

### Risks
- Poor boundary definition could leak AWS concerns into domain logic.
- Weak contract ownership could lead to duplicated schemas and frontend reshaping logic.
- Overengineering the structure could slow the MVP.

### Edge Cases
- Some configuration may fit DynamoDB first and later move to S3.
- The first provider adapter may need to coexist with future providers.
- Export flows may require different transport or storage concerns than review flows.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
