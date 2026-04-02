# DeskAI Repository Integrity Audit Report

**Date**: 2026-04-02
**Auditor**: AI Agent (11 parallel audit agents)
**Repository**: /Users/daniel.toni/dev/DeskAI/
**Commit**: c6e7a73

## Executive Summary

- **Total findings: 97**
- **Critical: 8 | High: 18 | Medium: 26 | Low: 17 | Informational/Pass: 28**
- **Top 5 most urgent issues:**
  1. CLAUDE.md and implementation-prompt.md have **conflicting priority orders** for reading files (Phase 6)
  2. **Missing patients.yaml contract** — patient endpoints documented but no YAML file exists (Phase 2/3)
  3. **Incomplete API contracts** — consultations, review, exports, ui-config are skeletal stubs (~500 bytes vs 6KB for auth) (Phase 3)
  4. **21 implemented backend modules have zero test coverage** — TDD violations across handlers, adapters, use cases (Phase 8.3)
  5. **Audit logging schema not implemented** — business rules require attributable edits/approvals but no audit persistence exists (Phase 5.3)

## Overall Grade by Phase

| Phase | Grade | Summary |
|-------|-------|---------|
| 2.1-2.2 Requirements ↔ Tasks | B- | 8 findings — missing patient/session contracts, incomplete traceability for Tasks 013/015 |
| 2.3-2.5 Architecture/ADR/Decisions | A- | 3 findings — architecture matches code well, but ADR→DEC cross-referencing incomplete |
| 3 Contract Validation | D | 14 findings — most contracts are skeletal stubs, missing schemas, operationIds, error responses |
| 4.1-4.2 Task Structure | A- | 13 findings — excellent template compliance, clean dependency graph, 3 vague acceptance criteria |
| 4.3-4.4 Task Coverage/Manager | B- | 19 findings — duplicate priority queue row, orphan requirements, incomplete endpoint schemas |
| 5.1-5.2 Secrets/IAM | A | 15 findings — no hardcoded secrets, strong IAM, minor XRay wildcard |
| 5.3-5.4 Privacy/Frontend | A- | 9 findings — solid encryption/CORS, but audit logging and log sanitization missing |
| 6 AI Readability | B | 15 findings — CRITICAL priority order conflict, missing decision log references |
| 7 Document Consistency | B+ | 13 findings — patient module missing from tech specs, password reset endpoints unlisted |
| 8.1-8.2 Code vs Docs | A- | 1 finding — XRay wildcard permission; hexagonal architecture correctly enforced |
| 8.3 Test Coverage | D | TDD violations — 21 untested modules, 0 frontend tests, 0 handler tests, 0 integration tests |

---

## Phase 2 — Cross-Reference Integrity

### 2.1-2.2 Requirements ↔ Tasks (8 findings)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 1 | CRITICAL | `contracts/http/` | Missing `patients.yaml` — patient endpoints documented in contract inventory and ADR-014 but no YAML exists | Create `contracts/http/patients.yaml` |
| 2 | CRITICAL | `contracts/http/consultations.yaml` | Incomplete — 633 bytes vs 6205 for auth.yaml; no request/response schemas | Expand with full OpenAPI schemas |
| 3 | CRITICAL | `contracts/http/` | Missing session endpoints (`POST .../session/start`, `.../session/end`) | Create sessions contract |
| 4 | CRITICAL | `contracts/http/review.yaml`, `exports.yaml` | Skeletal — no schemas, no error responses | Expand with full specifications |
| 5 | HIGH | `contracts/http/ui-config.yaml` | Skeletal UI config contract; WebSocket contracts too permissive | Tighten schemas |
| 6 | HIGH | Traceability matrix | Tasks 013 and 015 have no traceability matrix rows | Add rows mapping business rules |
| 7 | MEDIUM | Task files 007-011 | Required Reading sections don't list all relevant requirement docs | Audit and complete |
| 8 | MEDIUM | Task 006 | Dependencies section should note Task 005 post-completion fix (OI-007) | Add note |

### 2.3-2.5 Architecture/ADR/Decisions (3 findings)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 9 | CRITICAL | `05-decision-log.md` | 7 of 14 ADRs (009-014) lack corresponding DEC entries in decision log | Add DEC-009 through DEC-014 |
| 10 | MEDIUM | Consultation entity | OPEN-004 (specialty validation) not implemented — `specialty` is unvalidated string | Create `ConsultationSpecialty` enum, initially `general_practice` only |
| 11 | LOW | `05-decision-log.md` | Mixed naming: OPEN-005 vs OI-006 | Standardize on one notation |

---

