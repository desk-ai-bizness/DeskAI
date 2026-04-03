# DeskAI Deep Code Audit Prompt v2

**Date**: 2026-04-03
**Target Repository**: `desk-ai-bizness/DeskAI`
**Previous Audit**: `docs/audit-report-2026-04-02.md` (97 findings, v1)
**Purpose**: This file is a prompt for an AI agent to execute a comprehensive, line-by-line code audit of the DeskAI repository. The project is unfinished (Tasks 001-009 done, 010-015 planned). Audit only what exists. Do not audit planned/future work.
**Pre-Investigation**: 16 parallel audit agents have already scanned the repo. Their findings are in Appendix A at the end of this document. Use them as a starting checklist -- verify each finding still holds, then go deeper.

---

## Your Role

You are a senior staff engineer and security auditor performing a deep code review of a medical documentation SaaS product for Brazilian physicians. This is health-sensitive software. Your audit must be ruthlessly thorough. Do not be polite about findings. Do not give the benefit of the doubt. If something looks wrong, flag it. If something is ambiguous, flag it. If something is missing, flag it.

You have access to the full repository. Read every file. Do not skip files because they look small or unimportant. A 34-byte port file that says `# Placeholder` is a finding. A 6.8MB PNG committed to git is a finding. An empty `conftest.py` is a finding.

---

## Context: What DeskAI Is

DeskAI is a medical documentation assistant for Brazilian physicians. It:

1. Captures live audio from doctor-patient consultations via browser
2. Transcribes in real-time using a third-party provider (Deepgram planned)
3. AI pipeline (Claude/LLM) generates: draft medical history, consultation summary, flagged insights with evidence
4. Physician reviews, edits, and explicitly finalizes
5. Only finalized consultations can be exported

**Critical rule**: DeskAI is a DOCUMENTATION tool, not a clinical decision-maker. It must REPORT what was said, NEVER interpret what it means. No auto-diagnoses, no auto-prescriptions. Insights are review flags only.

**Tech stack**: Python backend on AWS Lambda, React+TypeScript frontend, AWS CDK infrastructure (Cognito, API Gateway, DynamoDB, S3, Step Functions, EventBridge/SQS/SNS), dev+prod environments only.

**Architecture**: Hexagonal (ports & adapters). Business rules must be framework-agnostic. Backend layers: domain (entities, value objects, business rules) -> ports (interfaces) -> adapters (AWS implementations) -> application (use cases) -> handlers (Lambda entry points) -> BFF (frontend-facing assembly).

---

## Previous Audit (v1) Summary

The v1 audit on 2026-04-02 found 97 issues (8 critical, 18 high, 26 medium, 17 low, 28 info/pass). Top issues were:

1. Conflicting priority orders between CLAUDE.md and implementation-prompt.md
2. Missing/skeletal API contracts (consultations, review, exports were stubs)
3. 21 backend modules with zero test coverage (TDD violations)
4. Audit logging schema not implemented
5. Missing patients.yaml contract

**Your job in v2**: Re-check ALL v1 findings to see which were fixed and which persist. Then go DEEPER than v1 did. v1 was mostly structural/organizational. v2 must be code-level, line-by-line.

---

## Audit Execution Instructions

### Phase 0: Repository Hygiene and Git Discipline

Read every file in the repo root, `.github/`, and dotfiles. Check for:

1. **`.DS_Store` committed to git** -- is it in `.gitignore`? Is the existing one tracked? This is a hygiene failure.
2. **`.poc-frontend/` directory** -- contains two massive PNG files (~6.8MB and ~6MB each) committed to the repo. Investigate: are these referenced anywhere? Are they needed? Should they be in `.gitignore` or LFS? This bloats clone size by ~13MB for no apparent reason.
3. **`tsconfig.app.tsbuildinfo` and `tsconfig.node.tsbuildinfo`** committed in `app/` -- build artifacts should not be in version control. Check `.gitignore` coverage.
4. **`infra/deskai_infra.egg-info/`** -- Python egg-info directory committed. This is a build artifact. Should be gitignored.
5. **`package-lock.json` at root level** -- the root has a package.json and lock file. Check: is this intentional for monorepo tooling (prettier, stylelint, markdownlint) or an accidental artifact? Are the root deps actually used?
6. **GitHub workflows** (`app-ci.yml`, `backend-ci.yml`, `infra-ci.yml`, `deploy.yml`) -- read each one line by line:
   - Do they actually run tests or just lint?
   - Is `deploy.yml` a placeholder? If so, what happens if someone triggers it?
   - Are there any missing CI checks (e.g., contract validation, security scanning)?
   - Do the CI pipelines match the Makefile targets?
7. **CODEOWNERS** -- read it. Does it cover all critical paths? Are the owners valid GitHub users/teams?

### Phase 1: Documentation Consistency Deep-Dive

This is NOT a surface-level check. Read EVERY documentation file and cross-reference them against each other and the code.

**Files to read in full**:
- `CLAUDE.md`
- `docs/ai-context-rules.md`
- `docs/mvp-business-rules.md`
- `docs/mvp-technical-specs.md`
- `docs/implementation-prompt.md`
- `.ai-utils/implementation-prompt.md`
- `docs/local-development.md`
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/02-backend-architecture.md`
- `docs/architecture/03-contract-inventory.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/01-requirements-traceability-matrix.md`
- `docs/requirements/02-consultation-lifecycle.md`
- `docs/requirements/03-plan-entitlements.md`
- `docs/requirements/04-failure-behavior-matrix.md`
- `docs/requirements/05-decision-log.md`
- `tasks/@task-manager.md`
- All 15 task files (`tasks/001-*.md` through `tasks/015-*.md`)
- `CONTRIBUTING.md`
- All README.md files (root, backend, infra, app, website, contracts)

**For each document, check**:

1. **Internal consistency**: Does the document contradict itself? Are section numbers correct? Are cross-references valid?
2. **Cross-document consistency**: Do two documents say different things about the same topic? Especially check:
   - File reading priority order (CLAUDE.md vs implementation-prompt.md vs .ai-utils/implementation-prompt.md)
   - State machine definitions (business rules vs lifecycle doc vs tech specs)
   - API endpoint lists (contract inventory vs tech specs vs actual YAML files)
   - Plan types and entitlements (business rules vs plan-entitlements doc)
   - DynamoDB access patterns (tech specs vs data-flow doc vs actual code)
3. **Docs vs Code drift**: Does the documentation describe something that doesn't exist in code? Does the code do something not documented?
4. **Stale references**: Do any docs reference files, sections, or features that don't exist?
5. **Local path leakage**: Do any docs contain local filesystem paths (e.g., `/Users/gabrielsantiago/Documents/DeskAI/`)? The README.md has this -- flag every instance.
6. **`.ai-utils/implementation-prompt.md` vs `docs/implementation-prompt.md`**: Are these identical? If not, which is authoritative? This is a duplication hazard.

### Phase 2: Contract Validation (YAML files)

Read every YAML file in `contracts/` character by character.

**HTTP contracts** (`contracts/http/`):
- `auth.yaml` (~6KB -- the most complete one)
- `consultations.yaml` (~12KB)
- `patients.yaml` (~3KB)
- `review.yaml` (~7KB)
- `exports.yaml` (~2KB)
- `ui-config.yaml` (~5KB)
- `errors.yaml` (~480B)

**For each HTTP contract**:

1. Does every endpoint have an `operationId`?
2. Does every endpoint have `security` declarations? (Protected endpoints need `bearerAuth`, public endpoints need explicit `security: []`)
3. Does every endpoint define request body schemas with required fields?
4. Does every endpoint define response schemas for success AND error cases (400, 401, 403, 404, 409, 500)?
5. Are `$ref` references valid and pointing to existing schema definitions?
6. Do parameter names match what the backend code actually expects?
7. Are there endpoints documented in `docs/architecture/03-contract-inventory.md` that are MISSING from the YAML files?
8. Are there YAML endpoints that are NOT listed in the contract inventory doc?
9. Check for plan-based access control: endpoints that enforce plan limits should document `403` with codes like `plan_limit_exceeded`, `trial_expired`, `feature_not_available`.
10. Validate YAML syntax -- are there any parsing errors, unclosed quotes, wrong indentation?

**WebSocket contracts** (`contracts/websocket/`):
- `events.yaml`
- `session.yaml`

1. Are message types strictly defined or using `additionalProperties: true` (too permissive for health data)?
2. Is the `data` field loosely typed? Can arbitrary payloads be sent?
3. Is there authentication defined for the WebSocket `$connect` route?
4. Are error/disconnect events documented?

**Feature flags** (`contracts/feature-flags/flags.yaml`):
1. Are all flags referenced in code defined here?
2. Does each flag have plan-specific overrides?
3. Are default values appropriate?

**UI config** (`contracts/ui-config/labels.yaml`, `screen-schemas.yaml`):
1. Are required keys defined or is it open-ended?
2. Does `additionalProperties: true` appear? If so, flag it.

### Phase 3: Backend Code Audit -- Domain Layer (LINE BY LINE)

The domain layer is the heart of the application. It MUST be pure business logic with ZERO framework/AWS imports.

**Read every file in these directories**:
- `backend/src/deskai/domain/auth/`
- `backend/src/deskai/domain/consultation/`
- `backend/src/deskai/domain/patient/`
- `backend/src/deskai/domain/session/`
- `backend/src/deskai/domain/transcription/`
- `backend/src/deskai/domain/ai_pipeline/`
- `backend/src/deskai/domain/audit/`
- `backend/src/deskai/domain/review/`
- `backend/src/deskai/domain/export/`
- `backend/src/deskai/domain/config/`

**For each domain file, check**:

1. **Import violations**: Does ANY domain file import from `boto3`, `botocore`, `aws_cdk`, `aws_lambda_powertools`, or any AWS SDK? This violates hexagonal architecture. Flag every instance with file:line.
2. **Framework leakage**: Does any domain file import from `fastapi`, `flask`, `django`, or any web framework? Flag it.
3. **Entity immutability**: Are domain entities (dataclasses, frozen dataclasses, named tuples) truly immutable? Can they be mutated after creation? Check for:
   - `@dataclass` without `frozen=True`
   - Mutable default arguments (lists, dicts)
   - Methods that modify `self` state
4. **Value object validation**: Do value objects validate their invariants on creation? For example:
   - Does `ConsultationStatus` enforce valid state transitions?
   - Does an email value object validate format?
   - Does a CPF value object validate checksum?
   - Does a medical specialty value object restrict to allowed values?
5. **State machine correctness**: Read the consultation lifecycle state machine. Compare it against `docs/requirements/02-consultation-lifecycle.md`. Check:
   - Are ALL documented states implemented?
   - Are ALL documented transitions implemented?
   - Are INVALID transitions explicitly rejected?
   - Is `processing_failed` handled?
   - What happens on double-finalization?
6. **Business rule enforcement**: For each business rule in `docs/mvp-business-rules.md`, find the corresponding domain code. Flag any business rule that has NO domain code enforcing it.
7. **Empty/stub modules**: Which domain subdirectories contain only `__init__.py` files? These are stub modules with no implementation. List them all.
8. **Error handling**: Do domain methods raise domain-specific exceptions or generic Python exceptions? Are error messages informative?
9. **Type safety**: Are type hints used consistently? Are there any `Any` types that should be specific? Are `Optional` types handled properly (no bare access without None checks)?

### Phase 4: Backend Code Audit -- Ports Layer

Read every file in `backend/src/deskai/ports/`.

1. **Stub detection**: Several port files are only 34 bytes (`# Placeholder`). List EVERY stub port. Cross-reference against the architecture doc to determine which ports should exist.
2. **Interface completeness**: For ports that ARE implemented (have abstract methods):
   - `artifact_repository.py` -- does it define all CRUD operations needed?
   - `audit_repository.py` -- does it define log_event? query_events?
   - `auth_provider.py` -- does it cover all auth flows (login, signup, refresh, forgot-password, confirm-forgot-password, sign-out, change-password)?
   - `consultation_repository.py` -- does it cover create, read, update, list, delete?
   - `doctor_repository.py` -- what operations does it define?
   - `patient_repository.py` -- does it handle the clinic-scoped access pattern?
   - `session_repository.py` -- does it handle WebSocket connection lifecycle?
   - `transcript_repository.py` -- does it handle both raw and normalized transcripts?
   - `transcription_provider.py` -- does it define streaming and batch interfaces?
   - `llm_provider.py` -- does it define prompt execution and structured output parsing?
