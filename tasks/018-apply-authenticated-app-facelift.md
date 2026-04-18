# Task 018: Apply Authenticated App Facelift

## 1. Overview

### Objective
Apply the Notter design system across the authenticated React app to improve visual quality, usability, information hierarchy, responsive behavior, and physician workflow clarity.

### Why This Matters
The app is functional but needs a more professional, coherent, and comfortable experience before broader release readiness. The facelift should make the workflow easier to scan without changing backend-owned rules.

### Task Type
- Frontend

### Priority
- High

## 2. Context

### Product Context
Physicians use the app to move from consultation creation through live recording, review, editing, finalization, and export. Each step must feel clear, trustworthy, and explicit about what is draft versus finalized.

### Technical Context
Task 017 creates reusable primitives. This task applies those primitives to page-level UX and may reorganize frontend component placement when that improves maintainability.

### Related Systems
- Frontend app
- Backend API
- Authentication

### Dependencies
- `012-build-authenticated-react-app.md`
- `016-apply-notter-frontend-branding.md`
- `017-create-authenticated-app-design-system.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/03-plan-entitlements.md`

## 3. Scope

### In Scope
- Refactor existing authenticated app pages to use the design system components.
- Improve app shell, navigation, login, consultation list, consultation creation, live session, review, finalization, and export UI.
- Improve loading, empty, success, warning, and error states across pages.
- Improve responsive layouts for mobile, tablet, and desktop.
- Improve keyboard focus, form affordances, and action hierarchy.
- Move or split components when it creates clearer ownership and reuse.
- Update tests to cover the redesigned states and preserve critical workflow behavior.

### Out of Scope
- Changing backend API contracts or business rules.
- Adding new product features beyond UX improvements already supported by existing backend payloads.
- Rewriting the app with a new framework or heavy UI kit.
- Public website facelift.

## 4. Requirements

### Functional Requirements
- Physicians must still be able to complete the full authenticated MVP workflow.
- The UI must clearly distinguish draft AI output, reviewable insight flags, finalized state, and export availability.
- Page-level loading and error states must be clear and recoverable where recovery is possible.
- The layout must remain readable with realistic Portuguese copy and clinical documentation content.

### Non-Functional Requirements
- The facelift must preserve frontend thinness and rely on BFF payloads for workflow decisions.
- The UI must be responsive, accessible, and stable as content changes.
- Transitions must be subtle and must respect reduced-motion preferences.
- The app must not log raw medical content, CPF, PII, or unnecessary patient-identifiable data.

### Business Rules
- No AI-generated output is final until reviewed by the physician.
- Finalization must remain an explicit physician action.
- Only finalized consultations may be exported.
- Insights are review flags, not diagnoses or autonomous clinical decisions.
- User-facing product content must be in `pt-BR`.

### Technical Rules
- Use React + TypeScript + Vite.
- Keep business logic out of the frontend.
- Use backend-provided configuration, labels, statuses, and action availability wherever practical.
- Follow existing test patterns with Vitest and Testing Library.

## 5. Implementation Notes

### Proposed Approach
Update one page at a time using the design system primitives, starting with shared layout and then moving through the primary workflow. Keep visual refactors scoped and preserve existing API calls and state transitions.

### AWS / Infrastructure Notes
- No AWS infrastructure changes are expected.

### Backend Notes
- No backend changes are expected unless an existing BFF contract drift is discovered; any contract drift should be documented before expanding scope.

### Frontend Notes
- Prefer page sections and clear layout structure over nested decorative cards.
- Keep primary actions visually prominent and destructive or final actions clearly separated.
- Give live-session states strong visual feedback without implying clinical interpretation.
- Keep long review artifacts easy to scan with headings, evidence excerpts, and editable sections.

## 6. Deliverables

The task should produce:
- Updated authenticated app pages using the design system
- Refined component organization where useful
- Updated frontend tests
- Documentation updates if app structure or design system usage changes

## 7. Acceptance Criteria

- [ ] Core authenticated pages use the design system primitives consistently.
- [ ] The full sign-in to finalization workflow still works.
- [ ] Draft, review, finalized, and export states are visually clear.
- [ ] Mobile and desktop layouts are responsive and layout-stable.
- [ ] Accessibility basics are preserved or improved.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Component/integration tests for major page states and workflow actions.
- Regression tests for physician review, finalization, and export affordances.
- Existing frontend tests must remain green.

### Manual Verification
Run the app locally, complete the main workflow from login through review/finalization/export, and inspect the pages at mobile and desktop widths. Verify keyboard navigation, focus states, loading states, and reduced-motion behavior.

## 9. Risks and Edge Cases

### Risks
- Visual refactors could accidentally remove backend-driven action availability.
- A polished layout could hide warnings about draft or incomplete AI output.
- Component movement could make tests brittle if done without preserving behavior.

### Edge Cases
- Empty consultation list.
- Failed API request.
- Incomplete generated artifacts.
- WebSocket disconnected or microphone permission denied.
- Finalized consultation loaded in read-only mode.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