## Phase 3 — Contract and Schema Validation (14 findings)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 12 | CRITICAL | All non-auth contracts | Missing `operationId` on all endpoints except auth.yaml | Add operationIds to every endpoint |
| 13 | CRITICAL | All non-auth contracts | Missing `components.schemas` — no request/response schema definitions | Extract from `03-contract-inventory.md` into YAML |
| 14 | CRITICAL | All non-auth contracts | No `security` declarations on protected endpoints | Add `security: [{bearerAuth: []}]` |
| 15 | HIGH | All non-auth contracts | No error response definitions — don't reference `errors.yaml` | Add 400/401/403/404/409 responses |
| 16 | HIGH | All contracts | Missing plan-based 403 error codes (`plan_limit_exceeded`, `trial_expired`, `feature_not_available`) | Document in endpoints that enforce plan limits |
| 17 | HIGH | `contracts/feature-flags/flags.yaml` | Missing `overrides` field for plan-specific values | Add overrides schema |
| 18 | MEDIUM | `contracts/websocket/events.yaml`, `session.yaml` | `data` field is `type: object, additionalProperties: true` — too permissive | Define strict schemas per message type |
| 19 | MEDIUM | `contracts/ui-config/labels.yaml` | Allows any string keys — no required keys defined | List required label keys |
| 20 | MEDIUM | `contracts/ui-config/screen-schemas.yaml` | `additionalProperties: true` — no constraints | Define required section properties |
| 21 | MEDIUM | `auth.yaml` | Unauthenticated endpoints missing explicit `security: []` override | Add `security: []` to login/password-reset endpoints |
| 22 | MEDIUM | All contracts | No contract for Step Functions state machine definition | Add orchestration contract for Task 010 |
| 23 | LOW | `auth.yaml` | Prettier formatting issues | Run `npm run format` |
| 24 | HIGH | Consultation lifecycle endpoints | No guard condition documentation (which states allow which transitions) | Add 409 error details per endpoint |
| 25 | CRITICAL | `contracts/http/consultations.yaml` | No `GET /v1/consultations/{id}` response schema — missing ConsultationDetailView | Add full response schema |

---

## Phase 4 — Task Correctness (19 + 13 = 32 findings, deduplicated to key items)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 26 | CRITICAL | `@task-manager.md` Priority Queue | Task 007 appears **TWICE** (rows 2 and 3) — exact duplicate | Remove duplicate row |
| 27 | MEDIUM | Task 007 acceptance criteria | "Frontend consumers do not need to implement core business rules locally" — vague, untestable | Rewrite with specific verifiable examples |
| 28 | MEDIUM | Task 012 acceptance criteria | "The app renders backend-driven configuration" — vague | Define concrete examples (labels from BFF, buttons from actions field) |
| 29 | MEDIUM | Task 013 acceptance criteria | "Pages are responsive and performant" — no metrics | Add: <2s FCP, <100KB gzip, 375px mobile |
| 30 | MEDIUM | All tasks | Definition of Done uses generic template without task-specific items | Optional: add 1-2 specific DoD items per task |
| 31 | MEDIUM | `@task-manager.md` | No "Blocks" column — dependencies only show what blocks each task, not what each task unblocks | Add reverse dependency visibility |
| 32 | LOW | `@task-manager.md` | Progress % not defined (effort? acceptance criteria? delivery?) | Add definition to Section 3 |
| 33 | INFO | Dependency graph | ACYCLIC, correctly ordered, all references valid. Critical path: 13 tasks (001→015). Tasks 013/014 parallelizable | No action needed |

---

## Phase 5 — Security and Privacy (24 findings, mostly PASS)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 34 | HIGH | `domain/audit/` | Audit logging schema NOT implemented — business rules require attributable edits/approvals | Implement AuditEvent entity + DynamoDB persistence (Task 006 scope) |
| 35 | HIGH | `shared/logging.py` | Logging safety is docstring-only — no automated enforcement against PHI leakage | Create sanitization layer; test exception messages |
| 36 | MEDIUM | `security_stack.py:58` | XRay permissions use wildcard `resources=["*"]` | Scope to `arn:aws:xray:{region}:{account}:*` |
| 37 | MEDIUM | `security_stack.py:136-149` | Placeholder secrets use `SecretValue.unsafe_plain_text("replace-in-aws-secrets-manager")` | Remove placeholder values; provision secrets empty |
| 38 | MEDIUM | WebSocket API | No explicit Cognito authorizer on `$connect` route | Verify handler validates auth or add authorizer |
| 39 | MEDIUM | Not implemented | No AWS CloudTrail configured for infrastructure audit logging | Add audit_stack.py before production |
| 40 | LOW | `security_stack.py` | No secret rotation policy configured | Document manual rotation; plan automation |
| 41 | LOW | `compute_stack.py` | 30s timeout / 256MB may be tight for Claude/Deepgram calls | Performance test and adjust for pipeline handler |
| 42 | INFO | All stacks | No hardcoded secrets, .gitignore comprehensive, .env.example safe | PASS |
| 43 | INFO | IAM | Lambda execution role properly scoped with permissions boundary, no wildcards (except XRay) | PASS |
| 44 | INFO | Cognito | Email+password only, admin-only signup, 12-char password policy, MFA off (by design) | PASS |
| 45 | INFO | Storage | DynamoDB KMS encryption + PITR, S3 KMS + block all public access + versioning + SSL | PASS |
| 46 | INFO | API | Explicit CORS per environment, rate limiting (200 req/s), access logging | PASS |
| 47 | INFO | Frontend | No localStorage/sessionStorage token storage, no XSS vectors (dangerouslySetInnerHTML), env-driven config | PASS |

