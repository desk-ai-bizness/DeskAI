# Task 022: Build Staged Consultation Entry And Patient Flow

## 1. Overview

### Objective
Split the consultation list from consultation creation and replace the post-login home screen with a staged patient-first "Nova consulta" flow.

### Why This Matters
The current screen combines the appointment list and new appointment creation, which makes the primary workflow feel cluttered. Doctors should start from a focused flow: choose an existing patient or create a new patient, then begin the consultation workspace.

### Task Type
- Frontend

### Priority
- Critical

## 2. Context

### Product Context
After login, the doctor should immediately land on the flow for starting a new consultation. Existing-patient selection should support name/CPF search and show patient context before the doctor starts a new consultation. New-patient creation should be fast and require only the minimum identity fields.

### Technical Context
The app currently redirects `/` to `/consultations`, and `ConsultationsPage` contains both the consultation list and new consultation form. Task 021 provides the backend patient CPF/search/detail/history contract required for the staged flow.

### Related Systems
- Frontend app
- Backend API
- BFF layer
- Authentication

### Dependencies
- `021-extend-patient-identity-search-and-history-contracts.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`

## 3. Scope

### In Scope
- Split consultation creation and consultation listing into separate screens.
- Route `/` after login to the staged "Nova consulta" entry screen.
- Keep `/consultations` as a list/history screen only.
- Build first-stage choices: "Selecionar paciente existente" and "Novo paciente."
- Build existing-patient search by name or CPF using the backend patient search contract.
- Build patient detail/history screen using `GET /v1/patients/{patient_id}`.
- Add a prominent "Iniciar nova consulta" button on the patient detail screen.
- Build new-patient flow requiring only patient name and CPF.
- Default consultation date to today's date when creating a consultation.
- Continue to the consultation workspace route after consultation creation.
- Update navigation, tests, and app documentation.

### Out of Scope
- Backend patient CPF/search/detail implementation; that belongs to Task 021.
- Redesigning the live consultation workspace; that belongs to Task 024.
- Implementing real live transcript/autofill events; that belongs to Task 023.
- Clinic-wide patient history across doctors.

## 4. Requirements

### Functional Requirements
- Successful login and direct visits to `/` must take authenticated doctors to the "Nova consulta" flow.
- The consultation list must no longer contain the new consultation form.
- Existing-patient search must support backend filtering by name or CPF.
- Selecting a patient must show patient details and previous consultations owned by the current doctor.
- The patient detail screen must include a prominent "Iniciar nova consulta" action.
- New-patient creation must ask for name and CPF, then create or reuse the patient according to backend behavior and create a consultation dated today.

### Non-Functional Requirements
- The flow must be responsive, accessible, and layout-stable.
- Sensitive patient identifiers must be displayed carefully, using masked CPF when provided by the backend.
- Error, loading, and empty states must be clear and consistent with the design system.

### Business Rules
- User-facing copy must be in Brazilian Portuguese (`pt-BR`).
- Each consultation must belong to one physician, one patient, and one clinic context.
- The frontend must not decide business rules such as CPF uniqueness, patient ownership, or plan limits.
- Consultation content in history must remain limited to authorized current-doctor data.

### Technical Rules
- Use React + TypeScript + Vite.
- Keep workflow rules backend-driven where practical.
- Use existing query/mutation hook patterns and invalidate caches after create actions.
- Follow strict TDD for route and component behavior.

## 5. Implementation Notes

### Proposed Approach
Add route-level tests for the new post-login redirect and separated list/create screens. Create a new consultation entry page, patient search/detail components, and a list-only consultations page while reusing existing API and query-hook patterns.

### AWS / Infrastructure Notes
- No AWS infrastructure changes are expected.

### Backend Notes
- No backend changes are expected beyond consuming the Task 021 contracts.

### Frontend Notes
- Update `App.tsx` route defaults and login navigation targets.
- Consider routes such as `/nova-consulta`, `/patients/:patientId`, and `/consultations` while keeping URL names consistent with existing route style.
- Use today's local date as the default scheduled date in the create consultation request.
- Keep specialty as the backend-supported general-practice value unless UI config later provides a selector.
- Ensure the "Iniciar nova consulta" action is visually prominent and keyboard accessible.

## 6. Deliverables

The task should produce:
- New staged consultation entry screen
- Patient search and patient detail/history screen
- List-only consultation history screen
- Updated routing and navigation
- Updated query hooks/types if needed
- Updated frontend tests and documentation

## 7. Acceptance Criteria

- [ ] After login, doctors land on the "Nova consulta" flow instead of the consultation list.
- [ ] The consultation list and new-consultation flow are separate screens.
- [ ] Existing-patient flow searches by name or CPF and opens patient detail/history.
- [ ] Patient detail includes a prominent "Iniciar nova consulta" button.
- [ ] New-patient flow requires only name and CPF and creates a consultation dated today.
- [ ] `/consultations` remains available as the list/history screen.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Route tests for `/`, login redirect, and list-only `/consultations`.
- Component tests for staged choice selection, existing-patient search, empty states, patient detail/history, and new-patient submission.
- Mutation tests for create patient and create consultation cache invalidation.
- Accessibility-focused assertions for primary actions and form labels.

### Manual Verification
Log in locally, confirm the home screen is "Nova consulta", choose existing patient, search by name/CPF, inspect patient history, start a new consultation, then repeat with a new patient and verify today's date is sent by default.

## 9. Risks and Edge Cases

### Risks
- Moving route defaults could break tests or expectations around `/consultations`.
- Frontend may accidentally duplicate backend uniqueness or plan rules if validations go beyond presentation checks.
- CPF display could expose more than the backend intended if full CPF values are rendered.

### Edge Cases
- No patients match the search.
- Patient exists but has no current-doctor consultation history.
- Trial or plan limits prevent consultation creation.
- Create patient succeeds but create consultation fails.
- Browser date differs from backend date due to timezone boundaries.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
