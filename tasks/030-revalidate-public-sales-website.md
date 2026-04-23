# Task 030: Revalidate Public Sales Website

## 1. Overview

### Objective
Perform the wrap-up validation pass for the public sales website, covering design fidelity, content accuracy, entry flows, responsiveness, SEO, accessibility, performance, and deployment readiness.

### Why This Matters
The public website is user-facing and claims-sensitive. Before moving to token hardening and release readiness, the website must be checked as a complete product surface rather than as isolated design or implementation pieces.

### Task Type
- QA

### Priority
- High

## 2. Context

### Product Context
The site must accurately introduce Notter to physicians in Brazil and guide them to the authenticated product without overpromising clinical behavior.

### Technical Context
This is the final validation task after design system, Figma design, interface implementation, and integration work. It should close the public website delivery loop and update the tracker with any remaining open issues.

### Related Systems
- Public website
- Frontend app
- Backend API
- AWS CloudFront
- CI/CD

### Dependencies
- `029-integrate-sales-website-entry-flows-and-javascript.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/requirements/03-plan-entitlements.md`
- `website/README.md`
- `app/README.md`

## 3. Scope

### In Scope
- Revalidate visual alignment against the Figma design and Task 026 design system.
- Verify website copy against MVP business boundaries and `pt-BR` language requirements.
- Verify entry links, lightweight JavaScript behavior, SEO metadata, accessibility, and responsive layouts.
- Validate public-facing Notter branding/domains and internal DeskAI naming boundary.
- Run website validation commands and any affected frontend/backend checks.
- Update task status, documentation, or open issues based on findings.

### Out of Scope
- New feature implementation beyond defects found during validation.
- Auth token hardening work owned by Task 025.
- Observability/security hardening work owned by Task 014.
- Release-wide end-to-end readiness owned by Task 015.

## 4. Requirements

### Functional Requirements
- The website must expose working public pages and entry links.
- The site must remain usable without JavaScript for core content and navigation links where practical.
- CTA behavior must match the configured app entry flow.

### Non-Functional Requirements
- Pages must be responsive, accessible, SEO-friendly, and performant.
- Validation must include mobile and desktop checks.
- Any remaining domain/configuration gaps must be explicitly tracked.

### Business Rules
- Public copy must describe documentation support and physician review, never autonomous clinical decision-making.
- The website must not advertise social login, SSO, automatic diagnoses, or automatic prescriptions.
- User-facing public content must be in Brazilian Portuguese.

### Technical Rules
- Run existing project validation commands before marking the task done.
- Keep the public website static and separate from the authenticated React app.
- Preserve internal DeskAI technical identifiers.

## 5. Implementation Notes

### Proposed Approach
Use a checklist-style validation pass. Start with automated checks, then manually inspect local pages across responsive widths and compare to Figma. Fix defects that are clearly within the public website scope; record larger follow-ups in the task manager.

### AWS / Infrastructure Notes
- Verify whether Notter domains are configured and reachable for `dev`/`prod`.
- If domains are not fully ready, record the exact remaining DNS/ACM/CloudFront action in Open Issues.

### Backend Notes
- Confirm no sensitive data is exposed through any public integration.

### Frontend Notes
- Check text wrapping, focus states, keyboard navigation, reduced-motion behavior, metadata, and link destinations.

## 6. Deliverables

The task should produce:
- Validation fixes if needed
- Updated documentation/checklist notes
- Updated task manager status and open issues
- Evidence of automated and manual verification

## 7. Acceptance Criteria

- [ ] Public website design is revalidated against Figma and website tokens.
- [ ] Public copy is accurate, `pt-BR`, and within MVP boundaries.
- [ ] Entry links, JavaScript interactions, and responsive layouts are verified.
- [ ] SEO, accessibility, and performance basics are checked.
- [ ] Public Notter domain/branding status is verified or remaining gaps are tracked.
- [ ] Relevant tests are added or updated.
- [ ] Documentation is updated if behavior or setup changed.

## 8. Testing

### Required Tests
- Run `npm run lint` in `website/`.
- Run any affected app/backend/infra tests if the validation fixes touch those areas.
- Run static accessibility/SEO checks if tooling is available in the website package.

### Manual Verification
Open the site locally on desktop and mobile widths. Verify landing, pricing, and about/trust pages; CTA links; keyboard navigation; no layout overlap; Notter branding; metadata; and compliance with the report-only product boundary.

## 9. Risks and Edge Cases

### Risks
- Validation could uncover scope that belongs in security hardening or release readiness rather than the public website tasks.
- Domain readiness may depend on external purchase or DNS access.

### Edge Cases
- If a public domain is not reachable yet, document the exact missing dependency instead of marking the website behavior as implemented.
- If Figma and implementation disagree, prioritize product rules, accessibility, and static-site maintainability.

## 10. Definition of Done

- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass.
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security and permissions were reviewed if relevant.
- [ ] Task is ready for review or merge.
