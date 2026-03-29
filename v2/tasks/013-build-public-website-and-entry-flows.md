# Task 013: Build Public Website And Entry Flows

## 1. Overview

### Objective
Build the public marketing website and entry flows that explain the product, support SEO, and direct users into the authenticated application.

### Why This Matters
The MVP frontend includes both a public website and the logged-in app. The public website must communicate the product clearly, set correct expectations, and avoid misrepresenting the MVP as a clinical decision-maker.

### Task Type
- Frontend

### Priority
- Medium

## 2. Context

### Product Context
The public website introduces the documentation-support value proposition, plan positioning, trust cues, and authenticated entrypoints for physicians.

### Technical Context
The technical specs explicitly call for standard HTML, CSS, and minimal JavaScript to maximize crawlability, performance, and simple deployment.

### Related Systems
- Frontend app
- Authentication
- CI/CD

### Dependencies
- `003-bootstrap-repository-and-engineering-foundation.md`
- `004-provision-aws-foundation-with-cdk.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`

## 3. Scope

### In Scope
- Build the public landing and entry pages using standard HTML and CSS.
- Add login and product entry links that route users into the authenticated flow.
- Define the core marketing copy, plan presentation, and trust messaging for the MVP.
- Ensure the website is optimized for SEO, performance, and responsive layout.

### Out of Scope
- Complex SPA behavior on marketing pages.
- In-app authenticated product workflows.
- Non-MVP sales automation or CRM integrations.

## 4. Requirements

### Functional Requirements
- The website must explain what the product does and does not do.
- The website must present product content in `pt-BR`.
- The website must give users a clear path to log in or start the product flow.
- The website must support future updates to plan messaging without major rewrites.

### Non-Functional Requirements
- Pages should prioritize crawlability and fast load times.
- The site should remain simple to deploy via CloudFront.
- The UX must be responsive across mobile and desktop.

### Business Rules
- The product must be presented as documentation assistance and review support, not as an autonomous clinical system.
- Social login or SSO options must not be advertised.
- The initial target user is a physician in Brazil.

### Technical Rules
- Use standard HTML and CSS with minimal JavaScript only when needed.
- Keep the website separate from the React authenticated app.

## 5. Implementation Notes

### Proposed Approach
Create a small set of static pages with strong information hierarchy, clear calls to action, and copy aligned to the MVP boundaries and plan model.

### AWS / Infrastructure Notes
- Ensure generated assets fit the CloudFront/static hosting path defined in CDK.

### Backend Notes
- Keep public website dependencies on backend services minimal.

### Frontend Notes
- Reuse design tokens or shared visual primitives only if they do not complicate deployment.

## 6. Deliverables

The task should produce:
- Public website pages and assets
- Login and entry routing
- SEO and metadata setup
- Copy aligned with business rules

## 7. Acceptance Criteria

- [ ] Public website pages exist and are deployable as static assets.
- [ ] Product copy clearly describes the MVP as a physician review tool, not a clinical decision-maker.
- [ ] Login or product entry flows connect users to the authenticated app.
- [ ] Pages are responsive and performant.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Static build validation
- Basic accessibility and SEO checks

### Manual Verification
Open the public pages on desktop and mobile, verify copy and navigation, and confirm the login entrypoint routes correctly into the authenticated product flow.

## 9. Risks and Edge Cases

### Risks
- Marketing copy could overpromise functionality outside MVP boundaries.
- Overengineering the public website could distract from core product delivery.

### Edge Cases
- A logged-in user lands on a public page and needs a clear route back into the app.
- Plan messaging changes before launch.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
