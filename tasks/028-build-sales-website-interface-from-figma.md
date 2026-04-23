# Task 028: Build Sales Website Interface From Figma

## 1. Overview

### Objective
Implement the public sales website interface in `website/` from the Figma layout produced by Task 027.

### Why This Matters
The public website is the first physician-facing touchpoint. It must be polished, responsive, accurate, and deployable as simple static assets.

### Task Type
- Frontend

### Priority
- High

## 2. Context

### Product Context
The interface must explain Notter's documentation-support value proposition, establish trust, and guide physicians toward the authenticated app entry flow.

### Technical Context
The website package is a static HTML/CSS site with minimal JavaScript. It already has `pages/`, `assets/css/`, `assets/js/`, and Notter logo assets under `website/assets/images`.

### Related Systems
- Public website
- Frontend app
- CI/CD

### Dependencies
- `027-create-sales-website-figma-design.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `website/README.md`

## 3. Scope

### In Scope
- Build the website pages and sections from the approved Figma layout.
- Implement responsive desktop and mobile layouts using static HTML and CSS.
- Use the Task 026 website design system and Notter logo assets.
- Include SEO metadata, semantic headings, accessible navigation, and static content structure.
- Preserve existing simple deployment model.

### Out of Scope
- Backend API changes.
- Complex SPA behavior.
- Authenticated app workflow changes.
- Analytics, CRM, chat widgets, or non-MVP sales automation.

## 4. Requirements

### Functional Requirements
- Public pages must render the Figma-approved layout.
- Website navigation must connect landing, pricing, about/trust, and login/product entry surfaces.
- Product-facing content must be in `pt-BR`.
- Copy must clearly state that AI-generated content requires physician review.

### Non-Functional Requirements
- Pages must be fast, crawlable, responsive, and accessible.
- CSS should remain maintainable and avoid unnecessary framework/runtime dependencies.
- The implementation must avoid layout shifts from logo or responsive text changes.

### Business Rules
- The product must be presented as documentation assistance and review support, not as a clinical decision-maker.
- Social login, SSO, automatic diagnosis, and automatic prescriptions must not be advertised.
- The initial target user is a physician in Brazil.

### Technical Rules
- Use standard HTML and CSS.
- Use minimal JavaScript only when needed for lightweight interactions.
- Keep website and authenticated React app separate.

## 5. Implementation Notes

### Proposed Approach
Translate the Figma sections into semantic HTML first, then apply the website token layer and responsive CSS. Keep content editable in the static pages and avoid introducing build complexity unless a clear existing website tool already supports it.

### AWS / Infrastructure Notes
- Ensure static file paths remain compatible with CloudFront hosting.

### Backend Notes
- No backend changes are expected.

### Frontend Notes
- Check all text at mobile widths and use stable dimensions for headers, logo areas, CTA groups, plan cards, and repeated sections.
- Avoid in-app explanatory text about shortcuts or implementation details.

## 6. Deliverables

The task should produce:
- Implemented static website pages
- Updated CSS based on Task 026 tokens
- SEO metadata and accessible navigation
- Static validation updates if needed

## 7. Acceptance Criteria

- [ ] Website pages implement the approved Figma layout.
- [ ] Pages are responsive across mobile and desktop.
- [ ] Copy is in `pt-BR` and stays within MVP product boundaries.
- [ ] Login/product entry links are present as configured placeholders or static links for Task 029 to wire.
- [ ] Website remains deployable as static assets.
- [ ] Relevant tests or static validations are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Run `npm run lint` in `website/`.
- Add static checks if the website package supports them.

### Manual Verification
Open landing, pricing, and about/trust pages at desktop and mobile widths. Verify visual alignment to Figma, link presence, semantic heading order, metadata, logo rendering, and responsive text fit.

## 9. Risks and Edge Cases

### Risks
- Implementing pixel-perfect Figma details could add brittle CSS if the design is not adapted for static HTML.
- Marketing copy could drift from business rules during layout implementation.

### Edge Cases
- Long Portuguese CTA or plan text may wrap unexpectedly on small screens.
- Missing final domain values may require temporary environment-based links.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
