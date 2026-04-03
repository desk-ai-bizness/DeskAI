# DeskAI Deep Code Audit Report v2

**Date**: 2026-04-03
**Auditor**: 7 parallel agents + lead auditor (Claude Opus 4.6)
**Repository**: desk-ai-bizness/DeskAI
**Commit**: 75715f2

---

## Executive Summary

- **Total findings**: 217
- **CRITICAL: 15** | **HIGH: 52** | **MEDIUM: 73** | **LOW: 52** | **INFO/PASS: 25**
- **5 confirmed runtime bugs** that will crash production deployments
- **Delta from v1**: ~50 v1 findings resolved, ~120 new findings, ~38 persisting/partially fixed

### Top 10 Most Urgent Issues

1. **CRITICAL: KMS `secrets_key` not granted to Lambda** — every Secrets Manager read crashes with `AccessDeniedException` (T6-I3)
2. **CRITICAL: Missing `consultation-session-index` GSI** — session queries crash with `ValidationException` (T6-I5)
3. **CRITICAL: `DESKAI_WEBSOCKET_URL` defaults to localhost in Lambda** — real-time streaming broken (T6-I15)
4. **CRITICAL: Zero DynamoDB error handling across ALL 6 repositories** — any AWS throttle/network error crashes the app (T5-A5-1/2/3)
5. **CRITICAL: No plan entitlement enforcement on consultation creation** — free-trial users get unlimited consultations (T5-U6-1)
6. **CRITICAL: `validate_ws_token()` does not exist** — WebSocket $connect always crashes with `AttributeError` (T5-H7-2)
7. **CRITICAL: SNS alerts topic has zero subscribers** — all monitoring is deaf (T6-I27)
8. **CRITICAL: CloudFront no custom domains vs CORS** — API calls blocked from CDN (T6-I38)
9. **HIGH: MFA disabled for health data application** — LGPD/HIPAA non-compliance (T6-I9)
10. **HIGH: AI prompts are 10-line placeholders with no injection defenses** — core AI pipeline non-functional (T6-PR1-PR5)

---

## v1 Finding Status

### v1 CRITICAL Findings (8 total)

| v1 # | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | Missing `patients.yaml` | **FIXED** | Now 3,109B with full schemas |
| 2 | Incomplete `consultations.yaml` | **FIXED** | Now 12,439B |
| 3 | Missing session endpoint contracts | **FIXED** | In consultations.yaml |
| 4 | Skeletal `review.yaml`/`exports.yaml` | **FIXED** | 7,416B/2,111B |
| 9 | Missing DEC entries for ADRs 009-014 | **FIXED** | DEC entries present |
| 12 | Missing `operationId` on non-auth contracts | **FIXED** | All endpoints have operationIds |
| 13 | Missing `components.schemas` | **FIXED** | Full schemas defined |
| 14 | No `security` declarations on protected endpoints | **FIXED** | bearerAuth on all protected endpoints |

### v1 HIGH Findings — Key Status

| v1 # | Description | Status | Notes |
|------|-------------|--------|-------|
| 5 | Skeletal `ui-config.yaml` | **FIXED** | Strict schemas, `additionalProperties: false` |
| 15 | No error response definitions | **FIXED** | 400/401/404/409 on most endpoints |
| 24 | No guard condition docs on lifecycle | **FIXED** | Lifecycle doc complete |
| 25 | Missing `ConsultationDetailView` | **FIXED** | Full view in consultations.yaml |
| 26 | Duplicate Task 007 in priority queue | **FIXED** | Resolved |
| 34 | Audit logging not implemented | **PARTIALLY_FIXED** | Domain entity + adapter exist, but no service logic |
| 48 | CLAUDE.md vs implementation-prompt.md conflict | **PERSISTS** | Actually WORSE — 3 files, 2 orderings |
| 79 | 21 modules zero test coverage | **PARTIALLY_FIXED** | ~61% file coverage now, but critical modules (AI, review, export) still 0% |
| 81 | No integration tests | **PERSISTS** | Still only 1 trivial integration test |
| 83 | Empty conftest.py | **FIXED** | 219 lines with 9 fixture factories |

