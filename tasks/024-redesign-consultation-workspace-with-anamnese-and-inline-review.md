# Task 024: Redesign Consultation Workspace With Anamnese And Inline Review

## 1. Overview

### Objective
Redesign `/consultations/:id/live` into the primary consultation workspace with an Anamnese form, live transcript, provisional insights/autofill, session controls, and same-screen post-session review/finalization.

### Why This Matters
The live consultation screen is the core product experience. Doctors should not be sent through a fragmented live screen plus separate review screen. The consultation should start, run, end, be reviewed, edited, finalized, and exported from one coherent workspace.

### Task Type
- Full Stack

### Priority
- Critical

## 2. Context

### Product Context
The doctor begins a consultation with patient identity and today's date, records the session, watches transcript and AI-filled documentation appear, ends the session intentionally, then reviews and finalizes the generated content on the same screen.

### Technical Context
The current app has `/consultations/:id/live` for recording and `/consultations/:id/review` for review/finalization. Task 021 provides patient CPF/history contracts, Task 022 provides the staged entry flow, and Task 023 provides real realtime transcript/session data, async finalization, pause/resume, and the **schema-only** definitions for `insight.provisional` and `autofill.candidate` events.

This task is responsible for emitting those provisional AI/autofill events at runtime (backend producer) and rendering them (frontend consumer). Task 023 intentionally ships the contracts without an emitter; all runtime behavior for provisional events lands here.

### Related Systems
- Frontend app
- Backend API
- BFF layer
- WebSocket API
- AI pipeline
- Review/finalization/export workflows
- Storage

### Dependencies
- `021-extend-patient-identity-search-and-history-contracts.md`
- `022-build-staged-consultation-entry-and-patient-flow.md`
- `023-implement-realtime-consultation-data-feed.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/04-failure-behavior-matrix.md`
- `docs/requirements/05-decision-log.md`

## 3. Scope

### In Scope
- Redesign `/consultations/:id/live` as the main consultation workspace.
- Retire the separate review screen as the primary flow.
- Keep `/consultations/:id/review` as a redirect or backward-compatible route if existing links/tests need transition support.
- Build an "Anamnese" form with patient identity, consultation date, queixa principal, história da doença atual, medicamentos em uso, alergias, antecedentes pessoais, cirurgias/internações, antecedentes familiares, hábitos/estilo de vida, revisão de sistemas, exame objetivo/observações, transcript, resumo, and insights.
- Require only patient name, CPF, and today's consultation date to begin a new consultation.
- Show live transcript, provisional insights, and AI field-fill candidates during recording.
- Emit the `insight.provisional` and `autofill.candidate` events defined in Task 023 from the backend (AI pipeline / BFF) as soon as the pipeline has partial content, marked draft/incomplete with required evidence references.
- Render those provisional events on the workspace with explicit draft visual treatment and never as authoritative clinical content.
- Add pause/resume controls using the `session.pause` / `session.resume` actions introduced in Task 023.
- Add an end-session confirmation dialog.
- Keep the doctor on the same workspace after ending the session in a clear review state.
- Allow review, edit, finalization, and export from the same workspace.
- Make finalized consultations read-only.
- Update backend/BFF contracts if the unified workspace requires different view aggregation.

### Out of Scope
- Automatic diagnosis generation.
- Automatic prescription generation.
- Multi-specialty consultation handling.
- Clinic-wide patient history across doctors.
- Public marketing website changes.

## 4. Requirements

### Functional Requirements
- The full flow must happen on one workspace: create/start, record, pause/resume, end, review, edit, finalize, and export.
- The workspace must clearly distinguish recording, processing, review, finalized, and error states.
- AI-filled Anamnese fields must show source/evidence or incomplete/needs-review status where available.
- Ending the session must require a confirmation dialog.
- Finalization must remain explicit physician action.
- Finalized records must be locked from further edits.
- The route `/consultations/:id/review` must not be the primary user path after this task.

### Non-Functional Requirements
- The workspace must be attractive, organized, responsive, and optimized for sustained clinical documentation work.
- The layout must remain stable as live transcript and AI fields update.
- Sensitive data must not be logged or stored outside approved backend/browser state patterns.
- The frontend must remain presentation-focused and avoid owning clinical/business rules.

