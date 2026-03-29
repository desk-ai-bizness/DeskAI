# Task 006: Model Consultation Domain, Persistence, And Audit

## 1. Overview

### Objective
Implement the core consultation domain model, DynamoDB and S3 persistence patterns, status management, and audit foundations required for the MVP workflow.

### Why This Matters
The consultation domain is the backbone of the product. Every session, transcript, artifact, review action, and finalization event depends on a consistent domain model and storage strategy.

### Task Type
- Backend

### Priority
- Critical

## 2. Context

### Product Context
Each consultation belongs to one physician, one patient, one clinic context, and one specialty. It moves through defined business states and cannot be finalized before physician review.

### Technical Context
The technical specs require a single-table DynamoDB design, S3 artifact storage, auditable state transitions, and a clear distinction between metadata and large artifacts.

### Related Systems
- Backend API
- Database
- Storage
- Observability

### Dependencies
- `001-refine-mvp-requirements-and-delivery-decisions.md`
- `004-provision-aws-foundation-with-cdk.md`
- `005-implement-authentication-and-plan-access-control.md`

## 3. Scope

### In Scope
- Define and implement core entities for clinic, doctor, patient reference, consultation, session metadata, artifacts, review state, and audit events.
- Implement DynamoDB access patterns for consultation lookup, doctor consultation listing, status lookup, and artifact references.
- Implement S3 key strategies for audio, transcripts, AI outputs, and exports.
- Implement consultation status transition rules and persistence.
- Implement audit event creation for critical state changes and user actions.

### Out of Scope
- Real-time streaming transport implementation.
- Provider-specific transcription logic.
- AI generation logic.

## 4. Requirements

### Functional Requirements
- The system must create and retrieve consultations with stable identifiers and clinic ownership.
- The system must persist consultation state transitions in a way that supports list, detail, review, and finalization flows.
- The system must store S3 object references for large artifacts instead of storing large blobs in DynamoDB.
- The system must record attributable audit events for edits and final approval actions.

### Non-Functional Requirements
- Data access patterns must support the MVP without requiring a relational database.
- Domain services must remain independent from DynamoDB and S3 implementation details where practical.
- Storage interactions should be structured for idempotent async workflows.

### Business Rules
- Supported consultation states are `started`, `recording`, `in processing`, `processing failed`, `draft generated`, `under physician review`, and `finalized`. See `docs/requirements/02-consultation-lifecycle.md` for the complete state machine, transitions, and guard conditions.
- A consultation cannot be finalized before physician review.
- The final confirmed version is the only version considered complete for business purposes.
- Logs and operational records must avoid unnecessary exposure of patient-identifiable information.

### Technical Rules
- Use DynamoDB + S3, not PostgreSQL.
- Prefer the defined single-table design and S3 artifact layout patterns.
- Preserve traceability between generated artifacts and the consultation they belong to.

## 5. Implementation Notes

### Proposed Approach
Implement domain models and repositories that expose consultation use cases while hiding storage specifics behind ports and adapters. Use consistent keys, timestamps, and status transition guards.

### AWS / Infrastructure Notes
- Ensure PITR and bucket configuration from Task 004 are used correctly.

### Backend Notes
- Implement application services for create consultation, update status, fetch consultation detail, list consultations, and append audit events.
- Define artifact metadata structures for transcript, AI outputs, and exports.

### Frontend Notes
- BFF and frontend should receive backend-shaped identifiers and statuses instead of inferring state from raw data.

## 6. Deliverables

The task should produce:
- Consultation domain models and services
- DynamoDB repositories and access patterns
- S3 artifact pointer strategy in code
- Audit event model and persistence
- Documentation for status and storage behavior

## 7. Acceptance Criteria

- [ ] Consultations can be created, fetched, and listed with clinic and doctor context.
- [ ] Status transitions are validated against business rules.
- [ ] Artifact metadata and audit events are persisted with consistent identifiers.
- [ ] The domain model cleanly separates metadata from large artifacts.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for status transitions and domain rules
- Integration tests for DynamoDB access patterns and audit persistence

### Manual Verification
Create a consultation, move it through valid states, confirm invalid transitions are rejected, and verify artifact pointers and audit records are stored as expected.

## 9. Risks and Edge Cases

### Risks
- Incorrect access patterns could make listing or status queries expensive or awkward.
- Weak status guards could allow invalid finalization behavior.

### Edge Cases
- A consultation is created but no session ever starts.
- Processing fails after audio is stored but before drafts are generated.
- Partial artifacts exist for a consultation that never reaches finalization.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