**Summary**: ~50 of 88 actionable v1 findings FIXED. 38 PERSIST or PARTIALLY_FIXED. The contract and documentation gaps were well addressed; the backend code quality and test coverage gaps remain.

---

## Phase 0: Repository Hygiene

*18 findings — see `/tmp/DeskAI-audit/t1-repo-hygiene.md` for full details*

| # | Severity | File/Path | Issue |
|---|----------|-----------|-------|
| 001 | HIGH | `.DS_Store` | Tracked in git despite `.gitignore` listing — needs `git rm --cached` |
| 002 | HIGH | `.poc-frontend/` | 12.3 MB unreferenced PNGs bloating repo permanently |
| 003-004 | MEDIUM | `app/tsconfig.*.tsbuildinfo` | Build artifacts committed |
| 005-006 | MEDIUM | `**/deskai_*.egg-info/` | Python egg-info dirs committed (backend + infra) |
| 007 | MEDIUM | `app-ci.yml` | No test step — zero frontend test infrastructure |
| 008 | MEDIUM | `infra-ci.yml` | PR trigger has no path filter |
| 009 | LOW | `deploy.yml` | Placeholder exits 0 — should fail loudly |
| 010 | LOW | `CODEOWNERS` | Wildcard `*` only, no path-specific ownership |
| 011 | LOW | `.gitignore` | Missing 6+ patterns (egg-info, tsbuildinfo, poc-frontend, etc.) |
| 014 | MEDIUM | CI pipelines | No contract validation in any CI workflow (NEW) |
| 015 | MEDIUM | CI pipelines | No security scanning — no Dependabot, CodeQL, SAST (NEW) |

---

## Phase 1: Documentation Consistency

*15 findings — see `/tmp/DeskAI-audit/t2-docs.md` for full details*

| # | Severity | Documents | Issue |
|---|----------|-----------|-------|
| 012 | HIGH | `README.md` | 6 local filesystem paths (`/Users/gabrielsantiago/...`) — broken links |
| 013 | MEDIUM | CLAUDE.md / docs/implementation-prompt.md / .ai-utils/ | 3-way reading order conflict |
| 014 | MEDIUM | `ai-context-rules.md` | Missing TDD exemptions (static assets, config) |
| 015-022 | LOW | Various | Stale DEC notes, URL param inconsistency, duplicate impl-prompt |

---

## Phase 2: Contract Validation

*27 findings — see `/tmp/DeskAI-audit/t3-contracts.md` for full details*

| # | Severity | File | Issue |
|---|----------|------|-------|
| 023-025 | HIGH | `review.yaml` | Missing `403` on all 3 review endpoints — authorization gap for medical data |
| 026 | HIGH | `session.yaml` | No `$connect` auth schema for WebSocket |
| 027-031 | MEDIUM | Various | Missing `409` on PUT review, loose `additionalProperties: true` on medical schemas |
| 032 | MEDIUM | All contracts | No `500`/`503` responses defined anywhere |
| 033 | MEDIUM | `screen-schemas.yaml` | `consultation_list` config defined but never served |

---

## Phases 3-4: Domain + Ports

*39 findings — see `/tmp/DeskAI-audit/t4-domain-ports.md` for full details*

### Domain Layer (22 findings)

| # | Severity | Issue |
|---|----------|-------|
| 034-036 | HIGH | 3 mutable aggregate roots (Consultation, Session, NormalizedTranscript) — not `frozen=True` |
| 037 | HIGH | `transition_consultation()` uses `setattr` — bypasses all type checking |
| 038-044 | HIGH | ZERO `__post_init__` validation on ALL 13 frozen dataclasses — invalid state accepted everywhere |
| 045 | HIGH | `SessionState` has 6 states but NO transition enforcement (unlike ConsultationStatus) |
| 046 | MEDIUM | `ArtifactPointer.s3_key` — S3 infrastructure concept in domain |
| 047 | MEDIUM | 4 entire subdomains are empty stubs: ai_pipeline, review, export, config |

