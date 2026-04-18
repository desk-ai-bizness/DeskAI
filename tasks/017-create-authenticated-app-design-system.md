# Task 017: Create Authenticated App Design System

## 1. Overview

### Objective
Create a small, reusable frontend design system for the authenticated React app, covering visual tokens, buttons, typography, links, chips, loaders, cards, inputs, banners, and icon usage.

### Why This Matters
The app has a functional workflow, but the UI needs a more consistent premium visual foundation before broader page-level polish. A focused design system prevents one-off CSS and makes later UI improvements faster and safer.

### Task Type
- Frontend

### Priority
- High

## 2. Context

### Product Context
Physicians need a calm, professional interface for sensitive consultation documentation. The interface should feel trustworthy, responsive, and polished without distracting from review and finalization responsibilities.

### Technical Context
The authenticated app currently uses plain CSS and page-level class names. The app is small enough to keep CSS-first styling, but it may need a lightweight icon library and reusable React components.

### Related Systems
- Frontend app
- CI/CD

### Dependencies
- `012-build-authenticated-react-app.md`
- `016-apply-notter-frontend-branding.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/03-plan-entitlements.md`

## 3. Scope

### In Scope
- Define reusable CSS tokens for color, spacing, type scale, elevation, borders, focus states, motion, and responsive layout.
- Create reusable components for buttons, text/headings, links, pills/chips, loaders/spinners, cards/panels, form inputs, textareas, selects, alerts/banners, and empty states.
- Add a lightweight icon library when justified, preferably one that is tree-shakeable and simple to test.
- Add Notter logo components or brand primitives if not already created in Task 016.
- Add component tests for behavior, accessibility, disabled/loading states, and variant rendering.
- Document usage guidance in the app README or an app-local design system note.

### Out of Scope
- Rebuilding every page with the new components.
- Adding a large UI framework unless a clear need is documented.
- Changing backend-driven business logic, contracts, or API behavior.
- Creating a public website design system.

## 4. Requirements

### Functional Requirements
- Components must support the current app needs: login, consultation list, live session, review, finalization, export, loading, empty, and error states.
- Button components must support loading and disabled states without layout shift.
- Form components must support labels, help text, error text, and accessible field associations.
- Loader components must support inline button loading and page/section loading states.
- Icons must be decorative by default unless a meaningful accessible label is required.

### Non-Functional Requirements
- Styling must remain maintainable for a small app and should prefer CSS modules or organized plain CSS over scattered page-only styles.
- Transitions and fades must respect `prefers-reduced-motion`.
- Components must be responsive and layout-stable.
- The visual style should feel premium, restrained, and professional for a healthcare documentation product.

### Business Rules
- User-facing product copy must be in Brazilian Portuguese (`pt-BR`).
- The interface must preserve the physician review boundary for AI-generated content.
- Clinical attention flags must be presented as reviewable observations, not diagnoses.

### Technical Rules
- Use React + TypeScript + Vite.
- Keep business rules out of frontend components.
- Prefer backend-shaped data and backend-provided labels where practical.
- If adding dependencies, update `app/package.json`, `app/package-lock.json`, tests, and docs.
- Document any important dependency choice as a concise ADR entry in `docs/mvp-technical-specs.md` if it becomes a durable technical decision.

## 5. Implementation Notes

### Proposed Approach
Create an app-local component library under `app/src/components/ui` and a small token/style foundation under `app/src/styles` or the existing CSS structure. Keep primitives composable and boring enough to be reused across pages.

### AWS / Infrastructure Notes
- No AWS infrastructure changes are expected.

### Backend Notes
- No backend changes are expected.

### Frontend Notes
- Consider `lucide-react` or an equivalent lightweight icon library for icons.
- Use components with stable sizing for buttons, chips, cards, and loaders.
- Avoid page components owning low-level styling details after primitives exist.
- Avoid card-inside-card layouts and avoid relying on decorative blobs or one-note palettes.
- Keep border radii modest and consistent.

## 6. Deliverables

The task should produce:
- Reusable UI components
- Shared design tokens/styles
- Icon library integration if approved by the implementation
- Component tests
- App documentation and ADR update if a new durable dependency is introduced

## 7. Acceptance Criteria

- [x] A reusable app-local design system exists for core UI primitives.
- [x] Buttons, inputs, chips, loaders, cards/panels, links, alerts, and empty states have consistent variants.
- [x] Loading and disabled states are accessible and layout-stable.
- [x] Motion respects reduced-motion preferences.
- [x] Any added dependency is justified, documented, and covered by lockfile updates.
- [x] Relevant tests are added or updated.
- [x] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Unit/component tests for UI primitives and variants.
- Accessibility-oriented assertions for labels, roles, disabled states, and loading states.
- Existing app tests must remain green.

### Manual Verification
Run the app locally and inspect the component usage in a temporary or integrated page context. Verify keyboard focus, hover states, loading states, mobile widths, and reduced-motion behavior.

## 9. Risks and Edge Cases

### Risks
- Overbuilding a design system could slow MVP delivery.
- Adding a heavy UI dependency could increase bundle size and reduce control.
- Visual polish could accidentally hide review warnings or important clinical documentation states.

### Edge Cases
- Long Portuguese labels must wrap without breaking buttons or cards.
- Loading text changes must not resize primary action buttons.
- Icons must not be the only way to understand an action.

## 10. Definition of Done

- [x] Implementation is complete.
- [x] Acceptance criteria are met.
- [x] Tests pass.
- [x] No obvious regressions were introduced.
- [x] Logs, metrics, and error handling were considered.
- [x] Security and permissions were reviewed if relevant.
- [x] Task is ready for review or merge.

## 11. Implementation Summary (2026-04-18)

- Added reusable UI primitives under `app/src/components/ui`: `Button`, `Text`, `Heading`, `Link`, `Chip`, `Loader`, `Card`, `TextField`, `TextAreaField`, `SelectField`, `Alert`, `EmptyState`, and `Icon`.
- Added design tokens in `app/src/styles/tokens.css` and component styles in `app/src/styles/design-system.css`.
- Added `lucide-react` as a lightweight tree-shakeable icon dependency and wrapped it behind the app-local `Icon` primitive.
- Documented design-system usage in `app/README.md`.
- Added ADR-015 in `docs/mvp-technical-specs.md` for the icon library decision.
- Added component tests for accessibility, variants, loading/disabled states, form descriptions, alerts, empty states, and icon defaults.
- Verified with `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`, and `npm audit --omit=dev` in `app/`.