### Business Rules
- The MVP is a documentation support tool, not a clinical decision-maker.
- The system must report what was said and never interpret what it means as final clinical judgment.
- The system must not fabricate symptoms, diagnoses, medications, allergies, findings, plans, or follow-up instructions.
- No AI-generated output is final until physician review.
- A finalized consultation is immutable and locked from further edits.
- Only finalized consultations may be exported.

### Technical Rules
- Use React + TypeScript + Vite for the authenticated app.
- Keep backend business rules independent from frontend presentation.
- Use BFF-shaped data and backend-provided configuration where practical.
- Follow strict TDD for new view contracts, use cases, frontend routes, components, and workflow behavior.

## 5. Implementation Notes

### Proposed Approach
Start by defining the unified workspace view shape and failing tests for the desired route behavior. Then aggregate consultation detail, patient identity, live session state, review artifacts, and action availability into a BFF-friendly payload. Update the frontend workspace incrementally while preserving the existing finalization/export use cases.

### AWS / Infrastructure Notes
- No new AWS services are expected by default.
- If the unified workspace needs extra BFF aggregation, keep Lambda permissions least-privilege and avoid exposing raw artifacts beyond authorized requests.

### Backend Notes
- Align any new workspace payload with existing `ReviewView`, `ConsultationDetailView`, action availability, and UI config patterns.
- If `/review` redirects to `/live`, keep backend review endpoints available for compatibility unless explicitly removed in a later task.
- Ensure finalization still stores immutable final artifacts and audit events.

### Frontend Notes
- Build the primary workspace around stable sections rather than nested cards.
- Use "Anamnese" as the visible pt-BR label for structured medical history.
- Use field-level statuses such as draft, preenchido pela IA, precisa de revisão, incomplete, or equivalent backend-provided labels where available.
- Keep transcript, insights, and form updates visually distinct from physician-edited/finalized content.
- Preserve keyboard accessibility for recording controls, pause/resume, confirmation dialog, edit/save, finalize, and export actions.

## 6. Deliverables

The task should produce:
- Unified consultation workspace route and UI
- Anamnese form sections and field-state rendering
- Inline live transcript, insights, and AI/autofill candidate handling
- Pause/resume controls and end-session confirmation
- Same-screen review, edit, finalization, and export behavior
- Backward-compatible `/review` redirect or transition route
- Updated backend/BFF contracts if needed
- Updated tests and documentation

## 7. Acceptance Criteria

- [ ] `/consultations/:id/live` is the primary consultation workspace.
- [ ] `/consultations/:id/review` is no longer the primary review path and redirects or remains compatible.
- [ ] The workspace includes the required Anamnese sections.
- [ ] Only patient name, CPF, and today's consultation date are required to begin.
- [ ] Live transcript, provisional insights, and AI field-fill candidates appear on the same screen during recording.
- [ ] Pause/resume controls work according to backend state.
- [ ] Ending the session shows a confirmation dialog.
- [ ] Post-session review, edit, finalization, and export happen on the same workspace.
- [ ] Finalized consultations are read-only and exportable.
- [ ] Route, component, API, and workflow tests cover the complete flow.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Backend/BFF tests for any unified workspace view or action availability changes.
- Frontend route tests for `/live` primary workspace and `/review` redirect/compatibility behavior.
- Component tests for Anamnese fields, live transcript, provisional field updates, insights, and status banners.
- Interaction tests for start, pause, resume, end confirmation, review edits, finalization, read-only finalized state, and export.
- Regression tests proving no diagnosis/prescription automation is introduced by the workspace.

### Manual Verification
Complete the end-to-end flow: login, start a new consultation from a patient, record with live transcript, pause/resume, end with confirmation, review AI-filled Anamnese fields and insights on the same screen, edit content, finalize, confirm read-only state, and export.

## 9. Risks and Edge Cases

### Risks
- Combining live and review flows could accidentally blur provisional AI content and finalized content.
- A large workspace could become visually overwhelming if sections are not staged clearly.
- Redirecting the old review route could break existing links if not handled carefully.

### Edge Cases
- Processing is still running after the session ends.
- AI artifacts are partially generated or incomplete.
- The doctor navigates away during recording.
- WebSocket disconnect occurs during pause or resume.
- Finalization succeeds but export fails.
- Consultation is already finalized when opened.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