**State machine: PASS** — ConsultationStatus: 7/7 states, 9/9 transitions, all forbidden paths blocked.
**Hexagonal imports: PASS** — Zero boto3/AWS imports in entire domain layer.

### Ports Layer (17 findings)

| # | Severity | Issue |
|---|----------|-------|
| 048 | HIGH | `find_by_cognito_sub` — "cognito" leaks into port interface |
| 049-052 | MEDIUM | 4 ports return raw `dict` instead of domain objects |
| 053-056 | HIGH | 4 stub ports (34 bytes): config, event_publisher, export_generator, storage |
| 057 | MEDIUM | Zero async ports — problematic for streaming transcription |

---

## Phases 5-10: Adapters through Container

*49 findings — see `/tmp/DeskAI-audit/t5-adapters-container.md` for full details*

### Top Findings

| # | Severity | Layer | Issue |
|---|----------|-------|-------|
| 058-060 | **CRITICAL** | Adapters | Zero error handling on ALL DynamoDB calls across ALL 6 repositories |
| 061 | **CRITICAL** | Application | No entitlement check on `CreateConsultationUseCase` — unlimited free consultations |
| 062 | **CRITICAL** | Application | `GetConsultationUseCase` has no doctor_id ownership check |
| 063 | **CRITICAL** | Handlers | `validate_ws_token()` does not exist — WebSocket crashes |
| 064 | **CRITICAL** | Handlers | No size limit on WebSocket audio chunk payload |
| 065 | **CRITICAL** | Shared | Dev defaults silently used in production config |
| 066 | HIGH | Adapters | No S3 `ServerSideEncryption` on PHI artifacts |
| 067 | HIGH | Adapters | Expression injection via kwargs in DynamoDB `update_status` |
| 068 | HIGH | BFF | Feature flags hardcoded ignoring plan type |
| 069-072 | HIGH | Container | 4 ports not wired: artifact_repository, event_publisher, export_generator, llm_provider |

---

## Phases 11-13: Prompts + CDK Infrastructure

*47 findings — see `/tmp/DeskAI-audit/t6-prompts-infra.md` for full details*

### AI Prompts (7 findings)

| # | Severity | Issue |
|---|----------|-------|
| 073 | **CRITICAL** | All 3 prompts are 10-line placeholders (~200 bytes) — not production-ready |
| 074 | **CRITICAL** | Missing transcript prompt (only 3 of 4 artifact types) |
| 075-077 | HIGH | No output schema enforcement, no prompt injection defenses, no prompt loading code exists |

### CDK Infrastructure (31 findings) — 5 Confirmed Runtime Bugs

| Bug | Severity | Issue |
|-----|----------|-------|
| #1 | **CRITICAL** | KMS `secrets_key` not granted to Lambda — `AccessDeniedException` on every secret read |
| #2 | **CRITICAL** | SNS alerts topic zero subscribers — monitoring is deaf |
| #3 | **CRITICAL** | CloudFront no custom domains — CORS blocks API calls |
| #4 | **CRITICAL** | Missing `consultation-session-index` GSI — session queries crash |
| #5 | **CRITICAL** | `DESKAI_WEBSOCKET_URL` defaults to localhost in Lambda |

Additional infrastructure findings: MFA off, shared Lambda role, no VPC, no WAF, WebSocket unauthenticated at API Gateway level, `unsafe_plain_text` secrets, no deletion protection on DynamoDB/Cognito/KMS.

### CDK Tests (9 findings)

No security assertions, no negative tests, no prod-config tests. Orchestration/monitoring/CDN tests only count resources.

---

## Phases 14-16: Frontend + Website + Test Coverage

*See `/tmp/DeskAI-audit/t7-frontend-tests.md` for full details*

### Frontend (12 findings)

