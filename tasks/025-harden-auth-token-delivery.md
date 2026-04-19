# Task 025: Harden Authentication Token Delivery

## 1. Overview

### Objective
Resolve OI-007 by moving the authenticated app away from `sessionStorage`-based token storage to a hardened delivery strategy that is safe to ship to production.

### Why This Matters
Task 012 shipped the authenticated React app with access and refresh tokens stored in `sessionStorage`. This was an explicit interim decision. Any XSS vulnerability in the SPA would expose both the access token and the refresh token, granting persistent account access to an attacker. This must be hardened before production rollout and before the end-to-end release readiness pass in Task 015.

### Task Type
- Full Stack

### Priority
- High

## 2. Context

### Product Context
DeskAI handles sensitive medical data. Authentication tokens are the keys to the entire consultation workflow. The MVP must treat token theft as a realistic threat and adopt industry-standard browser token handling before release.

### Technical Context
- `app/src/auth/sessionStorage.ts` stores `{ accessToken, refreshToken, expiresAt }` under `deskai.auth.session` in `sessionStorage`.
- Access tokens are passed to the API client via `Authorization: Bearer`.
- `AuthContext` restores the session on app mount and clears it on sign-out.
- The BFF currently returns Cognito tokens in the JSON body via `POST /v1/auth/login`.
- Cognito tokens live ~1 hour (access) and up to 30 days (refresh), depending on pool config.

### Related Systems
- Frontend authenticated app
- BFF layer
- HTTP API (auth endpoints)
- Cognito user pool
- CloudFront / API Gateway CORS and cookie policy

### Dependencies
- `005-implement-authentication-and-plan-access-control.md`
- `012-build-authenticated-react-app.md`
- `020-fix-authenticated-app-polish-copy-and-logo.md`

This task must land **before** Task 014 (security hardening pass) and Task 015 (release readiness).

### Required Reading
- `docs/mvp-business-rules.md` (auth and privacy rules)
- `docs/mvp-technical-specs.md` (Sections on auth, BFF, and CORS)
- `docs/architecture/03-contract-inventory.md`
- `docs/requirements/04-failure-behavior-matrix.md`
- `contracts/http/auth.yaml`

## 3. Scope

### In Scope
- Adopt a hybrid token strategy:
  - **Refresh token**: `HttpOnly; Secure; SameSite=Strict` cookie, path-scoped to the auth refresh endpoint, never accessible to JavaScript.
  - **Access token**: held in memory only (React context / closure), not persisted to `sessionStorage` or `localStorage`.
- Add a BFF endpoint `POST /v1/auth/refresh` that reads the refresh token from the cookie, calls Cognito, and returns a new access token in the JSON body (memory-only on the client).
- Update `POST /v1/auth/login` to set the refresh cookie (Set-Cookie) and return only the access token + expiry in the body.
- Update `POST /v1/auth/logout` to revoke the Cognito refresh token and clear the cookie.
- Update frontend `AuthContext` to:
  - Request a fresh access token via `/v1/auth/refresh` on app mount.
  - Silent-refresh before access token expiry.
  - Drop all `sessionStorage` token persistence.
- Update the API client to handle 401 by attempting a single silent refresh before surfacing the failure.
- Update CORS and CloudFront configuration to allow credentialed requests from the app origin only.
- Update `contracts/http/auth.yaml` with the new `refresh` endpoint and Set-Cookie response shape.
- Add contract tests and browser integration tests for cookie behavior, silent refresh, and sign-out.

### Out of Scope
- Replacing Cognito with a different identity provider.
- Changing the email+password-only business rule.
- Adding social/SSO login (explicitly forbidden by business rules).
- Migrating the public website (`website/`) — it has no auth.
- Changing consultation or review business logic.

## 4. Requirements

### Functional Requirements
- The refresh token never appears in JavaScript-accessible storage or the DOM.
- The access token is rehydrated on app reload via the refresh cookie without the user re-entering credentials, while the refresh cookie is still valid.
- Silent refresh succeeds at least once before the access token expires during normal use.
- Explicit sign-out clears the cookie and revokes the refresh token at Cognito.
- A cross-site request from any other origin cannot trigger a refresh (SameSite=Strict enforced).
- Login and logout flows remain pt-BR and visually unchanged for the user.

### Non-Functional Requirements
- Cookie attributes are `HttpOnly; Secure; SameSite=Strict; Path=/v1/auth` (or a narrower safe path).
- Cookie max-age aligns with Cognito refresh token validity.
- No token value is ever logged.
- The new endpoint is rate-limited where appropriate.
- CORS is configured with `Access-Control-Allow-Credentials: true` and an explicit allow-list of origins (no wildcards).

### Business Rules
- Authentication remains email + password only via Cognito.
- Plan-based access control continues to be enforced.
- Physician ownership and clinic scope are unchanged.

