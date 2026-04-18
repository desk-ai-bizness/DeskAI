# Task 016: Apply Notter Frontend Branding

## 1. Overview

### Objective
Update the authenticated frontend display branding from DeskAI to Notter and integrate the new logo assets in the React app without renaming backend systems, packages, variables, contracts, infrastructure, or internal project references.

### Why This Matters
The product needs a polished physician-facing identity while preserving the existing DeskAI technical baseline. This keeps the rebrand reversible and limits risk to the presentation layer.

### Task Type
- Frontend

### Priority
- High

## 2. Context

### Product Context
Physicians should see the product as Notter in the authenticated app. The application still supports the same consultation documentation workflow and must remain clear that AI-generated content requires physician review.

### Technical Context
The React app currently contains user-facing DeskAI references and the new logo assets already exist in `app/public/logo-icon.png` and `app/public/logo-text.png`.

### Related Systems
- Frontend app
- Authentication
- CI/CD

### Dependencies
- `012-build-authenticated-react-app.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/02-consultation-lifecycle.md`

## 3. Scope

### In Scope
- Replace user-facing DeskAI product-name references in the authenticated app with Notter.
- Add the new Notter logo icon and text assets to the app shell and login experience.
- Update document title, accessible logo alt text, and visible brand copy where applicable.
- Add or update frontend tests that protect the frontend-only branding boundary.
- Keep pt-BR product copy where text is visible to users.

### Out of Scope
- Renaming npm packages, source folders, backend modules, Python packages, environment variables, API paths, AWS resources, contracts, or internal DeskAI references.
- Updating the public marketing website branding unless it is explicitly in shared app metadata used by the authenticated frontend.
- Changing authentication, entitlement, consultation, review, finalization, or export behavior.

## 4. Requirements

### Functional Requirements
- The authenticated app must display Notter as the product name in user-facing surfaces.
- Logo images must load from `app/public/logo-icon.png` and `app/public/logo-text.png`.
- Brand images must have appropriate accessible text or hidden treatment depending on whether adjacent text already announces the brand.
- Existing app routes and user flows must continue to work.

### Non-Functional Requirements
- The change must be presentation-only and low risk.
- Logo usage must be responsive and must not cause layout shift in the header or login screen.
- Sensitive user or consultation data must not be introduced into logs or analytics as part of this work.

### Business Rules
- User-facing app content must be written in Brazilian Portuguese (`pt-BR`).
- The app must continue to represent AI-generated content as draft content pending physician review.
- The MVP must remain limited to authenticated physicians using email and password.

### Technical Rules
- Use React + TypeScript + Vite.
- Keep internal DeskAI technical identifiers unchanged.
- Prefer existing component and test patterns in `app/src`.

## 5. Implementation Notes

### Proposed Approach
Identify user-facing brand strings in the authenticated app, update them to Notter, and add a small reusable brand/logo component only if it reduces duplication across login and app layout.

### AWS / Infrastructure Notes
- No AWS infrastructure changes are expected.

### Backend Notes
- No backend changes are expected.

### Frontend Notes
- Review `AppLayout`, `LoginPage`, `index.html`, and any visible app metadata.
- Use fixed intrinsic logo dimensions or CSS constraints to avoid layout movement.
- Preserve internal technical references such as `deskai-app`, API client names, contract versions, and environment variable names.

## 6. Deliverables

The task should produce:
- Frontend branding updates
- Logo integration in authenticated app surfaces
- Updated frontend tests
- Documentation updates if local app setup or branding guidance changes

## 7. Acceptance Criteria

- [x] User-facing authenticated app surfaces display Notter instead of DeskAI.
- [x] `app/public/logo-icon.png` and `app/public/logo-text.png` are used where appropriate.
- [x] Internal DeskAI technical references remain unchanged.
- [x] Product-facing UI content remains in `pt-BR`.
- [x] Relevant tests are added or updated.
- [x] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Component tests for login and authenticated layout branding.
- Regression test or assertion that visible app copy uses Notter while internal technical names are not renamed.

### Manual Verification
Run the app locally, verify login and authenticated layout show Notter branding, confirm the logos render at desktop and mobile widths, and complete a basic navigation flow after login.

## 9. Risks and Edge Cases

### Risks
- Accidentally renaming internal DeskAI identifiers could break package scripts, API configuration, or infrastructure references.
- Logo dimensions could create layout shift or cramped mobile headers.

### Edge Cases
- Asset loading failure should leave readable text or accessible brand fallback.
- Some technical references may legitimately continue to contain DeskAI and should not be changed.

## 10. Definition of Done

- [x] Implementation is complete.
- [x] Acceptance criteria are met.
- [x] Tests pass.
- [x] No obvious regressions were introduced.
- [x] Logs, metrics, and error handling were considered.
- [x] Security and permissions were reviewed if relevant.
- [x] Task is ready for review or merge.

## 11. Implementation Summary (2026-04-18)

- Added a reusable `BrandLogo` component for the authenticated app.
- Updated login, authenticated shell, session-loading shell, and app document title to use Notter branding.
- Integrated `app/public/logo-icon.png` and `app/public/logo-text.png` with fixed dimensions to avoid layout shift.
- Preserved internal DeskAI technical references such as `deskai-app` and `deskai.auth.session`.
- Added component tests covering Notter branding, logo assets, and existing sign-out behavior.
- Verified with `npm run typecheck`, `npm run lint`, `npm test`, and `npm run build` in `app/`.
