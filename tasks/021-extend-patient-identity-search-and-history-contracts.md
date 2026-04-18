# Task 021: Extend Patient Identity, Search, And History Contracts

## 1. Overview

### Objective
Extend patient identity and lookup support so CPF is required, unique within a clinic, searchable, and available on patient detail screens with current-doctor-only consultation history.

### Why This Matters
The revised consultation entry flow depends on finding patients by name or CPF and safely reviewing prior appointments before starting a new consultation. The current backend only supports minimal patient records with `name` and `date_of_birth`, name-only search, and no patient detail/history endpoint.

### Task Type
- Full Stack

### Priority
- Critical

## 2. Context

### Product Context
Doctors should start consultations from a patient-first workflow. Existing patients are selected by name or CPF, and patient history must respect the current MVP access rule that consultation content belongs to the creating physician.

### Technical Context
Patient endpoints were intentionally minimal in ADR-014 and DEC-008. This task expands those contracts and persistence rules while keeping business logic in the backend and frontend behavior backend-shaped.

### Related Systems
- Backend API
- BFF layer
- Database
- Frontend app
- Authentication
- Observability

### Dependencies
- `006-model-consultation-domain-persistence-and-audit.md`
- `011-implement-review-finalization-and-export-workflows.md`
- `014-add-observability-security-privacy-and-cost-controls.md` for security guidance where relevant

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/03-plan-entitlements.md`
- `docs/requirements/05-decision-log.md`

## 3. Scope

### In Scope
- Update patient contracts, domain model, use cases, handlers, BFF views, and frontend types for CPF.
- Make `name` and CPF the minimum required patient identity fields.
- Make `date_of_birth` optional unless a later business rule explicitly makes it required again.
- Normalize CPF to digits for storage/search, validate CPF format, and return masked CPF where appropriate for display.
- Enforce CPF uniqueness per clinic.
- Extend `GET /v1/patients?search=` to filter by patient name or CPF.
- Add `GET /v1/patients/{patient_id}` returning patient details plus previous consultations owned by the current doctor only.
- Include safe patient history data such as consultation id, status, scheduled date, finalized date when available, and safe reviewed/finalized preview only when authorized and already available.
- Update docs, contract inventory, and ADR/decision notes for the new patient contract.

### Out of Scope
- Clinic-wide consultation history across multiple doctors.
- Deep EHR integration, external patient import, CNS lookup, CADSUS integration, or public-sector registry integration.
- Changing finalization immutability or export rules.
- Building the full staged frontend flow; that belongs to Task 022.

## 4. Requirements

### Functional Requirements
- Creating a patient requires `name` and CPF.
- CPF must be normalized and unique within a clinic.
- Patient search must match by name or CPF.
- Patient detail must include patient identity fields and current-doctor-only consultation history.
- Patient history must not expose consultation content owned by other physicians.
- Existing consultation creation must still reference an existing patient in the clinic.

### Non-Functional Requirements
- CPF, patient names, and consultation content must not be logged raw.
- Authorization failures must be explicit and auditable.
- The data model should remain reversible and compatible with DynamoDB single-table patterns.
- Contract changes must be covered by tests to prevent frontend/backend drift.

### Business Rules
- Each consultation belongs to one physician, one patient, and one clinic context.
- Patient records are clinic-scoped, but consultation data access remains limited to the creating physician.
- Consultation data is sensitive health information.
- The system must not expose raw medical content or unnecessary patient-identifiable data in logs.

### Technical Rules
- Follow Hexagonal Architecture boundaries.
- Keep CPF validation and uniqueness enforcement in backend/domain/application layers, not the frontend.
- Follow strict TDD for new domain, use case, handler, adapter, and contract behavior.
- Update shared contracts before relying on new response shapes in the frontend.

## 5. Implementation Notes

### Proposed Approach
Define the new patient contract first with failing contract/handler tests, then update the patient entity and persistence adapter. Add a repository lookup for normalized CPF within clinic, a current-doctor history query, and a BFF detail view that returns only authorized history fields.

### AWS / Infrastructure Notes
- Reuse the existing DynamoDB table.
- Add or adjust indexes only if needed for CPF uniqueness/search or patient consultation history performance.
- Any new index or IAM permission must be least-privilege and covered by infrastructure tests.

### Backend Notes
- Add CPF normalization and masking helpers in backend code, with unit tests.
- Enforce uniqueness per clinic at write time; handle duplicate CPF as a clear 409 or equivalent domain error.
- Add `GET /v1/patients/{patient_id}` to contracts, router, handler, use case, and BFF view.
- Add a consultation repository method for current-doctor history by patient, or use an existing query pattern if it remains efficient and explicit.
- Avoid logging raw CPF; structured logs should use patient id and clinic id only, or masked CPF if absolutely necessary.

### Frontend Notes
- Update TypeScript contract types and API endpoint wrappers.
- Do not build the staged flow yet; only make the new endpoint and types ready for Task 022.
- Display CPF only in masked form unless the backend explicitly returns a full value for a justified editing use case.

## 6. Deliverables

The task should produce:
- Updated patient HTTP contracts
- Updated domain/application/adapter/handler/BFF code
- Updated frontend API types and endpoint wrappers
- Updated docs and ADR/decision notes
- Domain, handler, repository, contract, frontend type/API, and security logging tests

## 7. Acceptance Criteria

- [x] Patient creation requires `name` and CPF and treats `date_of_birth` as optional.
- [x] CPF is normalized, validated, unique per clinic, and never logged raw.
- [x] `GET /v1/patients?search=` searches by name or CPF.
- [x] `GET /v1/patients/{patient_id}` returns patient details plus current-doctor-only consultation history.
- [x] Patient history does not expose other doctors' consultation content.
- [x] Contract inventory, DEC-008, and ADR-014 are updated.
- [x] Relevant tests are added or updated.
- [x] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Domain tests for CPF normalization, validation, and required identity fields.
- Application tests for duplicate CPF handling and patient detail/history authorization.
- DynamoDB adapter tests for CPF persistence/search and any new query/index behavior.
- HTTP handler and BFF view tests for create/list/detail response shapes.
- Contract tests for patient create/list/detail schemas.
- PHI/PII logging tests proving raw CPF is not logged.
- Frontend API/type tests where practical.

### Manual Verification
Create a patient with name and CPF, attempt duplicate CPF in the same clinic, search by name and CPF, open patient detail, and verify history only includes consultations owned by the authenticated doctor.

## 9. Risks and Edge Cases

### Risks
- CPF uniqueness can race if implemented without a conditional write strategy.
- Adding clinic-wide patient search could accidentally expose consultation summaries if history authorization is not separated.
- Existing seed/test fixtures may assume `date_of_birth` is required.

### Edge Cases
- CPF entered with punctuation, spaces, or copy/paste artifacts.
- Patient without date of birth from existing records.
- Patient exists in another clinic with the same CPF.
- Patient has no consultations owned by the current doctor.
- Patient has finalized and non-finalized consultations in history.

## 10. Definition of Done

- [x] Implementation is complete.
- [x] Acceptance criteria are met.
- [x] Tests pass.
- [x] No obvious regressions were introduced.
- [x] Logs, metrics, and error handling were considered.
- [x] Security and permissions were reviewed if relevant.
- [x] Task is ready for review or merge.
