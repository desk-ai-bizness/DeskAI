# Task 001: Refine MVP Requirements And Delivery Decisions

## 1. Overview

### Objective
Turn the current business rules and technical specs into an implementation-ready requirements baseline by resolving ambiguities, defining explicit behavior, and documenting the decisions the team needs before coding begins.

### Why This Matters
The current source files define clear boundaries, but they still leave operational and product details open. The team needs a single requirements baseline so later architecture, IaC, backend, frontend, and integration work does not rely on assumptions.

### Task Type
- Full Stack

### Priority
- Critical

## 2. Context

### Product Context
This task prepares the MVP for delivery of the main physician workflow: sign in, create a consultation, stream audio in real time, review AI-generated outputs, edit them, and explicitly finalize the record.

### Technical Context
The repo currently contains only planning documents and task templates. No delivery structure, architecture package layout, or implementation contracts exist yet.

### Related Systems
- Backend API
- Frontend app
- Authentication
- Storage
- Observability

### Dependencies
- `docs/mvp-business-rules.md`
- `docs/mvp-technical-specs.md`
- `docs/ai-context-rules.md`

## 3. Scope

### In Scope
- Create a requirements traceability matrix mapping business rules to features, APIs, data, and UI flows.
- Define the complete MVP consultation lifecycle and allowed state transitions.
- Define the minimum fields required to create, process, review, and finalize a consultation.
- Clarify plan-aware behavior for `free_trial`, `plus`, and `pro`, even if some plans initially share the same permissions.
- Define expected failure behavior for transcription, AI generation, export, and finalization paths.
- Define clinic, doctor, patient, and consultation ownership rules needed for authorization and audit.
- Record unresolved decisions that need product or technical approval.

### Out of Scope
- Writing production code.
- Provisioning infrastructure.
- Building user interfaces.
- Deep pricing strategy or non-MVP commercial packaging.

## 4. Requirements

### Functional Requirements
- The team must have a documented end-to-end workflow for live consultation processing.
- The requirements baseline must define the required outputs for a successful consultation: raw transcript, draft structured medical history, summary, insights, and evidence excerpts.
- The baseline must define incomplete, failed, and retryable states for all critical steps.
- The baseline must define who can review, edit, and finalize a consultation.
- The baseline must define what data must remain editable, immutable, or auditable.

### Non-Functional Requirements
- Requirements must be explicit enough to support backend-first implementation without frontend-owned rules.
- Definitions must stay aligned with a serverless AWS architecture and a small-team MVP scope.
- Decisions must remain reversible where the product intentionally has not committed yet.

### Business Rules
- The MVP is a documentation support tool only and must never be defined as a clinical decision-maker.
- All user-facing product behavior defaults to `pt-BR`.
- AI-generated content must remain reviewable and cannot be considered final until physician confirmation.
- The product must support only email and password login in the MVP.
- Each consultation belongs to one physician, one patient, one clinic context, and one specialty.
- The product must not invent clinical facts when data is missing or unclear.

### Technical Rules
- The frontend must remain intentionally dumb and backend-driven.
- The BFF is mandatory and owns frontend-shaped contracts.
- The backend follows Hexagonal Architecture principles.
- Only `dev` and `prod` environments exist.
- AWS CDK is mandatory for infrastructure changes.

## 5. Implementation Notes

### Proposed Approach
Create a requirements package in `docs/` that includes a rule-to-feature matrix, a consultation state machine, a role and ownership matrix, a failure-mode matrix, and a short decision log for unresolved items. Update the source docs only where clarification becomes canonical.

### AWS / Infrastructure Notes
- Confirm which requirements affect environment isolation, retention, encryption, and audit scope before IaC work starts.

### Backend Notes
- Define the minimum consultation, review, artifact, and audit entities needed by later backend tasks.
- Define idempotency expectations for async processing and finalization flows.

### Frontend Notes
- Define the screens and major states the frontend must render, but keep workflow rules in backend-facing requirements.

## 6. Deliverables

The task should produce:
- A requirements traceability document
- A consultation lifecycle and state transition definition
- A plan entitlement and authorization decision record
- A failure behavior matrix
- Updated canonical docs where necessary

## 7. Acceptance Criteria

- [ ] Every major business rule is mapped to at least one concrete system behavior or task area.
- [ ] The consultation lifecycle defines allowed transitions for `started`, `in processing`, `draft generated`, `under physician review`, and `finalized`.
- [ ] The team has a documented answer or open decision for plan entitlements, clinic retention behavior, export scope, and provider selection criteria.
- [ ] Requirements clearly distinguish draft, reviewable, and finalized data.
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Review the requirements package against the business rules and technical specs for completeness.

### Manual Verification
Confirm a teammate can read the requirements package and describe the full MVP flow, failure states, and review/finalization rules without consulting older notes.

## 9. Risks and Edge Cases

### Risks
- Ambiguous plan behavior could cause authorization rework later.
- Missing failure definitions could create inconsistent backend and frontend behavior.
- Unclear retention or export rules could affect storage design and audit scope.

### Edge Cases
- A consultation ends without enough audio to generate reliable outputs.
- AI generation returns only partial artifacts.
- A physician edits some outputs but not others before finalization.
- A clinic deletes audio but must retain the finalized note.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