| # | Severity | Issue |
|---|----------|-------|
| 078 | **CRITICAL** | Zero test files — no test runner configured |
| 079 | **CRITICAL** | No authentication at all — no auth tokens in API calls |
| 080 | HIGH | No 401/403 handling in API client |

**Status**: Skeleton/prototype. 14 TS files, 1 real API call, no routing, no auth.

### Website (10 findings)

No security headers (CSP, X-Frame-Options). Missing meta descriptions, no OG tags. Dead links. Pricing has no actual prices.

### Test Coverage Matrix

| Category | Files | Tested | Coverage |
|----------|-------|--------|----------|
| Domain | 40 | 23 | 57.5% |
| Application | 25 | 16 | 64.0% |
| Adapters | 23 | 15 | 65.2% |
| Handlers | 21 | 14 | 66.7% |
| BFF | 12 | 10 | 83.3% |
| Shared+Container | 7 | 6 | 85.7% |
| **Backend Total** | **128** | **78** | **60.9%** |
| Frontend | 14 | 0 | **0%** |

**570 backend tests + 21 infra tests = 591 total**

**Critical untested modules**: AI pipeline (0 tests), review domain (0 tests), export domain (0 tests), all Step Functions handlers (0 tests), Claude LLM adapter (0 tests), all domain services except transcription (0 tests).

---

## Phase 17: Security Audit

*Cross-cutting findings derived from all agent reports*

| # | Severity | Area | Issue |
|---|----------|------|-------|
| 081 | **CRITICAL** | Authentication | WebSocket `$connect` has no API Gateway authorizer AND `validate_ws_token` method doesn't exist — double failure |
| 082 | **CRITICAL** | Authorization | `GetConsultationUseCase` has no doctor_id check — any doctor in same clinic reads others' consultations |
| 083 | HIGH | MFA | MFA disabled (`cognito.Mfa.OFF`) for medical/PHI application |
| 084 | HIGH | Data at rest | S3 `put_object` calls have no `ServerSideEncryption` directive for PHI |
| 085 | HIGH | Secrets | `SecretValue.unsafe_plain_text("replace-in-aws-secrets-manager")` visible in CFN template |
| 086 | HIGH | Prompt injection | Zero defenses in AI prompts — malicious transcript content could manipulate outputs |
| 087 | HIGH | Token security | Session ID used as WebSocket `connection_token` — guessable, not cryptographically signed |
| 088 | MEDIUM | PHI in logs | `shared/logging.py` warns about PHI but has no programmatic enforcement |
| 089 | MEDIUM | Error exposure | `str(exc)` passed directly to error responses — may leak internal details |
| 090 | MEDIUM | CORS | Properly restrictive (specific domains, no wildcards) — PASS |
| 091 | MEDIUM | Rate limiting | No per-endpoint rate limiting on auth endpoints (login, forgot-password) |
| 092 | LOW | Account ID | AWS account `183992492124` hardcoded in config files |

---

## Phase 18: Architecture Compliance

| # | Severity | Area | Issue |
|---|----------|------|-------|
| 093 | INFO | Hexagonal | Domain layer: ZERO import violations — no boto3/AWS/framework imports |
| 094 | MEDIUM | Layer violation | `application/config/get_ui_config.py` imports from `deskai.bff.ui_config.assembler` — application→BFF dependency |
| 095 | MEDIUM | Business logic leak | `transition_consultation()` uses `setattr` — bypasses frozen dataclass protection |
| 096 | MEDIUM | Dead code | `BffResponse` dataclass, `get_consultation_list_config()`, `fetchConsultations()` — defined but never used |
| 097 | LOW | Naming | Ports use mixed style (docstring vs `...` for abstract body) |
| 098 | LOW | Type safety | `dict[str, Any]` in 4 ports and 2 domain entities — loses type checking |

---

## Phase 19: Cross-Cutting Concerns

