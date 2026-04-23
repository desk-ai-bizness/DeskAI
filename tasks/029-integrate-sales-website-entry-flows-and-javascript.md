# Task 029: Integrate Sales Website Entry Flows And JavaScript

## 1. Overview

### Objective
Wire the public sales website entrypoints, lightweight JavaScript behavior, and allowed API/config integrations needed for the static Notter website.

### Why This Matters
The website must do more than look finished: physicians need reliable navigation into the authenticated app, and lightweight interactions must work without moving business logic into the public frontend.

### Task Type
- Full Stack

### Priority
- High

## 2. Context

### Product Context
Visitors should be able to understand the product, move to login, and follow the intended product entry path without seeing unsupported auth choices or clinical claims.

### Technical Context
The website uses `website/assets/js/main.js` for minimal JavaScript. The authenticated app owns login and product workflows. Public website integrations must use existing configuration or explicitly defined public endpoints only.

### Related Systems
- Public website
- Frontend app
- Backend API
- Authentication
- AWS CloudFront

### Dependencies
- `028-build-sales-website-interface-from-figma.md`
- `005-implement-authentication-and-plan-access-control.md`
- `012-build-authenticated-react-app.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `website/README.md`
- `app/README.md`

## 3. Scope

### In Scope
- Wire website CTA and login links to the authenticated app entrypoints for local, `dev`, and `prod` contexts.
- Add minimal JavaScript for navigation menu behavior and other Figma-approved lightweight interactions.
- Add configuration for public website app URLs and public-facing Notter domain placeholders/values.
- If an API integration is required, use only existing public-safe endpoints or create a separately tested, explicitly scoped endpoint.
- Update public metadata and links to use the public Notter brand while preserving internal DeskAI identifiers.
- Cover JavaScript and configuration behavior with tests or static validation where practical.

### Out of Scope
- Implementing authenticated product workflows in the public website.
- Adding social login, SSO, CRM automation, chat widgets, or unsupported lead-capture behavior.
- Logging or transmitting sensitive health information from public pages.
- Broad internal DeskAI renaming.

## 4. Requirements

### Functional Requirements
- Login and product entry CTAs must route to the authenticated app entrypoints.
- Mobile navigation and lightweight interactive elements must work without a heavy client framework.
- Environment-specific app URLs must be configurable rather than hardcoded in scattered markup.
- Any API usage must handle failure visibly or degrade safely.

### Non-Functional Requirements
- JavaScript must remain small, optional, and non-essential for SEO content.
- Link configuration must avoid leaking tokens, PII, or consultation data.
- Public domain changes must keep deployment risk low.

### Business Rules
- Authentication remains email + password only.
- Public content must not advertise clinical decision-making, social login, or unsupported integrations.
- The public website must operate in Brazil and use `pt-BR` visible content.

### Technical Rules
- Keep frontend behavior presentation-oriented.
- Do not put business rules in website JavaScript.
- Keep internal repository, package, stack, environment, and variable names on `DeskAI`; only public-facing branding/domains should use Notter.

## 5. Implementation Notes

### Proposed Approach
Centralize app-entry URLs in a small website config pattern, then update CTA links and JavaScript to read from that source. Keep menu interactions progressive-enhancement friendly. If a backend endpoint is truly needed, define the contract and write failing tests before implementation.

### AWS / Infrastructure Notes
- Coordinate with OI-019: choose or confirm public Notter website/app domains, ACM/CloudFront/DNS needs, and config values.
- Preserve internal CDK and AWS resource naming unless a future dedicated migration task says otherwise.

### Backend Notes
- Prefer no backend changes.
- If backend work is unavoidable, add tests first and limit the endpoint to public-safe metadata or configuration.

### Frontend Notes
- Confirm links for local development and deployed `dev`/`prod`.
- Ensure menu toggles, keyboard interactions, and reduced-motion behavior are accessible.

## 6. Deliverables

The task should produce:
- Wired CTA/login/product entry links
- Minimal JavaScript interactions
- Website app URL/domain configuration
- Public Notter metadata/link updates
- Tests or static validation for integration behavior

## 7. Acceptance Criteria

- [ ] Website CTAs route to the correct authenticated app entrypoints by environment.
- [ ] Minimal JavaScript interactions work and degrade safely.
- [ ] Public-facing URLs and metadata use the Notter brand where configured.
- [ ] Internal DeskAI technical identifiers remain unchanged.
- [ ] No unsupported auth, clinical, CRM, or sales automation behavior is introduced.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Run `npm run lint` in `website/`.
- Add JavaScript unit/static tests if the website test tooling supports them; otherwise add deterministic static validation scripts only if needed.
- Run affected backend tests first if any endpoint is added or changed.

### Manual Verification
Open the public website locally, test desktop and mobile navigation, verify CTA destinations, confirm keyboard access for menus, and verify Notter public URLs/metadata while internal DeskAI identifiers remain unchanged.

## 9. Risks and Edge Cases

### Risks
- API integration could accidentally create new product behavior not covered by MVP rules.
- Domain changes could be mixed with internal renaming and increase infrastructure risk.

### Edge Cases
- Final Notter domains may not be purchased/configured yet; links should support clear placeholders or environment configuration.
- JavaScript may fail to load; core content and CTA links should remain usable.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
