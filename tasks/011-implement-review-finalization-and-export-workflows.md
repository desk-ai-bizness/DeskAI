# Task 011: Implement Review, Finalization, And Export Workflows

## 1. Overview

### Objective
Implement physician review, editing, explicit final approval, audit attribution, and export flows for consultation outputs.

### Why This Matters
The MVP’s trust model depends on physician review. AI-generated content is useful only if the physician can inspect it, edit it, and explicitly confirm the final record.

### Task Type
- Backend

### Priority
- Critical

## 2. Context

### Product Context
After AI processing finishes, the physician must review the transcript-derived outputs, make edits, and confirm the final consultation record before it is considered complete.

### Technical Context
This task completes the business workflow on top of consultation data, generated artifacts, and audit foundations. It also adds export capability for downstream use.

### Related Systems
- Backend API
- Storage
- Authentication
- Observability

### Dependencies
- `007-build-bff-contracts-ui-config-and-feature-flags.md`
- `010-build-ai-processing-pipeline-and-artifacts.md`

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
- Implement `GET /v1/consultations/{consultation_id}/review`.
- Implement `PUT /v1/consultations/{consultation_id}/review`.
- Implement `POST /v1/consultations/{consultation_id}/finalize`.
- Implement `POST /v1/consultations/{consultation_id}/export`.
- Persist physician edits, review metadata, final confirmation, and export records.
- Record audit events for edits, approvals, and exports.

### Out of Scope
- Deep EHR integration.
- Electronic prescribing or diagnostic outputs.
- Complex collaborative multi-review workflows.

## 4. Requirements

### Functional Requirements
- Physicians must be able to retrieve a review payload containing transcript-derived outputs and evidence.
- Physicians must be able to edit the draft medical history, summary, and insights before finalization.
- Finalization must require explicit physician confirmation and associate the action with the responsible physician.
- Export generation must use the finalized content, not an unreviewed draft.

### Non-Functional Requirements
- Review and finalization flows must be auditable and attributable.
- Finalization must be idempotent or safely reject duplicates.
- Error handling must clearly distinguish review-state conflicts from technical failures.

### Business Rules
- No AI-generated output is final until reviewed by the physician.
- The final signed or confirmed version is the only version considered complete.
- Clinical attention flags remain review flags, not diagnoses.
- If processing failed or remains incomplete, the consultation must not be treated as finalized.

### Technical Rules
- Keep finalization logic in backend services, not the frontend.
- Preserve traceability between edited content, original generated artifacts, and final confirmed output.
- Store large export artifacts in S3 with metadata in DynamoDB.

## 5. Implementation Notes

### Proposed Approach
Implement a review aggregate or service that merges generated artifacts, user edits, finalization status, and audit behavior. Keep final confirmed outputs immutable after confirmation unless the product explicitly supports reopening later.

### AWS / Infrastructure Notes
- Use S3 for generated export files and ensure access is appropriately controlled.

### Backend Notes
- Validate that required upstream artifacts exist before enabling finalization.
- Capture edit history or at minimum final edited content plus attributable audit events.

### Frontend Notes
- The frontend should receive explicit editability and finalization state, not infer them from raw status strings alone.

## 6. Deliverables

The task should produce:
- Review, update, finalize, and export endpoints
- Edit and finalization persistence
- Audit trails for human actions
- Export generation logic
- Workflow documentation

## 7. Acceptance Criteria

- [ ] Physicians can review and edit generated outputs before finalization.
- [ ] Finalization requires explicit physician confirmation and records attribution.
- [ ] Finalized records cannot be produced from incomplete processing states.
- [ ] Export generation uses finalized content and stores resulting artifacts correctly.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for review-state rules and finalization guards
- Integration tests for review update, finalize, and export endpoints

### Manual Verification
Load a generated consultation, edit the outputs, finalize it as the responsible physician, and confirm the exported artifact and audit trail reflect the finalized version.

## 9. Risks and Edge Cases

### Risks
- Weak attribution could undermine trust and compliance expectations.
- Finalization race conditions could produce conflicting records.

### Edge Cases
- A physician opens the review screen before AI generation fully finishes.
- Export is requested before finalization.
- A second finalize request arrives after completion.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