| # | Severity | Area | Issue |
|---|----------|------|-------|
| 099 | HIGH | Observability | SNS topic with zero subscribers means ALL alarms fire into void |
| 100 | HIGH | Observability | No Lambda duration/throttle alarms — approaching-timeout invisible |
| 101 | MEDIUM | Idempotency | DynamoDB `put_item` for updates (full overwrite, no optimistic concurrency) |
| 102 | MEDIUM | Pagination | DynamoDB queries don't handle `LastEvaluatedKey` — results silently truncated at 1MB |
| 103 | MEDIUM | Concurrency | No condition expressions on DynamoDB writes — last-write-wins race condition |
| 104 | MEDIUM | Graceful degradation | No fallback if ElevenLabs or Claude API is down — Lambda crashes with unhandled errors |
| 105 | MEDIUM | Cost controls | No reserved concurrency on Lambda — runaway scaling possible |
| 106 | LOW | Build reproducibility | Python deps use `>=` with no upper bounds — breaking changes possible |

---

## Severity Definitions

- **CRITICAL**: Security vulnerability, data loss risk, runtime crash, or blocking correctness issue
- **HIGH**: Significant quality gap, missing tests for implemented code, or architecture violation
- **MEDIUM**: Inconsistency, incomplete implementation, or documentation gap
- **LOW**: Style issue, minor improvement, or optional enhancement
- **INFO/PASS**: Verified correct, no action needed

---

## Recommended Fix Priority

### Tier 1: Fix Immediately (before any new development)

1. **KMS `secrets_key` grant** (Bug #1) — 2-file fix in compute_stack.py + app.py
2. **Add `consultation-session-index` GSI** (Bug #4) — storage_stack.py
3. **Set `DESKAI_WEBSOCKET_URL`** in Lambda environment (Bug #5) — compute_stack.py
4. **Add SNS email subscriber** (Bug #2) — orchestration_stack.py or CLI
5. **Implement `validate_ws_token()`** on CognitoAuthProvider
6. **Add try/except to ALL DynamoDB calls** — create base class with error handling
7. **Add entitlement check** to `CreateConsultationUseCase`
8. **Fix dev defaults in config** — require env vars in prod, no silent fallback

### Tier 2: Fix Before Next Task Completion

9. MFA at minimum OPTIONAL for health data
10. Add `ServerSideEncryption='aws:kms'` to all S3 `put_object` calls
11. Add doctor_id ownership check to `GetConsultationUseCase`
12. Add size limit to WebSocket audio chunk handler
13. Remove `.DS_Store`, `.poc-frontend/`, egg-info, tsbuildinfo from git
14. Fix README local paths
15. Wire feature flags to plan types (not hardcoded)
16. Add custom domains + ACM certificates to CloudFront (Bug #3)
17. Add `__post_init__` validation to critical value objects

### Tier 3: Fix Before Production

18. Per-Lambda IAM roles (least privilege)
19. WAF on both APIs
20. VPC for Lambda functions
21. Production-grade AI prompts (1-5KB with schemas, injection defenses)
22. Prompt loading code + downstream validation
23. Integration tests for DynamoDB adapters (moto)
24. Handler chain tests (Lambda event → handler → use case → mock repo)
25. Cognito deletion protection + advanced security
26. DynamoDB deletion protection
27. Session state machine transition enforcement
28. Separate dev/prod AWS accounts
29. Automated deploy pipeline (replace placeholder deploy.yml)
30. Frontend auth implementation + test framework

### Tier 4: Ongoing Improvement

31. Async ports for streaming operations
32. Domain value objects with validation
33. Frozen entity pattern (return new instances, don't mutate)
34. Standardize documentation reading order (eliminate 3-way conflict)
35. CDK security assertions in tests
36. Negative CDK tests (verify absence of dangerous patterns)
37. S3 access logging
38. Cost budget early warnings (80% threshold)
39. Delete dead code (BffResponse, screen_config, etc.)
40. Frontend accessibility (ARIA, keyboard navigation)

---

*Report compiled from 7 parallel audit agents scanning 475 files across all layers. Individual phase reports available at `/tmp/DeskAI-audit/t{1-7}-*.md`.*