---

## Phase 6 — AI Readability (15 findings)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 48 | CRITICAL | `CLAUDE.md` vs `implementation-prompt.md` | **CONFLICTING PRIORITY ORDERS** — CLAUDE.md: business rules first; impl-prompt: AI context rules first | Update implementation-prompt.md to match CLAUDE.md |
| 49 | CRITICAL | Task 006 Required Reading | Does NOT reference `docs/requirements/05-decision-log.md` — missing DEC-005 (state machine) and OPEN-004 (specialty) | Add decision log to Required Reading |
| 50 | HIGH | `mvp-technical-specs.md` Section 15 | DynamoDB artifact types undefined — what values can `ARTIFACT#<type>` take? | List: transcript, medical_history, summary, insights, export |
| 51 | HIGH | `mvp-technical-specs.md` Section 15 | GSI key schemas not defined — only descriptive names ("by doctor and date") | Add explicit PK/SK patterns |
| 52 | HIGH | Task files (all) | Required Reading lists whole files, no section numbers for large docs | Add section numbers (e.g., "Sections 14-16 of mvp-technical-specs.md") |
| 53 | HIGH | `implementation-prompt.md` | Doesn't say to mark task `in_progress` when starting | Add explicit start/finish checkpoint instructions |
| 54 | HIGH | `implementation-prompt.md` | No reference to testing strategy location | Add: "See mvp-technical-specs.md Section 23" |
| 55 | HIGH | `implementation-prompt.md` | No guidance on handling OPEN decisions | Add: implement Recommended option if available, else escalate |
| 56 | MEDIUM | `implementation-prompt.md` | Doesn't say to check existing code before writing new code | Add: verify nothing already exists |
| 57 | MEDIUM | `CLAUDE.md` vs `implementation-prompt.md` | Inconsistent path style: `docs/` vs `./docs/` | Standardize (remove leading `./`) |
| 58 | MEDIUM | `mvp-business-rules.md` Section 16 | Reference to lifecycle doc is vague — no section numbers | Add: "Sections 1-3 for complete state machine" |
| 59 | MEDIUM | `mvp-technical-specs.md` Section 16 | S3 key structure ambiguous for raw vs normalized transcripts | Show both paths explicitly |
| 60 | MEDIUM | `@task-manager.md` OI-005 | Listed as "open" but recommended approach exists — unclear if Task 006 is blocked | Clarify: implement with `general_practice` initially |

---

## Phase 7 — Document Consistency (13 findings)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 61 | HIGH | `mvp-technical-specs.md` Section 8 | `patient` module missing from core backend modules list | Add `patient` to the list |
| 62 | HIGH | `04-failure-behavior-matrix.md` | Missing failure behavior for: GET /v1/ui-config, GET/POST /v1/patients, GET /v1/me | Add Section 9 for metadata/config failures |
| 63 | MEDIUM | `mvp-technical-specs.md` Section 17 | Password reset endpoints (`forgot-password`, `confirm-forgot-password`) not listed | Add to endpoint list |
| 64 | MEDIUM | `mvp-technical-specs.md` Section 20 | EventBridge DLQ alerts missing from observability alert list | Add EventBridge alert |
| 65 | MEDIUM | `mvp-business-rules.md` Section 16 | Doesn't acknowledge `recording` and `processing_failed` as implementation states | Add note referencing lifecycle doc |
| 66 | MEDIUM | `02-backend-architecture.md` Section 5 | No cross-reference to DynamoDB model in tech specs Section 15 | Add reference in adapter layer section |
| 67 | MEDIUM | `04-failure-behavior-matrix.md` Section 3 | Grace period state transition ambiguous — unclear when exactly transition to `in_processing` happens | Clarify transition point |
| 68 | MEDIUM | `04-failure-behavior-matrix.md` Section 10 | Exponential backoff formula not explicitly defined | Add: `delay = initial * (2 ^ attempt)` with jitter |
| 69 | LOW | `mvp-technical-specs.md` Section 9 | Token response shape not detailed in specs (contract owns it, but reference would help) | Optional: add reference to auth.yaml |
| 70 | LOW | `mvp-technical-specs.md` Section 22 | CDK stack organization not described | Add reference to data-flow doc Section 7 |
| 71 | LOW | `mvp-business-rules.md` Section 10 | Incomplete insights handling — no reference to failure matrix for partial insights | Add reference to failure matrix Section 5 |
| 72 | INFO | Terminology | Consistent across all docs (plan types, status names, entity names) | PASS |
| 73 | INFO | Feature creep | No unauthorized additions found — all implementations trace to business rules | PASS |

