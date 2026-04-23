# Task 027: Create Sales Website Figma Design

## 1. Overview

### Objective
Create the public sales website design in Figma using the Codex Figma Plugin and the website design tokens produced by Task 026.

### Why This Matters
The sales website should be designed deliberately before implementation, with a reusable visual direction that matches the authenticated app and keeps MVP claims accurate.

### Task Type
- Frontend

### Priority
- High

## 2. Context

### Product Context
The design must help Brazilian physicians quickly understand Notter's documentation-support workflow, review requirement, plan positioning, and login/start path.

### Technical Context
The public website is static HTML/CSS. Figma is the design source for the next implementation task, but code remains in `website/`.

### Related Systems
- Public website
- Figma
- Frontend app

### Dependencies
- `026-create-sales-website-design-system.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `website/README.md`

## 3. Scope

### In Scope
- Use the Codex Figma Plugin to create desktop and mobile designs for the public website.
- Apply the website token mapping from Task 026 for colors, spacing, radius, typography scale, and logo usage.
- Design at least the landing page, pricing/plan section, trust/product-boundary section, and login/product entrypoints.
- Include public-facing Notter branding and domain/link placeholders without internal DeskAI renames.
- Capture Figma implementation notes needed by Task 028.

### Out of Scope
- Implementing HTML/CSS.
- Adding interactive API behavior.
- Creating non-MVP marketing automation, CRM, or lead-routing flows.
- Presenting clinical recommendations, diagnosis, prescription, or autonomous medical behavior.

## 4. Requirements

### Functional Requirements
- The Figma design must include responsive desktop and mobile layouts.
- The design must include clear CTA states for login and product entry.
- The design must include sections for value proposition, product boundaries, plan positioning, and trust messaging.
- The design must use `pt-BR` user-facing text.

### Non-Functional Requirements
- The design must be implementable as static HTML/CSS with minimal JavaScript.
- Layouts must avoid text overlap and support realistic Portuguese copy lengths.
- Visual assets must support SEO-oriented static pages rather than SPA-only behavior.

### Business Rules
- The website must frame Notter as a physician-reviewed documentation tool.
- The design must not advertise social login, SSO, automatic diagnoses, automatic prescriptions, or autonomous clinical decisions.
- The initial target user is a physician in Brazil.

### Technical Rules
- Use the Figma plugin workflow for canvas creation and updates.
- Reuse prior tokens and Notter logo assets.
- Keep Figma naming and implementation notes in English, while visible product copy remains `pt-BR`.

## 5. Implementation Notes

### Proposed Approach
Load the Figma workflow skill before using Figma tools. Create a page or frame set for the public sales website, define styles from the Task 026 token mapping, then build desktop and mobile frames with component-like sections that can be translated directly into static HTML.

### AWS / Infrastructure Notes
- No AWS changes are expected.

### Backend Notes
- No backend changes are expected.

### Frontend Notes
- Favor simple full-width bands and unframed layouts over nested cards.
- Use real Notter logo assets or exported equivalents where the Figma workflow supports them.

## 6. Deliverables

The task should produce:
- Figma public website desktop layout
- Figma public website mobile layout
- Figma style/token mapping based on Task 026
- Implementation notes for Task 028

## 7. Acceptance Criteria

- [ ] Figma designs exist for desktop and mobile public website layouts.
- [ ] Designs use Task 026 colors, spacing, radius, typography, and Notter logo guidance.
- [ ] Visible copy is in `pt-BR` and respects MVP medical-product boundaries.
- [ ] Login/product entrypoints are represented clearly.
- [ ] Implementation notes identify the frames/sections Task 028 should build.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- No code tests are required unless repository files are changed.

### Manual Verification
Review Figma desktop and mobile frames for visual alignment with the authenticated app, copy accuracy, responsive feasibility, CTA clarity, and absence of unsupported product claims.

## 9. Risks and Edge Cases

### Risks
- A Figma layout could become too expressive or complex for the static website constraint.
- Marketing copy could overpromise clinical behavior outside MVP boundaries.

### Edge Cases
- Domain names may still be placeholders if final Notter domains are not purchased or configured yet.
- Some plan details may need to stay general if pricing is not final.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass if code changed.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