3. **Return types**: Do port methods return domain objects (good) or dicts/raw data (bad)?
4. **Async patterns**: Are any ports defined as async? Should they be?
5. **Missing ports**: Based on the architecture, should there be ports for: notification sending, metrics publishing, health checks, rate limiting?

### Phase 5: Backend Code Audit -- Adapters Layer

Read every file in `backend/src/deskai/adapters/` and all subdirectories:
- `auth/`, `events/`, `export/`, `llm/`, `persistence/`, `secrets/`, `storage/`, `transcription/`

1. **Port implementation**: Does every adapter implement a corresponding port interface? Are there adapters without ports or ports without adapters?
2. **AWS SDK usage**: Check for:
   - Hardcoded AWS regions, account IDs, or resource ARNs
   - Missing error handling around boto3 calls (every AWS call can fail)
   - Missing retry logic for transient failures
   - Missing pagination handling for list operations
   - DynamoDB: are queries using proper key conditions vs scan? Is `FilterExpression` used on large tables (expensive)?
   - S3: are uploads using proper content types? Is server-side encryption specified?
   - Cognito: are tokens validated properly? Is the user pool ID sourced from config?
3. **Data serialization**: How is data serialized to/from DynamoDB? Check for:
   - Decimal handling (DynamoDB returns Decimal, not float)
   - Date/time serialization (ISO 8601? Unix timestamps?)
   - Enum serialization (stored as strings? ints?)
   - Null handling (DynamoDB does not store None/null by default)
4. **Sensitive data handling**: Do any adapters log request/response bodies that could contain PHI (patient names, CPF, medical content)?
5. **Connection management**: Are AWS clients created per-request (expensive) or reused? Lambda best practice is to create clients outside the handler.

### Phase 6: Backend Code Audit -- Application Layer (Use Cases)

Read every file in `backend/src/deskai/application/` and all subdirectories:
- `auth/`, `consultation/`, `patient/`, `session/`, `transcription/`, `ai_pipeline/`, `config/`, `export/`, `review/`

1. **Use case structure**: Does each use case follow a consistent pattern? (Input DTO -> validate -> execute domain logic via ports -> return Output DTO)
2. **Authorization**: Do use cases that need it check user permissions? Is the doctor-only-sees-their-data rule enforced at this layer?
3. **Transaction boundaries**: Are multi-step operations atomic? What happens if step 2 fails after step 1 succeeds? Is there compensation logic?
4. **Input validation**: Is input validated at the use case boundary? Are there injection risks from unvalidated strings?
5. **Empty/stub use cases**: Which use case files are stubs? List them all.
6. **Plan entitlement enforcement**: Do use cases that should enforce plan limits actually check them? (consultation creation, export generation, concurrent session limits)

### Phase 7: Backend Code Audit -- Handlers Layer (Lambda Entry Points)

Read every file in:
- `backend/src/deskai/handlers/http/`
- `backend/src/deskai/handlers/websocket/`
- `backend/src/deskai/handlers/step_functions/`
- `infra/lambda_handlers/` (bff.py, pipeline.py, exporter.py, websocket.py)