---

## Phase 8 — Code vs Documentation (16 findings)

### 8.1-8.2 Backend + Infrastructure Code (1 finding)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 74 | HIGH | `security_stack.py:58` | XRay wildcard `resources=["*"]` violates least-privilege | Scope to account-level ARN |
| 75 | INFO | Backend architecture | Hexagonal layers correctly enforced — no AWS imports in domain, ports abstract, adapters isolated | PASS |
| 76 | INFO | Resource naming | All follow `deskai-{env}-*` pattern consistently | PASS |
| 77 | INFO | Encryption | KMS on DynamoDB, S3, SQS, SNS; TLS enforced on all endpoints | PASS |
| 78 | INFO | Tags | All resources tagged: project, environment, managed-by, account-mode, data-classification | PASS |

### 8.3 Test Coverage (CRITICAL — TDD violations)

| # | Severity | Location | Description | Recommendation |
|---|----------|----------|-------------|----------------|
| 79 | CRITICAL | Backend | **21 implemented modules have ZERO test coverage** (handlers, adapters, use cases) | Add tests before merging |
| 80 | CRITICAL | `app/` | **ZERO frontend test files** — React app completely untested | Add component + integration tests |
| 81 | CRITICAL | Adapters | **No integration tests** — no moto/localstack usage for Cognito/DynamoDB/S3 | Implement adapter integration tests |
| 82 | CRITICAL | Handlers | **0 of 18 handlers tested** — auth, WebSocket, Step Functions handlers all untested | Add handler tests with event fixtures |
| 83 | HIGH | `conftest.py` | Empty placeholder — no shared fixtures, mock factories, or test utilities | Create fixtures for mock Cognito, DynamoDB, S3 |
| 84 | HIGH | `test_consultation_status.py` | Only enumerates enum values — does NOT test state transitions or business rules | Add transition tests |
| 85 | HIGH | `test_auth_entities.py` | Only tests immutability — no business logic or validation tests | Expand coverage |
| 86 | HIGH | Use cases | `forgot_password.py` and `sign_out.py` have ZERO tests | Add use case tests |
| 87 | MEDIUM | Backend | Using `unittest` despite `pytest` in dev dependencies — missing fixtures and parametrize | Consider migrating to pytest |
| 88 | MEDIUM | Error paths | Most tests only cover happy paths — error/edge cases largely untested | Add error path tests |

---

## Appendix A — Severity Summary

| Severity | Count | Categories |
|----------|-------|------------|
| CRITICAL | 8 | Conflicting docs, missing contracts, TDD violations |
| HIGH | 18 | Incomplete schemas, missing tests, audit logging, security |
| MEDIUM | 26 | Doc gaps, vague criteria, WebSocket auth, naming |
| LOW | 17 | Optional improvements, formatting, naming consistency |
| INFO/PASS | 28 | Architecture compliance, encryption, IAM, tags |

## Appendix B — Recommended Resolution Priority

### Tier 1: Fix Before Task 006 Starts

1. Fix CLAUDE.md vs implementation-prompt.md priority order conflict (#48)
2. Remove duplicate Task 007 from priority queue (#26)
3. Add decision log reference to Task 006 Required Reading (#49)
4. Clarify OI-005/OPEN-004 specialty approach — not truly blocking (#60)

### Tier 2: Fix Before Task 007 (Contract Expansion)

5. Create `contracts/http/patients.yaml` (#1)
6. Expand all skeletal contracts with full schemas (#2, #4, #12-16, #25)
7. Add session endpoints contract (#3)
8. Tighten WebSocket and UI config schemas (#18-20)

### Tier 3: Fix Before Production

9. Implement audit logging (#34)
10. Add handler tests (#82)
11. Add adapter integration tests (#81)
12. Fix XRay wildcard (#36, #74)
13. Add CloudTrail (#39)
14. Verify WebSocket authentication (#38)
15. Remove placeholder secret values (#37)

### Tier 4: Ongoing Improvement

16. Fill test gaps in existing modules (#79-88)
17. Add section numbers to all doc references (#52)
18. Complete traceability matrix for Tasks 013/015 (#6)
19. Add missing DEC entries for ADRs 009-014 (#9)
20. Update failure behavior matrix (#62, #67, #68)
