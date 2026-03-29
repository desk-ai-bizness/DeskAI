# Task 005: Implement Authentication And Plan Access Control

## 1. Overview

### Objective
Implement MVP authentication and backend-enforced authorization using Cognito native email/password flows and plan-aware access control.

### Why This Matters
Identity and access control are foundational for all product flows. The MVP cannot expose consultation data, review actions, or plan-specific capabilities without authenticated and authorized access checks.

### Task Type
- Security

### Priority
- Critical

## 2. Context

### Product Context
Physicians must sign in with email and password only. Each doctor client belongs to a plan, and access may vary by plan. Consultation data must only be visible within the correct clinic context.

### Technical Context
This task builds the auth contract between Cognito, the BFF, the core backend, and the frontend session model. Authorization logic must live in backend or BFF layers, never only in the client.

### Related Systems
- AWS
- Backend API
- Frontend app
- Authentication

### Dependencies
- `004-provision-aws-foundation-with-cdk.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/02-backend-architecture.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/03-plan-entitlements.md`
- `docs/requirements/04-failure-behavior-matrix.md`

## 3. Scope

### In Scope
- Configure Cognito native users with email verification, forgot password, and reset password.
- Implement BFF auth session handling and authenticated user profile retrieval.
- Define doctor, clinic, and plan claims or lookup strategy used for authorization.
- Implement backend or BFF middleware for clinic-aware and plan-aware access control.
- Define account status handling and unauthorized/forbidden responses.

### Out of Scope
- Social login, SSO, or enterprise federation.
- Full clinic admin panel for user management.
- Fine-grained billing workflows beyond plan-aware enforcement.

## 4. Requirements

### Functional Requirements
- Users must be able to authenticate with email and password only.
- The system must support email verification and password reset.
- The system must know the authenticated doctor’s clinic context and plan type.
- Protected endpoints must reject unauthenticated access and enforce authorization rules consistently.
- The system must provide a reliable `me`-style payload for the frontend.

### Non-Functional Requirements
- Sensitive tokens should be handled securely and not rely on insecure persistent browser storage when avoidable.
- Auth implementation should minimize custom complexity where Cognito managed flows are sufficient.
- Access control decisions must be auditable and testable.

### Business Rules
- No Google, Facebook, Apple, or other social login options are allowed in the MVP.
- Supported plan types are `free_trial`, `plus`, and `pro`.
- Access to consultation data must be limited to authorized users within the correct clinic context.

### Technical Rules
- Cognito user pool native auth is the preferred default.
- Authorization must be enforced in backend or BFF layers.
- Frontend must not be the source of truth for permission checks.

## 5. Implementation Notes

### Proposed Approach
Use Cognito for identity and session issuance, then resolve doctor, clinic, and plan context in the BFF or backend through verified claims and profile lookups. Centralize authorization checks in reusable middleware or service policies.

### AWS / Infrastructure Notes
- Configure Cognito user pool, client settings, callback/logout URLs, password policy, and verification behavior.
- Store any app secrets or custom integration details in Secrets Manager.

### Backend Notes
- Implement auth guards, request context resolution, and plan access helpers.
- Return consistent error codes for unauthenticated and unauthorized access.

### Frontend Notes
- Expose only frontend-safe session information and capability flags.
- Keep login UX and token handling aligned with secure browser flows.

## 6. Deliverables

The task should produce:
- Cognito authentication configuration
- BFF auth endpoints or integration glue
- Authorization middleware or policy layer
- Session and current-user contracts
- Auth documentation

## 7. Acceptance Criteria

- [ ] Users can sign in with email and password and complete verification and reset flows.
- [ ] Protected APIs reject unauthenticated requests and enforce clinic and plan rules.
- [ ] The system returns a current-user payload with doctor and plan context.
- [ ] No social or federated login paths are exposed.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for authorization decisions
- Integration tests for auth-protected endpoints

### Manual Verification
Sign in as a valid user, confirm authorized access to allowed resources, confirm rejection outside the clinic context, and verify reset-password and email-verification behavior.

## 9. Risks and Edge Cases

### Risks
- Leaky authorization logic could expose PHI across clinic boundaries.
- Over-customizing auth flows could add avoidable complexity.

### Edge Cases
- A user exists in Cognito but has no active doctor profile mapping.
- A doctor’s plan changes while a session is still active.
- An account is disabled after a valid session is issued.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