1. **Request parsing**: Do handlers properly parse and validate incoming Lambda event payloads? Are there unhandled KeyError/TypeError exceptions if the event shape is unexpected?
2. **Response format**: Do HTTP handlers return proper API Gateway response format (`statusCode`, `body`, `headers`)? Is CORS handled?
3. **Error handling**: Do handlers catch exceptions and return structured error responses, or do they let exceptions propagate (causing 500s with stack traces)?
4. **Authentication extraction**: Do handlers extract and validate the Cognito JWT from the `Authorization` header or `requestContext.authorizer`? Is there a shared auth middleware or is it copy-pasted?
5. **Logging**: Do handlers log request IDs and correlation IDs for traceability?
6. **Cold start**: Are there any heavy imports or initializations inside the handler function (vs module level)?
7. **infra/lambda_handlers/ vs backend/src/deskai/handlers/**: What is the relationship? Does one delegate to the other? Are there two separate handler implementations (duplication)?
8. **BFF handler (`bff.py`)**: This is ~4.5KB -- read it line by line. Does it handle routing correctly? Does it handle all documented endpoints?

### Phase 8: Backend Code Audit -- BFF Layer

Read every file in `backend/src/deskai/bff/`:
- `action_availability.py`
- `response.py`
- `feature_flags/`
- `ui_config/`
- `views/`

1. **Action availability**: Does the action availability logic correctly determine which UI actions are available based on consultation status + plan type? Test mentally with each status/plan combination.
2. **Feature flag evaluation**: Is the feature flag system properly tied to plan types? Can a free_trial user access pro features through a flag bypass?
3. **View model assembly**: Do BFF views assemble all the data the frontend needs in a single response, or does the frontend need multiple roundtrips?
4. **Hardcoded values**: Are there hardcoded labels, URLs, or configuration that should come from contracts or config?

### Phase 9: Backend Code Audit -- Shared Layer

Read every file in `backend/src/deskai/shared/`:
- `config.py`, `errors.py`, `identifiers.py`, `logging.py`, `time.py`, `types.py`

1. **Config loading**: How are environment variables loaded? Is there validation? What happens if a required env var is missing?
2. **Error hierarchy**: Is there a proper exception hierarchy? Are domain errors distinguishable from infrastructure errors?
3. **Logging safety**: Does `logging.py` have ANY mechanism to prevent PHI from being logged? Or is it just a basic logger setup?
4. **ID generation**: How are entity IDs generated? UUID4? Are they collision-safe?
5. **Time handling**: Is timezone handling correct? All times should be UTC internally, pt-BR display externally.

### Phase 10: Backend Code Audit -- Container / DI

Read `backend/src/deskai/container.py` (~8KB) line by line.

1. **Dependency wiring**: Are all ports wired to their adapter implementations?
2. **Missing wirings**: Are there ports defined but not wired in the container?
3. **Circular dependencies**: Are there any circular import risks?
4. **Environment-specific wiring**: Does the container support different wirings for test vs dev vs prod?
5. **Singleton vs per-request**: Are AWS clients created as singletons (correct for Lambda) or per-request (wasteful)?

### Phase 11: Backend Code Audit -- Prompts

Read every file in `backend/src/deskai/prompts/`:
- `insights.pt-BR.md`
- `medical_history.pt-BR.md`
- `summary.pt-BR.md`

1. **Prompt injection risk**: Could a malicious transcript injection manipulate these prompts to produce fabricated medical content?
2. **Report-only compliance**: Do the prompts explicitly instruct the LLM to ONLY report what was said, never interpret?
3. **Schema enforcement**: Do the prompts instruct the LLM to output in a specific schema? Is there validation downstream?
4. **Completeness**: Are there prompts for ALL required artifacts (transcript, medical history, summary, insights)? Is the transcript prompt missing?
5. **Language**: Are prompts in pt-BR as required by CLAUDE.md?
6. **Size and quality**: Are the prompts suspiciously small (<300 bytes)? A production medical AI prompt should be detailed and specific.

### Phase 12: Infrastructure Code Audit (CDK Stacks)

Read every file in `infra/stacks/` and `infra/constructs/`:
- `api_stack.py`, `auth_stack.py`, `budget_stack.py`, `cdn_stack.py`, `compute_stack.py`, `monitoring_stack.py`, `orchestration_stack.py`, `security_stack.py`, `storage_stack.py`
- `constructs/tagged_construct.py`
- `infra/app.py` (CDK app entry point)
- `infra/config/base.py`, `infra/config/dev.py`, `infra/config/prod.py`
- `infra/scripts/build_lambda.sh`

**For each stack, check**:

1. **IAM permissions**: Are they least-privilege? Flag any `*` in resource ARNs. Flag any `Action: *`. The v1 audit found XRay wildcard -- is it still there?
2. **Encryption**: Is data encrypted at rest AND in transit for DynamoDB, S3, SQS, SNS? Is KMS key management proper?
3. **Network security**: Are Lambda functions in a VPC? If not, is that acceptable for health data?
4. **Secrets management**: Are secrets stored in AWS Secrets Manager / SSM Parameter Store? The v1 audit found `SecretValue.unsafe_plain_text("replace-in-aws-secrets-manager")` -- is this still there?
5. **Cognito configuration**: Password policy, MFA settings, email verification, user pool deletion protection?
6. **API Gateway**: Rate limiting, throttling, WAF integration, access logging?
7. **DynamoDB**: Point-in-time recovery (PITR), deletion protection, backup strategy, GSI design?
8. **S3**: Block public access, versioning, lifecycle rules, access logging?
9. **Lambda**: Memory allocation, timeout settings, reserved concurrency, dead letter queues?
10. **Step Functions**: State machine definition, error handling, retry policies, timeout per state?
11. **Budget alerts**: Are they configured? What are the thresholds?
12. **Monitoring**: CloudWatch alarms, dashboards, log retention policies?
13. **Cross-stack dependencies**: Are they properly managed via exports/imports or props?
14. **Environment separation**: Can dev and prod accidentally share resources? Are resource names environment-prefixed?
15. **CDN stack**: Is it configured correctly for the website and app? HTTPS enforcement? Cache policies?

### Phase 13: Infrastructure Tests

Read `infra/tests/test_config.py` and `infra/tests/test_stacks.py`.

1. **Coverage**: Do the tests cover ALL stacks? Which stacks have zero test assertions?
2. **Assertion quality**: Do tests assert on specific resource properties (security-critical) or just "stack synthesizes without error" (shallow)?
3. **Security assertions**: Do tests verify encryption, IAM policies, public access blocks?
4. **Missing tests**: Are there tests for the Lambda build script? For the CDK app entry point?

### Phase 14: Frontend Code Audit (React App)

Read every file in `app/src/`:
- `main.tsx`, `App.tsx`, `index.css`, `vite-env.d.ts`
- `components/AppLayout.tsx`, `components/StatusCard.tsx`
- `pages/DashboardPage.tsx`, `pages/ConsultationPage.tsx`
- `hooks/useUiConfig.ts`
- `api/client.ts`, `api/consultations.ts`
- `types/contracts.ts`
- `utils/format.ts`
- `config/env.ts`

Also read: `app/eslint.config.js`, `app/vite.config.ts`, `app/package.json`, `app/tsconfig.*.json`

1. **Authentication**: How is the auth token managed? Is it stored in localStorage (XSS vulnerable), sessionStorage, or httpOnly cookies? Is there token refresh logic?
2. **API client**: Does `client.ts` properly attach auth tokens to requests? Does it handle 401 responses (token expired)?
3. **XSS prevention**: Are there any uses of `dangerouslySetInnerHTML`? Is user input sanitized before display?
4. **Sensitive data exposure**: Does the frontend ever log or display sensitive data (CPF, patient names, medical content) in console, error messages, or analytics?
5. **Environment variables**: Does `config/env.ts` expose any secrets? Are all env vars prefixed with `VITE_` (required for Vite)?
6. **Completeness**: How many pages and components exist vs what's needed for the MVP? Is this a skeleton or a real app?
7. **Error handling**: What happens when API calls fail? Is there user-facing error handling or does the app crash silently?
8. **Testing**: Are there ANY test files in `app/`? (v1 found zero -- has this changed?)
9. **TypeScript strictness**: Is `strict: true` enabled in tsconfig? Are there any `any` types?
10. **Accessibility**: Are there ARIA attributes? Semantic HTML? Keyboard navigation?
11. **Build artifacts committed**: `tsconfig.app.tsbuildinfo` and `tsconfig.node.tsbuildinfo` should not be in git.

### Phase 15: Website Audit (Public Static Site)

Read every file in `website/`:
- `pages/index.html`, `pages/about.html`, `pages/pricing.html`
- `assets/` directory
- `package.json`

1. **Content language**: Is user-facing content in pt-BR as required?
2. **Security headers**: Are there meta tags for CSP, X-Frame-Options?
3. **External dependencies**: What JS/CSS is loaded from CDNs? Are there integrity hashes (SRI)?
4. **SEO**: Are there meta descriptions, Open Graph tags, canonical URLs?
5. **Pricing page**: Does it match the plan types defined in business rules (free_trial, plus, pro)?
6. **Links**: Do all links point to valid destinations? Are there broken links to the app?

### Phase 16: Test Coverage Audit (MOST CRITICAL)

The project claims strict TDD. Verify this claim ruthlessly.

**Read every test file** in:
- `backend/tests/unit/` (all subdirectories)
- `backend/tests/integration/`
- `backend/tests/conftest.py`
- `infra/tests/`

**For each test file**:

1. **What does it actually test?** Read the test functions. Do they test behavior and business rules, or just test that objects can be instantiated?
2. **Assertion quality**: Do tests assert on specific outcomes, or just `assert result is not None`?
3. **Edge cases**: Do tests cover error paths, boundary conditions, and invalid inputs?
4. **Mocking**: Are dependencies properly mocked? Or are tests hitting real services?

**Coverage gap analysis -- build a complete matrix**:

| Module | Source Files | Test Files | Coverage Assessment |
|--------|-------------|------------|---------------------|

List every single Python source file under `backend/src/deskai/` and check if a corresponding test file exists. Flag every file with zero test coverage.

**Specific TDD violations to look for**:
- Are there implementation files with no corresponding test? (Red flag: implementation without test = TDD violation)
- Are there test files that only test trivial things (enum values, dataclass creation) while ignoring business logic?
- `conftest.py` -- is it empty or does it have proper fixtures? Does it have fixtures for: mock DynamoDB, mock S3, mock Cognito, mock LLM responses, mock transcription responses, test consultation data, test user data?
- Integration tests: `test_settings_loading.py` is the ONLY integration test. There should be integration tests for every adapter using moto/localstack.
- Handler tests: Are there ANY handler tests? Can you find Lambda event fixtures?

### Phase 17: Security Audit (Health Data Focus)

This is a medical application handling sensitive health information. Security must be production-grade even in MVP.

1. **Authentication flow**: Trace the complete auth flow from login to API call. Can you find any way to bypass authentication?
2. **Authorization**: Is there tenant isolation? Can doctor A access doctor B's consultations? Trace the data access path.
3. **Data at rest**: Is ALL sensitive data encrypted? Check DynamoDB, S3, and any local storage.
4. **Data in transit**: Is TLS enforced everywhere? Check API Gateway, WebSocket, S3 access.
5. **PHI in logs**: Search the entire codebase for `print(`, `logger.info(`, `logger.debug(`, `logger.error(`, `console.log(`. Flag any that could log patient data, medical content, CPF, or personal identifiers.
6. **Error messages**: Do error responses expose internal details (stack traces, file paths, SQL queries, DynamoDB table names)?
7. **Input validation**: Are all user inputs validated? Check for:
   - SQL injection (not applicable with DynamoDB, but check if any SQL is used)
   - NoSQL injection (DynamoDB expressions built from user input)
   - XSS (user content reflected in responses)
   - Path traversal (file paths built from user input)
   - Prompt injection (user content sent to LLM without sanitization)
8. **CORS**: Are CORS policies properly restrictive? Can any domain make API calls?
9. **Rate limiting**: Is there protection against brute-force login, API abuse?
10. **Secret rotation**: Are API keys, JWT secrets, and LLM API keys rotatable?
11. **Dependency vulnerabilities**: Check `pyproject.toml` and `package.json` for known vulnerable dependencies. Note the versions of critical deps.
12. **WebSocket security**: Is the `$connect` route authenticated? Can an unauthenticated client establish a WebSocket connection?

### Phase 18: Architecture Compliance Audit

1. **Hexagonal violations**: For every import statement in every Python file, verify the dependency direction:
   - `domain/` must NOT import from `adapters/`, `handlers/`, `application/`, `bff/`, or any AWS SDK
   - `application/` must NOT import from `adapters/` or `handlers/` (only from `domain/` and `ports/`)
   - `ports/` must NOT import from `adapters/`
   - `handlers/` may import from `application/` and `bff/`, not from `domain/` directly (debatable but check)
2. **Business logic location**: Is any business logic in handlers (wrong), adapters (wrong), or BFF (wrong)?
3. **Single responsibility**: Are there god classes or god functions that do too much?
4. **Dead code**: Are there imported but unused modules? Defined but uncalled functions?
5. **Naming consistency**: Are file names, class names, and function names consistent across the codebase?
6. **Python code quality**:
   - Are there bare `except:` clauses (catches everything including SystemExit)?
   - Are there `pass` in except blocks (swallowed errors)?
   - Are there mutable default arguments?
   - Are there global variables that should be class/instance attributes?
   - Are type hints used consistently?
   - Is `if x is None` used instead of `if not x` for Optional checks?

### Phase 19: Cross-Cutting Concerns

1. **Observability**: Is there structured logging? Request tracing? Metrics emission?
2. **Idempotency**: Are write operations idempotent? What happens on retry?
3. **Pagination**: Are list endpoints paginated? What's the max page size?
4. **Concurrency**: Are there race conditions? What if two requests modify the same consultation simultaneously?
5. **Graceful degradation**: What happens if the LLM provider is down? If Deepgram is down? Is there fallback behavior?
6. **Cost controls**: Are there safeguards against runaway Lambda invocations or LLM API calls?

---

## Output Format

Produce your audit report in this exact structure:

```markdown
# DeskAI Deep Code Audit Report v2

**Date**: 2026-04-03
**Auditor**: [Your identifier]
**Repository**: desk-ai-bizness/DeskAI
**Commit**: [HEAD commit SHA]

## Executive Summary
- Total findings: X
- Critical: X | High: X | Medium: X | Low: X | Info/Pass: X
- Top 5 most urgent issues (numbered)
- Delta from v1: X findings resolved, X new findings, X persisting

## v1 Finding Status
| v1 # | v1 Severity | Status | Notes |
(For each of the 88 actionable v1 findings, mark: FIXED, PERSISTS, PARTIALLY_FIXED, WONTFIX)

## Phase 0: Repository Hygiene
(Table of findings)

## Phase 1: Documentation Consistency
(Table of findings)

... (one section per phase, Phases 2-19) ...

## Severity Definitions
- CRITICAL: Security vulnerability, data loss risk, or blocking correctness issue
- HIGH: Significant quality gap, missing tests for implemented code, or architecture violation
- MEDIUM: Inconsistency, incomplete implementation, or documentation gap
- LOW: Style issue, minor improvement, or optional enhancement
- INFO/PASS: Verified correct, no action needed

## Recommended Fix Priority
### Tier 1: Fix Immediately (before any new development)
### Tier 2: Fix Before Next Task Completion
### Tier 3: Fix Before Production
### Tier 4: Ongoing Improvement
```

**For each finding, provide**:
- Finding number (sequential across entire report)
- Severity (CRITICAL/HIGH/MEDIUM/LOW/INFO)
- File path and line number(s) where applicable
- Exact description of the issue
- Concrete recommendation (not vague -- specific code change or action)
- If it relates to a v1 finding, reference the v1 number

---

## Behavioral Rules for the Auditor

1. **Read every file**. Do not skip files. Do not assume a file is correct because its name looks reasonable.
2. **Quote code**. When you find an issue, show the exact code snippet. Don't just say "there's a problem in X" -- show the problematic lines.
3. **Be specific**. "Tests are weak" is not a finding. "test_consultation_status.py only tests enum membership via `self.assertEqual(ConsultationStatus.CREATED.value, 'created')` but does not test state transition logic (e.g., CREATED -> RECORDING is valid, CREATED -> FINALIZED is invalid)" is a finding.
4. **No false praise**. If something is a basic expectation (e.g., "files have docstrings"), don't give it a PASS finding. Only note things that are genuinely notable or above expectations.
5. **Count your findings**. Number them sequentially. Cross-reference where related.
6. **Prioritize security**. This is health data. A missing test is high severity. A potential PHI leak is critical.
7. **Check the small things**: trailing whitespace in YAML, inconsistent quote styles, TODO/FIXME comments left in code, commented-out code, unused imports, `__pycache__` or `.pyc` files committed.
8. **Verify v1 fixes**. For every v1 finding, explicitly state whether it's fixed or persists. Do not assume things were fixed.

---
---

# APPENDIX A: Pre-Investigation Findings (16 Parallel Audit Agents)

The following findings were discovered by 16 specialized audit agents scanning the repo on 2026-04-03. Use these as a verified starting checklist. Each finding should be RE-VERIFIED by you (the auditor) -- confirm it still holds, check if it's been fixed since the scan, and add any additional context you find.

**Total pre-investigation findings: ~150+**

---

## A.1 v1 Audit Fix Verification

### v1 CRITICAL Findings (8 total) -- 7 FIXED, 1 PERSISTS

| v1 # | Description | Status |
|---|---|---|
| 1 | Missing `patients.yaml` | **FIXED** -- now 3,109B with full schemas |
| 2 | Incomplete `consultations.yaml` (was 633B) | **FIXED** -- now 12,439B |
| 3 | Missing session endpoint contracts | **FIXED** -- in consultations.yaml |
| 4 | Skeletal `review.yaml`/`exports.yaml` | **FIXED** -- 7,416B/2,111B |
| 9 | Missing DEC entries for ADRs 009-014 | UNKNOWN (documentation scope) |
| 12 | Missing `operationId` on non-auth contracts | **FIXED** -- all endpoints have operationIds |
| 13 | Missing `components.schemas` | **FIXED** |
| 14 | No `security` declarations on protected endpoints | **FIXED** |

### v1 HIGH Findings -- Key Status

| v1 # | Description | Status |
|---|---|---|
| 5 | Skeletal `ui-config.yaml` | **FIXED** -- strict schemas, `additionalProperties: false` |
| 15 | No error response definitions | **FIXED** |
| 24 | No guard condition docs on lifecycle | **FIXED** |
| 25 | Missing `ConsultationDetailView` | **FIXED** |
| 26 | Duplicate Task 007 in priority queue | **FIXED** |
| 34 | Audit logging not implemented | **PARTIALLY_FIXED** -- domain entity exists, adapter exists |
| 48 | CLAUDE.md vs implementation-prompt.md conflict | **PERSISTS** -- actually WORSE (3 files, 2 orderings now) |
| 79 | 21 modules zero test coverage | **PARTIALLY_FIXED** -- now ~29 modules untested (out of ~40 real) |
| 81 | No integration tests | **PERSISTS** -- still only 1 trivial integration test |
| 83 | Empty conftest.py | **FIXED** -- now 6,631B with 9 fixture factories |

---

## A.2 Repository Hygiene Findings

| # | Severity | File/Path | Issue |
|---|----------|-----------|-------|
| H1 | HIGH | `.DS_Store` (root) | macOS binary committed despite `.gitignore` listing. Needs `git rm --cached`. |
| H2 | HIGH | `.poc-frontend/Gemini_Generated_Image_*.png` | Two unreferenced 6MB+ PNGs (~13MB total). Not used anywhere. Bloats repo permanently. |
| H3 | MEDIUM | `app/tsconfig.app.tsbuildinfo` | TypeScript build artifact committed. Add `*.tsbuildinfo` to `.gitignore`. |
| H4 | MEDIUM | `app/tsconfig.node.tsbuildinfo` | Same as above. |
| H5 | MEDIUM | `infra/deskai_infra.egg-info/` (5 files) | Python egg-info committed. Add `*.egg-info/` to `.gitignore`. |
| H6 | MEDIUM | `.github/workflows/app-ci.yml` | **No test step** -- only lint + typecheck + build. |
| H7 | LOW | `.github/workflows/infra-ci.yml` | PR trigger has no path filter (runs on ALL PRs, wastes runners). |
| H8 | LOW | `.github/workflows/deploy.yml` | Placeholder only -- `echo "Deployment pipeline placeholder"`. |
| H9 | LOW | `.github/CODEOWNERS` | Wildcard `*` only, no path-specific ownership. |
| H10 | LOW | `.gitignore` | Missing `*.egg-info/` and `*.tsbuildinfo` patterns. |
| H11 | INFO | `.prettierignore` | Lists `.poc-frontend` (knows it's dead) but `.gitignore` doesn't exclude it. |
| H12 | INFO | Root `Makefile` | No `app-test` target (consistent with missing app tests). |

---

## A.3 Domain Layer Findings

**Inventory**: 56 files total. 26 stubs, 28 real implementation files, 2 junk files.

**Four ENTIRE subdomains are empty placeholders**: `ai_pipeline/`, `config/`, `export/`, `review/` (20 stub files).

| # | Severity | File | Issue |
|---|----------|------|-------|
| D1 | MEDIUM | `domain/consultation/test.tmp` | Junk file containing `"x"` -- debug leftover committed to repo. |
| D2 | MEDIUM | `domain/session/test.tmp` | Same junk file. Add `*.tmp` to `.gitignore`. |
| D3 | MEDIUM | `consultation/services.py` | `transition_consultation()` uses `setattr(consultation, key, value)` -- bypasses type checking. Any kwargs silently become new attributes. |
| D4 | MEDIUM | `consultation/services.py` | `transition_consultation()` calls `utc_now_iso()` directly -- impure function, hard to unit test (can't freeze time without mocking import). |
| D5 | MEDIUM | `session/services.py` | `SessionService.can_reconnect()` also calls `utc_now_iso()` directly -- same impurity issue. |
| D6 | MEDIUM | All value objects | **No `__post_init__` validation on ANY frozen dataclass VO.** Can create `AudioChunk(chunk_index=-1, audio_data=b"")` or `SpeakerSegment(start_time > end_time)`. |
| D7 | MEDIUM | `session/entities.py` | `SessionState` has 6 values but **NO transition enforcement** (no `ALLOWED_TRANSITIONS` dict like consultation has). |
| D8 | LOW | `consultation/value_objects.py` | `ArtifactPointer` has `s3_key: str` field -- infrastructure concern leaking into domain. |
| D9 | LOW | `session/services.py` | Cross-domain import: imports `consultation.entities.ConsultationStatus`. |
| D10 | INFO | All domain files | **ZERO hexagonal violations** -- no boto3, botocore, or AWS imports anywhere. Clean. |
| D11 | INFO | Entities | 3 mutable entities (`Consultation`, `Session`, `NormalizedTranscript`) -- intentional for aggregate roots. All value objects and events are `frozen=True`. |

**State Machine** (found in `consultation/services.py`):
```
STARTED -> RECORDING -> IN_PROCESSING -> DRAFT_GENERATED -> UNDER_PHYSICIAN_REVIEW -> FINALIZED
                         IN_PROCESSING -> PROCESSING_FAILED -> IN_PROCESSING (retry)
                         UNDER_PHYSICIAN_REVIEW -> UNDER_PHYSICIAN_REVIEW (self-loop for edits)
```
7 states, 8 transitions. Matches docs. Properly enforced via `validate_transition()`.

---

## A.4 Ports Layer Findings

**Inventory**: 16 files. 11 real abstract interfaces (34 methods total), 4 stubs (34 bytes each), 1 `__init__.py`.

| # | Severity | File | Issue |
|---|----------|------|-------|
| P1 | HIGH | `doctor_repository.py` | Method `find_by_cognito_sub` -- infrastructure name "cognito" leaks into the port interface. Should be `find_by_identity_sub`. |
| P2 | HIGH | `llm_provider.py`, `transcript_repository.py`, `transcription_provider.py`, `artifact_repository.py` | Return raw `dict` instead of domain objects. 4 ports have untyped boundaries crossing the hexagonal boundary. |
| P3 | MEDIUM | `transcription_provider.py` | 5 sync methods for a real-time streaming service. Should be async. |
| P4 | MEDIUM | `consultation_repository.py` | `find_by_doctor_and_date_range(start_date: str, end_date: str)` -- string dates instead of `date`/`datetime`. |
| P5 | MEDIUM | `consultation_repository.py` | `update_status(**kwargs: object)` -- loose untyped escape hatch. |
| P6 | LOW | Various | Style inconsistency: some ports use docstring bodies, others use `...` (ellipsis). |
| P7 | LOW | `doctor_repository.py` | `count_consultations_this_month` -- cross-aggregate query on doctor port. |
| P8 | INFO | `config_repository.py`, `event_publisher.py`, `export_generator.py`, `storage_provider.py` | 4 stub ports (34 bytes, placeholder docstring only). |

**Missing ports identified**: NotificationProvider, MetricsCollector, HealthCheckProvider, ClinicRepository, UserRepository (account management).

---

## A.5 Adapters Layer Findings

**Inventory**: 27 files. 13 real implementations, 11 stubs, 3 `__init__.py`.

| # | Severity | File | Issue |
|---|----------|------|-------|
| **A1** | **CRITICAL** | ALL 6 DynamoDB adapters | **ZERO error handling on ANY DynamoDB call.** Every `put_item`, `get_item`, `query`, `update_item`, `delete_item` is unprotected. A throttle or access-denied error crashes the Lambda with raw `ClientError`. The Cognito adapter handles errors properly -- persistence layer must follow the same pattern. |
| A2 | HIGH | `dynamodb_consultation_repository.py` | `update_status` defaults `clinic_id = kwargs.pop("clinic_id", "")` -- if missing, writes to `PK = "CLINIC#"` (empty). Silent data corruption. |
| A3 | HIGH | `dynamodb_patient_repository.py` | `find_by_clinic` loads ALL patients into memory, then filters client-side. No server-side filtering. No pagination. Breaks at scale. |
| A4 | HIGH | `s3_client.py` | `put_json`/`put_bytes` have NO try/except. Write failures propagate as raw boto3 errors. |
| A5 | HIGH | `elevenlabs_provider.py` | In-memory `_sessions` dict will NOT survive Lambda cold starts across invocations. Session state is lost. |
| A6 | HIGH | `elevenlabs_provider.py` | Sends raw audio (PHI) to external ElevenLabs API. Requires BAA/data processing agreement for HIPAA/LGPD compliance. |
| A7 | MEDIUM | `s3_client.py`, `dynamodb_audit_repository.py` | `json.dumps()` has no Decimal handling. If DynamoDB Decimal values flow to JSON serialization, it crashes with `TypeError`. |
| A8 | MEDIUM | `dynamodb_session_repository.py` | `update()` uses unconditional `put_item` (full overwrite). No optimistic concurrency -- last-write-wins race condition. |
| A9 | MEDIUM | `elevenlabs_config.py` | No try/except on `get_secret_value()` Secrets Manager call. |
| A10 | INFO | `cognito_provider.py` | **Model adapter** -- excellent error handling, security-conscious, logs only error codes. |
| A11 | INFO | `elevenlabs_provider.py` | **Best retry logic in codebase** -- tenacity exponential backoff, proper error mapping. |

---

## A.6 Application Layer (Use Cases) Findings

**Inventory**: 14 real use cases, 7 stubs, 7 placeholders.

| # | Severity | File | Issue |
|---|----------|------|-------|
| **U1** | **CRITICAL** | `create_consultation.py` | **No entitlement check.** `CheckEntitlementsUseCase` exists but is NEVER called. Free plan users with 0 remaining consultations can create unlimited consultations. |
| U2 | HIGH | `create_consultation.py`, `start_session.py`, `end_session.py`, `finalize_transcript.py` | **No transaction boundaries.** Multi-step writes (save entity -> update related -> audit append) have no rollback. If step 2 fails after step 1, data is inconsistent. |
| U3 | HIGH | `get_consultation.py` | **No doctor_id check.** Any doctor in the same clinic can read any other doctor's consultations. Only scoped by `clinic_id`. |
| U4 | HIGH | `list_consultations.py` | No `AuthContext` usage. Takes bare `doctor_id` -- caller must pass correct ID with no verification. Also no date format validation. |
| U5 | MEDIUM | `config/get_ui_config.py` | **Architecture violation**: imports from `deskai.bff.ui_config.assembler`. Application layer must not depend on BFF layer. |
| U6 | MEDIUM | `config/get_ui_config.py` | Only use case that is NOT `@dataclass(frozen=True)` -- plain class, no DI. Inconsistent with all 13 other use cases. |
| U7 | MEDIUM | `list_patients.py` | `search_term` passed raw to repository with no sanitization. No `AuthContext`. |
| U8 | MEDIUM | `create_patient.py` | DOB validation only checks non-empty. No format, range, or future-date validation. |
| U9 | LOW | `authenticate.py` | No input validation -- empty email/password passed raw to Cognito. |
| U10 | LOW | `forgot_password.py` | No new_password strength validation at application level (relies on Cognito). |

---

## A.7 Handlers Layer Findings

**Architecture: Clean delegation.** `infra/lambda_handlers/` are thin Lambda entry points that delegate to `backend/src/deskai/handlers/`. No duplication.

| # | Severity | File | Issue |
|---|----------|------|-------|
| HA1 | MEDIUM | `infra/lambda_handlers/bff.py` | Container init (`build_container()`) has no try/except. Cold start failure = raw 502. |
| HA2 | MEDIUM | `websocket/router.py` | No try/except around handler dispatch. Unhandled exception = raw 502. |
| HA3 | MEDIUM | `websocket/router.py` | `json.loads(body)` can throw `JSONDecodeError` on malformed WS messages -- no error handling. |
| HA4 | MEDIUM | `websocket/audio_chunk_handler.py` | No size limit on audio chunk payload. Malicious client can send arbitrarily large base64. |
| HA5 | MEDIUM | `websocket/audio_chunk_handler.py` | `base64.b64decode()` not wrapped in try/except. Malformed base64 crashes handler. |
| HA6 | LOW | `http/me_handler.py`, `http/ui_config_handler.py` | JWT claim extraction duplicated instead of using shared middleware. |
| HA7 | LOW | `http/ui_config_handler.py` | `GetUiConfigUseCase()` instantiated directly instead of via DI container. |
| HA8 | LOW | `http/patient_handler.py` | `build_patient_view` imported from `consultation_view` -- misplaced function. |
| HA9 | LOW | `websocket/connect_handler.py` | Bare `except Exception` conflates auth errors with infra errors. |
| HA10 | LOW | `websocket/session_init_handler.py` | Unused `_consultation_id` variable (suppressed with `# noqa: F841`). |
| HA11 | LOW | `websocket/api_gateway_management.py` | New boto3 client created per WS message instead of cached. |
| HA12 | INFO | `step_functions/` | All 3 handler files are empty placeholders. |

---

## A.8 BFF + Shared + Container Findings

| # | Severity | File | Issue |
|---|----------|------|-------|
| B1 | HIGH | `bff/feature_flags/evaluator.py` | `export_pdf_enabled`, `insights_enabled`, `audio_playback_enabled` are **hardcoded** (True/True/False) ignoring plan type entirely. |
| B2 | HIGH | `shared/config.py` | **Dev defaults silently used in production** if env vars missing. `DEFAULT_DYNAMODB_TABLE = "deskai-dev-consultation-records"`. If prod env var is unset, app silently hits dev DB. |
| B3 | MEDIUM | `shared/config.py` | `int(getenv("DESKAI_MAX_SESSION_DURATION_MINUTES", "60"))` -- no error handling. Non-numeric env var crashes with `ValueError`. |
| B4 | MEDIUM | `bff/views/session_view.py` | `connection_token` is just `session_id` -- not a separate cryptographic token. Guessable UUIDs = session hijack risk. |
| B5 | MEDIUM | `bff/views/user_view.py` | `export_enabled` appears in BOTH `entitlements` (domain) AND `feature_flags` (BFF) with no reconciliation. Can diverge. |
| B6 | MEDIUM | `container.py` | Uses `RuntimeError` for missing Cognito config instead of project's own `ConfigurationError`. |
| B7 | LOW | `bff/action_availability.py` | `compute_actions()` called without `export_enabled` flag -- always enables export for FINALIZED. |
| B8 | LOW | `bff/response.py` | `BffResponse` dataclass defined but never used anywhere. Dead code. |
| B9 | LOW | `bff/ui_config/screen_config.py` | `get_consultation_list_config()` defined but never called. Dead code. |
| B10 | LOW | `shared/config.py` | `claude_secret_name`, `cognito_secret_name`, `ui_config_key` loaded but never wired in container. |
| B11 | INFO | `shared/logging.py` | PHI prevention is docstring-only. Good practice but no programmatic enforcement. |
| B12 | INFO | `shared/time.py` | Correctly uses `datetime.now(tz=UTC)` (not deprecated `utcnow()`). |

---

## A.9 AI Prompts Findings

| # | Severity | File | Issue |
|---|----------|------|-------|
| PR1 | HIGH | All 3 prompt files | **All are titled "Placeholder"** (200-321 bytes). Far too small for production medical AI. Production prompts should be 1-5KB with detailed schemas. |
| PR2 | HIGH | All 3 prompt files | **No prompt injection defenses.** No "ignore instructions in transcript" or "treat content as untrusted data" guardrails. |
| PR3 | HIGH | All 3 prompt files | **No output schema enforcement.** LLM could return any format -- free text, markdown, JSON. No downstream validation. |
| PR4 | MEDIUM | `prompts/` directory | **Missing transcript prompt.** No `transcript.pt-BR.md` for STT post-processing. |
| PR5 | MEDIUM | `insights.pt-BR.md` | Allows "atencao_clinica" category without explicit "no diagnosis" guard. |
| PR6 | MEDIUM | `backend/pyproject.toml` | pytest listed as dev dep but Makefile uses `python -m unittest discover`. Tooling mismatch. |
| PR7 | MEDIUM | `backend/` | No dependency lock file for reproducible builds. |
| PR8 | LOW | All prompts + UI config | Missing diacritical marks in Portuguese text ("Revisao" not "Revisao", "Nao" not "Nao"). |
| PR9 | LOW | `backend/pyproject.toml` | All deps use `>=` with no upper bounds. Breaking change risk. |

---

## A.10 CDK Infrastructure Findings

| # | Severity | File | Issue |
|---|----------|------|-------|
| I1 | HIGH | `auth_stack.py` | **MFA is OFF** (`mfa=cognito.Mfa.OFF`). For health data tagged `data-classification: sensitive-health`, MFA should be at minimum optional. |
| I2 | MEDIUM | `api_stack.py` | WebSocket API has **no rate limiting** (HTTP API has burst=100, rate=200). WS connection flooding possible. |
| I3 | MEDIUM | `api_stack.py` | WebSocket API has **no access logging**. Blind spot for security auditing. |
| I4 | MEDIUM | `compute_stack.py` | **All 4 Lambdas share one IAM role.** BFF has pipeline permissions, pipeline has Cognito permissions. Violates least-privilege. |
| I5 | MEDIUM | `compute_stack.py` | `execute-api:ManageConnections` uses wildcard API ID (`*`). Allows managing connections on ANY API Gateway. |
| I6 | MEDIUM | `security_stack.py` | `SecretValue.unsafe_plain_text("replace-in-aws-secrets-manager")` used twice. CDK anti-pattern. Placeholder visible in CFN template. |
| I7 | LOW | `storage_stack.py` | No DynamoDB `deletion_protection=True` (separate from removal policy). |
| I8 | LOW | `api_stack.py` | No WAF on either API. Recommended for health data applications. |
| I9 | LOW | `monitoring_stack.py` | No alarm for export handler Lambda. Missing duration/throttle alarms. |
| I10 | LOW | `cdn_stack.py` | Uses legacy OAI instead of newer OAC (Origin Access Control). |
| I11 | INFO | `security_stack.py` | XRay `resources=["*"]` is the ONLY wildcard -- unavoidable (AWS limitation). Not a real issue. |
| I12 | INFO | All stacks | KMS rotation, PITR, S3 BLOCK_ALL, permissions boundaries, environment tags -- all correctly implemented. |

---

## A.11 CDK Test Findings

| # | Severity | Issue |
|---|----------|-------|
| IT1 | MEDIUM | No CDN security tests (HTTPS-only, TLS version, OAI/OAC) |
| IT2 | MEDIUM | No SQS/SNS encryption tests |
| IT3 | MEDIUM | No Lambda env var tests (could leak secrets) |
| IT4 | MEDIUM | No Cognito MFA test |
| IT5 | MEDIUM | No DynamoDB deletion protection test |
| IT6 | LOW | No Lambda reserved concurrency test |
| IT7 | LOW | No alarm property assertions (just count) |
| IT8 | LOW | Pip deps not pinned or hash-verified (supply chain risk) |
| IT9 | LOW | No `ruff` security rules (`S` for bandit) |
| IT10 | LOW | No `cdk diff` enforcement before deploy |

**What IS tested well**: KMS key rotation, S3 public access blocks, DynamoDB PITR + encryption, Cognito password policy + no self-signup, dev/prod CORS disjoint.

---

## A.12 Frontend Findings

**Status: SKELETON / SCAFFOLD.** Only 1 real API call (`GET /v1/ui-config`).

| # | Severity | Issue |
|---|----------|-------|
| F1 | HIGH | **ZERO test files.** No vitest, jest, or testing-library in deps. No test script. |
| F2 | MEDIUM | **No auth at all.** No Authorization header in API client, no token storage, no login flow. |
| F3 | LOW | Dead code: `fetchConsultations()`, `toPtBrDate()`, `wsBaseUrl` config, `@/*` path alias -- all defined but never used. |
| F4 | LOW | `tsconfig.app.tsbuildinfo` and `tsconfig.node.tsbuildinfo` committed (build artifacts). |
| F5 | LOW | No `.env.example` documenting required VITE_ env vars. |
| F6 | INFO | TypeScript strict mode enabled with `noUncheckedIndexedAccess`. Good. |
| F7 | INFO | No `dangerouslySetInnerHTML` anywhere. Clean XSS profile. |

---

## A.13 Contract (YAML) Findings

| # | Severity | File | Issue |
|---|----------|------|-------|
| C1 | HIGH | `review.yaml` | `GET /review` missing `403` -- no authorization error for cross-doctor access. |
| C2 | HIGH | `review.yaml` | `PUT /review` missing `403` -- same. |
| C3 | HIGH | `review.yaml` | `POST /finalize` missing `403` -- same. |
| C4 | HIGH | `review.yaml` | `PUT /review` missing `409` -- no state conflict guard for non-reviewable consultations. |
| C5 | HIGH | `review.yaml` | `UpdateReviewRequest.medical_history` uses `additionalProperties: true` -- accepts ANY JSON for medical history writes. |
| C6 | MEDIUM | `auth.yaml` | `POST /forgot-password` missing `400` for malformed body. |
| C7 | MEDIUM | `consultations.yaml` | `GET /consultations` missing `403` (inconsistent with `listPatients`). |
| C8 | MEDIUM | `errors.yaml` | `error.code` is untyped string -- no enum of known error codes. |
| C9 | MEDIUM | `screen-schemas.yaml` | `consultation_list` config defined but NOT served by `GET /ui-config`. |
| C10 | LOW | `patients.yaml` | No `GET /patients/{id}` or `PUT/PATCH /patients/{id}` endpoints. |
| C11 | INFO | All HTTP contracts | ALL endpoints have `operationId` and proper `security` declarations. |
| C12 | INFO | `ui-config.yaml` | Gold standard -- `additionalProperties: false` everywhere. |

---

## A.14 Documentation Findings

| # | Severity | Issue |
|---|----------|-------|
| DOC1 | MEDIUM | **CLAUDE.md reading order conflicts with docs/implementation-prompt.md.** CLAUDE.md reads ai-context-rules first; docs/ reads business-rules first. Priority resolution order is consistent across both, but reading order diverges. |
| DOC2 | MEDIUM | **Two divergent copies of implementation-prompt.md.** `.ai-utils/` version matches CLAUDE.md (stale). `docs/` version is the corrected version. Delete `.ai-utils/implementation-prompt.md`. |
| DOC3 | MEDIUM | `01-repository-layout.md` says CLAUDE.md "should mirror" implementation-prompt.md but they disagree on reading order. |
| DOC4 | LOW | URL parameter naming: `{consultation_id}` in tech specs vs `{id}` in contract inventory. |
| DOC5 | LOW | DEC-007 note about updating Section 13 title is stale (fix was already applied). |
| DOC6 | INFO | No local file path leaks found (the README.md paths were cleaned up). |
| DOC7 | INFO | State machine is fully consistent across all documents. |

---

## A.15 Website Findings

| # | Severity | Issue |
|---|----------|-------|
| W1 | MEDIUM | No security headers (`Content-Security-Policy`, `X-Frame-Options`, `Referrer-Policy`). |
| W2 | MEDIUM | Two `href="#"` placeholder CTAs ("Entrar", "Solicitar acesso"). |
| W3 | MEDIUM | about.html and pricing.html lack site header/nav -- no navigation. |
| W4 | LOW | Pricing page has no actual pricing data or feature comparison. |
| W5 | LOW | No `<meta name="description">` on about.html/pricing.html (SEO). |
| W6 | LOW | Empty `images/` directory (no favicon, logo, OG image). |
| W7 | INFO | No footer with legal/privacy/terms links. |
| W8 | INFO | All text correctly in pt-BR. Plan names match backend enum. |

---

## A.16 Security Audit Findings

| # | Severity | Issue |
|---|----------|-------|
| S1 | MEDIUM | **MFA disabled** for a medical/PHI application. Should be at minimum optional. |
| S2 | MEDIUM | **`validate_ws_token()` called in connect_handler but NOT defined** in AuthProvider port or CognitoAuthProvider adapter. Will crash at runtime (`AttributeError`). |
| S3 | MEDIUM | **No schema validation library** (Pydantic, marshmallow). All validation is manual presence checks. No type/format/length enforcement. |
| S4 | MEDIUM | **`SecretValue.unsafe_plain_text`** placeholder values visible in CloudFormation template. |
| S5 | MEDIUM | **No per-endpoint rate limiting** on login/forgot-password beyond API GW stage limits. |
| S6 | MEDIUM | Prompt injection risk when AI pipeline is implemented -- no defenses in current prompt templates. |
| S7 | LOW | AWS account ID hardcoded in config files (`183992492124`). |
| S8 | LOW | No API Gateway-level authorizer on WebSocket $connect (Lambda handles it, but defense-in-depth missing). |
| S9 | INFO | PHI logging discipline is excellent -- structured logs, no patient data logged anywhere. |
| S10 | INFO | Tenant isolation is architecturally sound -- `clinic_id` always server-derived from JWT. |
| S11 | INFO | CORS properly restrictive -- specific domains only, no wildcards. |

---

## A.17 Test Coverage Matrix

**Overall: ~28% coverage (11 of ~40 real modules tested, ~109 test cases)**

### Modules WITH tests (well-tested):
| Module | Tests | Quality |
|--------|-------|---------|
| `adapters/storage/s3_client.py` | 10 | GOOD |
| `adapters/storage/s3_artifact_repository.py` | 6 | GOOD |
| `adapters/storage/s3_transcript_repository.py` | 7 | GOOD |
| `adapters/transcription/elevenlabs_config.py` | 7 | GOOD |
| `adapters/transcription/elevenlabs_provider.py` | 27 | EXCELLENT |
| `domain/transcription/entities.py` | 4 | ADEQUATE |
| `domain/transcription/exceptions.py` | 10 | ADEQUATE |
| `domain/transcription/services.py` | 15 | EXCELLENT |
| `domain/transcription/value_objects.py` | 8 | GOOD |
| `bff/action_availability.py` | 14 | EXCELLENT |
| `shared/config.py` | 1 | MINIMAL |

### CRITICAL modules WITHOUT tests:
- **ALL 6 DynamoDB persistence adapters** (tenant isolation boundary -- must be tested)
- **ALL HTTP handlers** (auth, consultation, patient, session, middleware)
- **ALL WebSocket handlers** (router, connect, session_init, audio_chunk)
- **ALL application use cases** (auth, consultation, patient, session, transcription)
- **Cognito auth adapter** (authentication security)
- **container.py** (DI wiring)
- **ALL domain modules except transcription** (auth, consultation, patient, session, audit)

### conftest.py fixtures built but UNUSED:
`make_apigw_event()`, `make_sample_consultation()`, `make_sample_patient()`, `make_sample_audit_event()` -- all defined but no test file imports them. Scaffolding for future tests.

---

## A.18 Top 10 Most Urgent Issues (Cross-Agent Consensus)

1. **CRITICAL: No entitlement enforcement on consultation creation** (U1) -- free plan users unlimited consultations
2. **CRITICAL: Zero error handling on ALL DynamoDB calls** (A1) -- any AWS error crashes the Lambda
3. **HIGH: MFA disabled for health data app** (I1, S1) -- HIPAA/LGPD non-compliance risk
4. **HIGH: `validate_ws_token()` not implemented** (S2) -- WebSocket $connect crashes at runtime
5. **HIGH: ~72% of modules have zero test coverage** (A.17) -- TDD violation
6. **HIGH: Feature flags hardcoded ignoring plan type** (B1) -- export/insights always enabled
7. **HIGH: Dev defaults silently used in production** (B2) -- wrong DB/bucket if env var missing
8. **HIGH: No prompt injection defenses** (PR2) -- when AI pipeline goes live
9. **HIGH: All prompts are placeholders** (PR1) -- 200-300 byte stubs, not production-ready
10. **MEDIUM: Reading order conflict across 3 files** (DOC1, DOC2) -- AI agents get inconsistent instructions

---
---

# APPENDIX B: AWS Infrastructure Deep Audit (15 Parallel Agents, 2026-04-03)

Pre-investigation of the CDK code and deployment configuration by 15 specialized agents. Cross-referenced against reported runtime errors from the live AWS dev environment.

**Total AWS findings: ~80+**
**Runtime-breaking bugs confirmed: 5**

---

## B.1 Confirmed Runtime Bugs (from reported errors + code verification)

### BUG #1: KMS AccessDeniedException on Secrets Manager -- CONFIRMED

**Severity: CRITICAL (actively failing)**

The Lambda execution role has KMS `Decrypt` permission only for `data_key`, but both secrets (`deskai/dev/elevenlabs` and `deskai/dev/claude`) are encrypted with `secrets_key`. When Lambda calls `GetSecretValue`, Secrets Manager tries to decrypt via `secrets_key` -- Lambda gets `AccessDeniedException`.

**Root cause in code:**
- `security_stack.py`: `self.elevenlabs_secret = ... encryption_key=self.secrets_key`
- `compute_stack.py`: KMS policy only grants `resources=[data_key.key_arn]` -- `secrets_key` is MISSING
- `app.py`: `secrets_key` is never passed to `ComputeStack`

**Exact fix (2 files):**

File 1 -- `infra/stacks/compute_stack.py`: Add `secrets_key: kms.IKey` parameter to constructor. Change KMS policy:
```python
resources=[data_key.key_arn, secrets_key.key_arn],  # was: [data_key.key_arn]
```

File 2 -- `infra/app.py`: Add to ComputeStack instantiation:
```python
secrets_key=security.secrets_key,
```

---

### BUG #2: SNS Alert Topic Has ZERO Subscribers -- CONFIRMED

**Severity: CRITICAL (monitoring is deaf)**

The `{prefix}-alerts` SNS topic is created in `orchestration_stack.py` with no subscriptions. All 6 CloudWatch alarms + 2 budget alerts publish to this topic but nobody receives anything. The topic is encrypted with KMS (good) but has zero subscribers.

**No subscriber is added ANYWHERE in the entire codebase** -- not in orchestration_stack, not in monitoring_stack, not in budget_stack, not in app.py.

**Config gap**: `EnvironmentConfig` has no `alert_email` field. No email address exists in any config.

**Fix (CDK + CLI):**

CDK (permanent): Add `alert_email` to `EnvironmentConfig`, add `sns.Subscription(protocol=EMAIL)` in `orchestration_stack.py`.

CLI (immediate): `aws sns subscribe --topic-arn arn:aws:sns:us-east-1:183992492124:deskai-dev-alerts --protocol email --endpoint YOUR_EMAIL`

---

### BUG #3: CloudFront Has No Custom Domain Aliases -- CONFIRMED

**Severity: CRITICAL (CORS blocks API calls)**

Both CloudFront distributions serve from raw `*.cloudfront.net` URLs. The CORS config on the HTTP API only allows `https://app.dev.deskai.com.br` and `https://dev.deskai.com.br`. Result: accessing the app via CloudFront URL triggers CORS rejection on every API call.

CDK `cdn_stack.py` does NOT configure `domain_names` or ACM certificates on either distribution. No Route53 records are defined.

**Workaround options:**
1. Add CloudFront URLs to CORS origins (quick fix for dev)
2. Wire custom domains with ACM certs (proper fix for prod)

---

### BUG #4: Missing `consultation-session-index` GSI -- NEW CRITICAL

**Severity: CRITICAL (runtime crash)**

`DynamoDBSessionRepository` queries `IndexName="consultation-session-index"` but this GSI does NOT exist in `storage_stack.py`. Only 3 GSIs exist: `gsi_doctor_date`, `gsi_status`, `gsi_patient`. Any session lookup by consultation ID will throw `ValidationException`.

**Additionally**: 2 of the 3 existing GSIs are DEAD -- `gsi_status` (GSI2PK/GSI2SK) and `gsi_patient` (GSI3PK/GSI3SK) are never populated by any code. Zero items in these indexes.

---

### BUG #5: `DESKAI_WEBSOCKET_URL` Defaults to localhost in Lambda -- NEW CRITICAL

**Severity: CRITICAL (real-time streaming broken)**

`config.py` reads `DESKAI_WEBSOCKET_URL` with default `"wss://localhost:3001"`. This env var is NOT set in CDK's `_shared_environment`. When `POST /v1/consultations/{id}/session/start` is called, the response includes `websocket_url: "wss://localhost:3001"` -- the frontend will try to open a WebSocket to localhost, which fails silently.

This is a chicken-and-egg problem: the WebSocket API URL is only known after `ApiStack` creates it, but `ComputeStack` (which sets Lambda env vars) is created before `ApiStack`.

---

## B.2 Lambda Configuration Findings

| # | Severity | Finding |
|---|----------|---------|
| L1 | HIGH | **All 4 Lambdas: 256MB / 30s timeout.** Pipeline handler needs 512-1024MB and 120-300s for AI/LLM calls. Export handler needs 512MB / 60-120s. |
| L2 | HIGH | **5 missing env vars** not set in CDK: `DESKAI_CONTRACT_VERSION`, `DESKAI_UI_CONFIG_KEY`, `DESKAI_COGNITO_CLIENT_SECRET_NAME`, `DESKAI_WEBSOCKET_URL`, `DESKAI_MAX_SESSION_DURATION_MINUTES` |
| L3 | HIGH | **`DESKAI_COGNITO_CLIENT_SECRET_NAME`** falls back to `"deskai/dev/cognito"` in prod. IAM policy doesn't grant access to any cognito secret. |
| L4 | MEDIUM | No reserved concurrency on any Lambda -- runaway scaling possible |
| L5 | MEDIUM | No DLQ configured directly on any Lambda function |
| L6 | MEDIUM | `DESKAI_RESOURCE_PREFIX` set in CDK but never read by code (dead config) |
| L7 | LOW | `.env.example` references stale `DESKAI_DEEPGRAM_SECRET_NAME` (renamed to ElevenLabs) |

---

## B.3 DynamoDB Findings

| # | Severity | Finding |
|---|----------|---------|
| DB1 | CRITICAL | Missing GSI `consultation-session-index` -- session repo queries it but it doesn't exist |
| DB2 | HIGH | 2 dead GSIs (`gsi_status`, `gsi_patient`) -- CDK creates them but no code populates GSI2PK/GSI2SK or GSI3PK/GSI3SK |
| DB3 | MEDIUM | No `deletion_protection` on table (separate from removal policy) |
| DB4 | MEDIUM | No TTL attribute configured |
| DB5 | MEDIUM | No DynamoDB Streams enabled |
| DB6 | LOW | CDK tests only check GSI names exist, not key schemas or projections |
| DB7 | INFO | Single-table design with 5 entity types is well-structured. PK/SK patterns are consistent and non-overlapping. PITR enabled. KMS encryption. On-demand billing. |

---

## B.4 API Gateway Findings

| # | Severity | Finding |
|---|----------|---------|
| AG1 | CRITICAL | **WebSocket API has NO authorizer on `$connect`** -- anyone with the URL can connect |
| AG2 | CRITICAL | **WebSocket API has NO rate limiting** -- connection/message flooding possible |
| AG3 | HIGH | **WebSocket API has NO access logging** -- blind spot for incident response |
| AG4 | MEDIUM | HTTP access log format is minimal (missing: sourceIp, httpMethod, userAgent, latency, errorMessage) |
| AG5 | MEDIUM | `DELETE /v1/auth/session` (logout) has no API Gateway authorizer (relies on handler-level auth) |
| AG6 | MEDIUM | No custom domains or ACM certificates on either API |
| AG7 | INFO | HTTP API CORS properly configured: specific origins, credentials, explicit headers |
| AG8 | INFO | HTTP API rate limiting: burst=100, rate=200. Access logging enabled. |
| AG9 | INFO | BFF router handles ALL API Gateway routes correctly. No dead handlers. |

---

## B.5 Cognito Findings

| # | Severity | Finding |
|---|----------|---------|
| CG1 | CRITICAL | **MFA is OFF** -- LGPD/HIPAA requires MFA for health data access |
| CG2 | HIGH | No user pool deletion protection |
| CG3 | HIGH | No advanced security / adaptive auth (compromised credential detection, bot detection) |
| CG4 | HIGH | Token lifetimes use Cognito defaults (30-day refresh) -- stolen token grants 30 days access |
| CG5 | HIGH | `TooManyRequestsException` not handled in adapter -- rate-limited requests get generic error |
| CG6 | MEDIUM | `USER_PASSWORD_AUTH` flow sends password over TLS (SRP would be more secure) |
| CG7 | MEDIUM | `PasswordResetRequiredException` not handled -- leaks account state |
| CG8 | MEDIUM | No breached password check (OWASP recommends HaveIBeenPwned integration) |
| CG9 | LOW | No Lambda triggers for audit logging of sign-ins |
| CG10 | INFO | Password policy exceeds OWASP minimums (12 chars, all types). Self-signup disabled. User enumeration prevented. |

---

## B.6 S3 Findings

| # | Severity | Finding |
|---|----------|---------|
| S1 | MEDIUM | **No S3 access logging** on any of the 3 buckets |
| S2 | MEDIUM | **S3Client never sets object tags** -- lifecycle rules depend on `audio_retention` tags but code never tags objects. Retention rules are dead code. |
| S3 | LOW | Backend writes lack explicit SSE headers (mitigated by bucket default KMS encryption) |
| S4 | LOW | No bucket policy enforcing encryption on PutObject |
| S5 | LOW | No lifecycle rules for non-audio artifacts (JSON, PDF) -- these never expire |
| S6 | INFO | All 3 buckets: BLOCK_ALL public access, versioning, SSL enforced. Artifacts bucket KMS-encrypted. |

---

## B.7 IAM Findings

| # | Severity | Finding |
|---|----------|---------|
| IAM1 | HIGH | **KMS `secrets_key` not granted** to Lambda role (confirmed Bug #1) |
| IAM2 | MEDIUM | `execute-api:ManageConnections` uses wildcard API ID (`*`) -- any WS API in account |
| IAM3 | MEDIUM | All 4 Lambdas share one IAM role -- export handler has Cognito auth perms, BFF has AI secret access |
| IAM4 | INFO | Zero `Action: *` statements anywhere. Only `resources=["*"]` is XRay (required by AWS). Permissions boundary attached to both roles. All resources prefix-scoped. |

---

## B.8 Step Functions / Orchestration Findings

| # | Severity | Finding |
|---|----------|---------|
| SF1 | CRITICAL | **Pipeline handler is a stub** returning fake success -- state machine "completes" without doing real work |
| SF2 | HIGH | Orchestration tests only check resource counts -- zero property assertions for encryption, DLQ config, retry |
| SF3 | HIGH | Step Functions retry is unfiltered -- retries ALL errors including non-transient (validation, bad input) |
| SF4 | MEDIUM | No per-task timeout/heartbeat on LambdaInvoke step -- relies on 15-min state machine timeout |
| SF5 | MEDIUM | Processing queue created but has NO consumer (no Lambda SQS event source mapping) |
| SF6 | MEDIUM | No EventBridge archive configured -- events lost if state machine is unavailable |
| SF7 | MEDIUM | No EventBridge bus resource policy -- any in-account principal can publish |
| SF8 | INFO | SQS queues encrypted with KMS. DLQ wired with maxReceiveCount=3. Tracing enabled. Dedicated IAM role with boundary. |

---

## B.9 Monitoring Findings

| # | Severity | Finding |
|---|----------|---------|
| MON1 | CRITICAL | **Export handler has ZERO monitoring** -- no alarm, not on dashboard, not passed to monitoring stack |
| MON2 | HIGH | No Lambda DURATION alarms -- approaching-timeout not detected |
| MON3 | HIGH | No Lambda THROTTLE alarms -- throttled invocations invisible |
| MON4 | HIGH | No WebSocket API error alarm (only HTTP API has 5xx alarm) |
| MON5 | MEDIUM | No DynamoDB throttle alarm |
| MON6 | MEDIUM | No Cognito sign-in failure alarm |
| MON7 | MEDIUM | No EventBridge FailedInvocations alarm |
| MON8 | MEDIUM | No SQS message age alarm (stuck messages undetected) |
| MON9 | LOW | Dashboard has no latency/duration widgets |
| MON10 | INFO | 6 existing alarms correctly configured with NOT_BREACHING missing-data treatment. All route to alerts SNS topic (which needs subscribers). |

---

## B.10 Budget / Cost Findings

| # | Severity | Finding |
|---|----------|---------|
| BG1 | MEDIUM | Budget only alerts at 100% ($5) -- no early warnings at 50%/75% |
| BG2 | MEDIUM | No auto-stop enforcement -- budget is alerts-only, services keep running |
| BG3 | LOW | $5/month is tight -- KMS ($1) + Secrets Manager ($0.80) + CloudWatch alone consume ~$2.30+ |
| BG4 | LOW | Cost allocation tag (`environment`) must be manually activated in AWS Billing console |
| BG5 | INFO | Budget correctly scoped per environment via tag filter. Shared-account mode handles dev/prod separation. |

---

## B.11 Build & Deploy Findings

| # | Severity | Finding |
|---|----------|---------|
| BD1 | CRITICAL | **README deploy instructions skip `build-lambda`** -- `cdk deploy --all` without building first deploys stale/missing Lambda code |
| BD2 | CRITICAL | **CI doesn't watch `backend/**`** -- backend code changes don't trigger infra CI. Broken Lambda code can merge. |
| BD3 | HIGH | No automated deploy pipeline -- `deploy.yml` is a placeholder |
| BD4 | HIGH | Lambda deps not pinned (`>=` not `==`) -- builds not reproducible |
| BD5 | HIGH | No `cdk diff` step in any workflow or documented process |
| BD6 | MEDIUM | No `deploy` Makefile target that chains build + diff + deploy |
| BD7 | MEDIUM | No `__pycache__`/`.dist-info` cleanup in build script -- bloats Lambda package |
| BD8 | MEDIUM | Manual sync between `requirements-lambda.txt` and `backend/pyproject.toml` |
| BD9 | LOW | No Lambda package size guard (250MB limit) |
| BD10 | LOW | `cdk.json` hardcodes `.venv/bin/python` -- fragile if venv name differs |
| BD11 | LOW | No security scanning (Checkov, cfn-nag, Trivy) in CI |

---

## B.12 Complete Environment Variable Matrix

| Env Var | In CDK? | In Code? | In .env.example? | Default | Risk |
|---------|---------|----------|-------------------|---------|------|
| `DESKAI_ENV` | YES | YES | YES | `"dev"` | Safe |
| `DESKAI_RESOURCE_PREFIX` | YES | NO | NO | N/A | Dead config |
| `DESKAI_DYNAMODB_TABLE` | YES | YES | YES | dev table name | Low |
| `DESKAI_ARTIFACTS_BUCKET` | YES | YES | YES | dev bucket name | Low |
| `DESKAI_ELEVENLABS_SECRET_NAME` | YES | YES | NO | dev secret name | Low |
| `DESKAI_CLAUDE_SECRET_NAME` | YES | YES | YES | dev secret name | Low |
| `DESKAI_COGNITO_USER_POOL_ID` | YES | YES | YES | `""` | RuntimeError guard |
| `DESKAI_COGNITO_CLIENT_ID` | YES | YES | YES | `""` | RuntimeError guard |
| `DESKAI_CONTRACT_VERSION` | NO | YES | YES | `"v1"` | Low |
| `DESKAI_UI_CONFIG_KEY` | NO | YES | YES | `"CONFIG#ui"` | Low |
| **`DESKAI_COGNITO_CLIENT_SECRET_NAME`** | **NO** | YES | YES | `"deskai/dev/cognito"` | **HIGH -- wrong secret in prod** |
| **`DESKAI_WEBSOCKET_URL`** | **NO** | YES | NO | `"wss://localhost:3001"` | **CRITICAL -- broken in Lambda** |
| `DESKAI_MAX_SESSION_DURATION_MINUTES` | NO | YES | NO | `"60"` | Low |

---

## B.13 Top 15 AWS Issues by Priority

**Fix IMMEDIATELY (blocking runtime):**
1. KMS `secrets_key` not granted to Lambda -- every secret read crashes
2. Missing `consultation-session-index` GSI -- session queries crash
3. `DESKAI_WEBSOCKET_URL` defaults to localhost -- real-time streaming broken
4. SNS topic zero subscribers -- monitoring is deaf
5. CloudFront no custom domains vs CORS -- API calls blocked from CDN

**Fix BEFORE any testing:**
6. Pipeline Lambda 30s/256MB too tight for AI calls
7. Export handler has zero monitoring
8. WebSocket API: no auth, no rate limiting, no logging
9. MFA OFF for health data
10. `DESKAI_COGNITO_CLIENT_SECRET_NAME` not in CDK

**Fix before production:**
11. No Cognito deletion protection or advanced security
12. Token lifetimes use unsafe defaults (30-day refresh)
13. No automated deploy pipeline
14. CI doesn't watch backend/** changes
15. Dead GSIs wasting resources + no DynamoDB deletion protection
