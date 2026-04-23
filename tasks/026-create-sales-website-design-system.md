# Task 026: Create Sales Website Design System

## 1. Overview

### Objective
Create a public sales website design system by reusing the authenticated app colors, spacing, logo assets, typography direction, and visual constraints already established for Notter.

### Why This Matters
The public website should feel like the same product physicians see after login, while staying static, fast, crawlable, and easy to deploy.

### Task Type
- Frontend

### Priority
- High

## 2. Context

### Product Context
The sales website introduces Notter to Brazilian physicians and must set accurate expectations: documentation support, physician review, and no autonomous clinical decisions.

### Technical Context
The authenticated app already has tokens in `app/src/styles/tokens.css`, UI primitives in `app/src/components/ui`, and Notter logo assets in `app/public`. The public website lives in `website/` and must remain standard HTML/CSS with minimal JavaScript.

### Related Systems
- Public website
- Frontend app
- CI/CD

### Dependencies
- `016-apply-notter-frontend-branding.md`
- `017-create-authenticated-app-design-system.md`
- `018-apply-authenticated-app-facelift.md`
- `020-fix-authenticated-app-polish-copy-and-logo.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `app/README.md`

## 3. Scope

### In Scope
- Audit authenticated app design tokens, logo usage, spacing, surfaces, radius, focus styles, and responsive layout conventions.
- Define website-scoped CSS custom properties in `website/assets/css/main.css` or a dedicated website design-system stylesheet.
- Reuse Notter logo assets from the existing frontend asset set without renaming internal DeskAI identifiers.
- Document the sales website token mapping and visual usage rules in `website/README.md`.
- Keep user-facing website examples and labels in `pt-BR`.

### Out of Scope
- Creating Figma screens.
- Implementing final page layouts.
- Adding backend integrations or new API behavior.
- Renaming internal `DeskAI` packages, stack names, variables, contracts, or infrastructure identifiers.

## 4. Requirements

### Functional Requirements
- The website design system must map the authenticated app token values into public website CSS variables.
- The website must use Notter logo assets consistently for public-facing branding.
- The design system must support landing, pricing, about/trust, and entry-flow surfaces.

### Non-Functional Requirements
- CSS must stay small, static, and compatible with CloudFront static hosting.
- Token naming should be clear and maintainable for future page work.
- The design system must preserve accessible focus states and responsive spacing.

### Business Rules
- Public copy must present Notter as documentation assistance and review support only.
- Public content must not imply diagnosis, prescription, autonomous clinical decisions, social login, or SSO.
- User-facing public content must be in Brazilian Portuguese.

### Technical Rules
- Use standard CSS custom properties.
- Keep the public website separate from the React authenticated app.
- Prefer reuse of existing visual decisions over inventing a new website palette.

## 5. Implementation Notes

### Proposed Approach
Start by reading the authenticated token files and logo component usage, then build a website token layer that mirrors the relevant values with website-specific names where helpful. Keep a compact usage guide in the website README so the next tasks can build from stable tokens.

### AWS / Infrastructure Notes
- No AWS changes are expected.

### Backend Notes
- No backend changes are expected.

### Frontend Notes
- Check `app/src/styles/tokens.css`, `app/src/styles/design-system.css`, `app/src/index.css`, `app/src/components/BrandLogo.tsx`, and `website/assets/images`.
- Avoid gradients, decorative blobs, or unrelated palette changes that would make the sales site diverge from the authenticated app.

## 6. Deliverables

The task should produce:
- Website design tokens and base styles
- Public website logo usage guidance
- Updated `website/README.md`
- Style validation updates if needed

## 7. Acceptance Criteria

- [ ] Website CSS includes a reusable token layer based on the authenticated app design system.
- [ ] Website logo assets and brand treatment match the existing Notter frontend identity.
- [ ] Website spacing, radius, focus, and surface styles are documented.
- [ ] Internal `DeskAI` technical identifiers are preserved.
- [ ] Relevant tests or static validations are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Run `npm run lint` in `website/`.
- Add or update style/static checks if token usage can be validated automatically.

### Manual Verification
Compare the website base styles with the authenticated app login and shell surfaces. Verify logo rendering, focus states, contrast, and responsive token behavior at mobile and desktop widths.

## 9. Risks and Edge Cases

### Risks
- Copying React app implementation details into the static website could make the website harder to maintain.
- A disconnected palette could make public and authenticated experiences feel like different products.

### Edge Cases
- Logo assets may need different sizing rules for header, footer, favicon, and social metadata contexts.
- Some app tokens may be too product-workflow-specific and should not be reused directly.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
