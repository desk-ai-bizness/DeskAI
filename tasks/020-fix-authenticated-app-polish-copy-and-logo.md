# Task 020: Fix Authenticated App Polish, Copy, And Logo

## 1. Overview

### Objective
Fix the authenticated app's immediate visual and copy issues by replacing gradient backgrounds with a stable light gray surface, correcting missing Brazilian Portuguese accents in user-facing copy, and making the login logo icon white when it appears on the dark showcase background.

### Why This Matters
The physician-facing app should feel calm, trustworthy, and production-ready. Cheap-looking visual treatment, incorrect accents, or inconsistent logo contrast reduce confidence before the doctor reaches the core consultation workflow.

### Task Type
- Full Stack

### Priority
- High

## 2. Context

### Product Context
Physicians use the authenticated app to document sensitive consultations. User-facing text must be in correct `pt-BR`, and the Notter brand must look intentional across the login and authenticated surfaces.

### Technical Context
The app already has Notter assets, design-system primitives, page-level styling, and backend-provided BFF labels. Some visible fallback strings and BFF UI labels still lack accents, and the login page applies a white treatment only to the logo text image.

### Related Systems
- Frontend app
- Backend API
- BFF UI configuration
- Authentication

### Dependencies
- `016-apply-notter-frontend-branding.md`
- `017-create-authenticated-app-design-system.md`
- `018-apply-authenticated-app-facelift.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`

## 3. Scope

### In Scope
- Replace authenticated app gradient/fade backgrounds with a stable light gray background.
- Remove login ambient background treatment that makes the product feel less polished.
- Correct missing accents in visible frontend copy, frontend tests, and backend-provided BFF UI labels.
- Make the login-page Notter logo icon white whenever the logo text is white.
- Add or update tests that protect corrected copy and logo treatment.

### Out of Scope
- Redesigning the consultation workflow, patient flow, live session, or review flow.
- Changing internal code identifiers, API paths, environment variables, AWS resources, or package names.
- Updating the public marketing website.
- Changing backend business rules beyond BFF label copy.

## 4. Requirements

### Functional Requirements
- The app must use a consistent light gray page background instead of decorative gradients or fades.
- All physician-facing copy in the authenticated app and BFF UI config must use correct Brazilian Portuguese accents.
- The login logo must render as a cohesive white logo on the dark showcase panel, including both icon and text.
- Existing login, authenticated shell, consultation, live session, review, finalization, and export flows must continue to work.

### Non-Functional Requirements
- Visual changes must remain responsive and layout-stable.
- Copy changes must not alter backend workflow behavior.
- The app must continue to avoid logging CPF, patient names, raw transcript content, or other sensitive consultation data.

### Business Rules
- User-facing app content must be written in Brazilian Portuguese (`pt-BR`).
- AI-generated content must continue to be shown as draft/reviewable content until physician finalization.
- The MVP remains an authenticated physician app using email and password only.

### Technical Rules
- Follow strict TDD for applicable frontend and backend copy tests.
- Keep the frontend presentation-only and backend-driven where labels come from BFF UI config.
- Keep internal DeskAI technical references unchanged.

## 5. Implementation Notes

### Proposed Approach
Start with failing tests or snapshot assertions for the most visible corrected labels and login logo styling. Then update frontend fallback strings, BFF UI labels, and CSS tokens/classes so the app background is neutral and the login logo uses a light icon variant or CSS treatment.

### AWS / Infrastructure Notes
- No AWS infrastructure changes are expected.

### Backend Notes
- Review BFF UI config label sources for missing accents, especially status labels, action labels, review labels, and warning/disclaimer copy.
- Keep API contract shapes unchanged.

### Frontend Notes
- Review `LoginPage`, `BrandLogo`, `AppLayout`, page components, tests, and `index.css`.
- Prefer an explicit logo variant prop such as `tone="light"` if it keeps the icon treatment reusable and testable.
- Use a single light gray background token for app shells and page body surfaces.
- Avoid decorative gradient, bokeh, or ambient background layers.

## 6. Deliverables

The task should produce:
- Frontend copy and CSS updates
- Login logo light-treatment update
- BFF UI label copy updates where needed
- Updated frontend and backend tests
- Documentation updates if styling or branding guidance changes

## 7. Acceptance Criteria

- [ ] Authenticated app backgrounds use a stable light gray surface without gradient/fade decoration.
- [ ] Login-page Notter icon and text both render white on the dark showcase background.
- [ ] User-facing authenticated app copy and BFF labels use correct `pt-BR` accents.
- [ ] Existing authenticated app behavior is unchanged.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Frontend component tests for login logo treatment and visible corrected copy.
- Frontend page tests updated for accented fallback strings.
- Backend/BFF tests updated for accented UI config labels.
- Existing frontend and backend tests must remain green.

### Manual Verification
Run the app locally, inspect login and authenticated pages at desktop and mobile widths, verify the background is neutral light gray, confirm the login logo is fully white on the dark panel, and scan visible app copy for missing accents.

## 9. Risks and Edge Cases

### Risks
- Correcting test strings without correcting all runtime strings could leave hidden unaccented fallback copy.
- Applying a CSS filter to the logo icon globally could accidentally make the authenticated shell icon white on light backgrounds.

### Edge Cases
- Logo assets fail to load and the accessible brand name must still be clear.
- Backend UI config fails to load and frontend fallback strings must still be correct `pt-BR`.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