### Technical Rules
- Frontend must remain presentation-focused; no security logic beyond token lifecycle coordination.
- Backend/BFF owns cookie issuance, validation, and revocation.
- Strict TDD: contract tests first, then backend handler tests, then frontend tests.

## 5. Implementation Notes

### Proposed Approach
1. Write failing contract tests for the new `/v1/auth/refresh` endpoint and for Set-Cookie on login.
2. Implement the BFF refresh endpoint and update login/logout handlers.
3. Configure cookie policy on API Gateway and CloudFront. Validate in `dev`.
4. Rewrite `AuthContext` and the API client to drop `sessionStorage` and rely on refresh + memory.
5. Delete `app/src/auth/sessionStorage.ts` and its tests.
6. Add browser-level tests for refresh-on-mount, silent refresh, and sign-out clearing.
7. Deploy to `dev` and do a manual verification pass.
8. Update `docs/mvp-technical-specs.md` and `contracts/http/auth.yaml`; close OI-007.

### AWS / Infrastructure Notes
- Ensure CloudFront forwards the `Cookie` header to API Gateway for the auth paths only.
- Ensure API Gateway stage variables and CORS include credentials appropriately.
- Consider a distinct API Gateway route or Lambda for `/v1/auth/refresh` to keep permissions narrow.

### Backend Notes
- `authenticate` use case response should be split: return `{ access_token, expires_in }` in the body and set the cookie at the handler level.
- `sign_out` use case should accept the refresh token from the cookie and revoke it at Cognito.
- Add explicit unit tests for cookie parsing and generation helpers.

### Frontend Notes
- Remove `sessionStorage` helpers and their tests.
- Add a `useSilentRefresh` hook that runs on mount and on a timer before expiry.
- Ensure `fetch` requests use `credentials: 'include'` for auth endpoints only.

## 6. Deliverables
- Updated `auth.yaml` contract
- BFF `/v1/auth/refresh` endpoint + handler + use case
- Updated login/logout handlers with cookie behavior
- Frontend `AuthContext` rewrite + API client refresh handling
- Removed `sessionStorage.ts` and its dependencies
- CORS, CloudFront, API Gateway configuration updates
- Contract tests, BFF tests, and frontend tests
- Documentation updates (technical specs, ADR entry if needed, decision log)
- OI-007 marked resolved in `tasks/@task-manager.md`

## 7. Acceptance Criteria
- [ ] No auth token values are ever written to `localStorage` or `sessionStorage`.
- [ ] `/v1/auth/login` sets a `HttpOnly; Secure; SameSite=Strict` refresh cookie.
- [ ] `/v1/auth/refresh` returns a new access token when the cookie is valid, and 401 otherwise.
- [ ] The app reloads without the user re-entering credentials while the cookie is valid.
- [ ] Silent refresh runs before access token expiry and does not interrupt user flow.
- [ ] Sign-out clears the cookie and revokes the refresh token at Cognito.
- [ ] CORS and CloudFront allow credentialed requests from the authenticated app origin only.
- [ ] Contract, backend, and frontend tests cover the new flow.
- [ ] OI-007 is marked resolved in the task manager.

## 8. Testing

### Required Tests
- Contract tests for `/v1/auth/login`, `/v1/auth/logout`, `/v1/auth/refresh`.
- BFF/unit tests for cookie issuance and parsing helpers.
- Integration/contract tests for `Set-Cookie` headers and `credentials: include` behavior.
- Frontend tests for silent refresh, mount-time rehydration, 401 handling, and sign-out flow.
- Regression tests proving tokens never land in browser storage.

### Manual Verification
- Log in, reload the app, confirm no login prompt until cookie expiry.
- Let access token expire; confirm silent refresh is invisible to the user.
- Log out; confirm cookie is cleared and protected routes redirect to login.
- Open DevTools → Application → Storage → confirm no tokens present anywhere.

## 9. Risks and Edge Cases

### Risks
- Cookie misconfiguration could break authentication across environments.
- Browser cookie policies (Safari ITP, Chrome third-party cookie changes) could affect behavior if origins differ. Mitigation: keep app and API on the same registrable domain or explicitly configure.
- Silent refresh race during concurrent API calls.

### Edge Cases
- The refresh cookie expires mid-session.
- The user opens a second tab; both perform silent refresh concurrently.
- Clock skew between client and server near token expiry.
- A 401 response during an in-flight request that needs automatic retry after refresh.

## 10. Definition of Done
- [ ] Implementation is complete.
- [ ] Acceptance criteria are met.
- [ ] Tests pass (`make test`, `make lint`, frontend test suite).
- [ ] No obvious regressions were introduced.
- [ ] Logs, metrics, and error handling were considered.
- [ ] Security review performed.
- [ ] Documentation and decision log updated.
- [ ] Task is ready for review or merge.
