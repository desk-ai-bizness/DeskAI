# MVP Technical Specs

## 0. Purpose Of This File

This file is the technical source of truth for the MVP.

It is written to be easily consumed by humans and AI agents.

Rules for using this file:

- treat this file as the canonical technical context for the MVP
- prefer this file over older planning notes
- load `docs/ai-context-rules.md` before implementation or planning work
- keep business decisions in `mvp-business-rules.md`
- keep technical decisions, constraints, and architecture here
- keep summarized ADR entries in this file

## 1. Canonical MVP Decisions

These decisions are fixed unless explicitly changed.

### Product And Language

- market: Brazil
- user-facing language: Brazilian Portuguese (`pt-BR`)
- transcription language: Brazilian Portuguese (`pt-BR`)
- code language: English
- code comments language: English
- documentation language: English

### Experience

- MVP is real-time-first
- the primary workflow is live consultation streaming
- post-consultation upload is not the primary MVP path
- post-consultation upload may be added later as a fallback or secondary workflow

### Frontend

- frontend has two parts:
  - public website for landing and sales pages
  - authenticated React web app for logged-in users
- frontend role: presentation layer only
- frontend must be as dumb as possible
- frontend must not own business rules
- frontend must not own workflow rules
- frontend should receive backend-shaped data and backend-provided configuration

### Backend

- backend language: Python
- compute model: AWS Lambda
- architecture style: AWS serverless-first
- backend is split into:
  - core backend layer
  - BFF layer for frontend-facing contracts

### Authentication

- login method: email + password only
- no Google login
- no Facebook login
- no social login
- no enterprise SSO in MVP

### Infrastructure

- cloud: AWS
- environments: `dev`, `prod`
- infrastructure as code: AWS CDK
- primary data storage: DynamoDB + S3
- relational database: not part of MVP

## 2. Technical Principles

- optimize for low initial cost
- optimize for operational simplicity
- optimize for fast iteration with a small team
- keep components replaceable
- keep all frontend behavior backend-driven whenever practical
- prefer configuration over code for UI text, labels, sections, and non-visual workflow settings
- keep business logic in backend services, never in the frontend client
- design for scale, but do not prematurely add heavy infrastructure

### Project Architecture Rules

- backend must follow Hexagonal Architecture principles
- business rules must remain independent from frameworks, AWS services, and delivery mechanisms
- prefer domain-oriented design for complex business rules, even without fully adopting DDD
- prefer event-driven and async interactions when they improve resilience, decoupling, or scalability
- design for testability, observability, and replaceability from the start
- keep modules highly cohesive and loosely coupled
- prefer composition over inheritance

### ADR Rule

- important technical decisions must be documented as short ADR entries in this file
- ADRs must be concise, explicit, and easy for humans and AI agents to scan

## 3. System Overview

The MVP has four main technical layers:

1. Web frontend
2. BFF layer
3. Core backend layer
4. Infrastructure and data layer

### High-Level Responsibilities

#### Web Frontend

- authenticate the user
- render public marketing pages
- capture microphone audio
- open and maintain the real-time consultation session
- render screens, forms, transcript views, summaries, and insights
- consume backend-driven UI configuration
- send user actions to the BFF

#### BFF Layer

- expose frontend-specific APIs
- shape backend data into UI-friendly payloads
- aggregate multiple backend responses into one frontend response
- inject UI configuration, labels, and screen metadata
- keep frontend contracts stable even if core services evolve

#### Core Backend Layer

- manage consultation domain logic
- manage session lifecycle
- manage transcription provider integration
- run the AI post-processing pipeline
- persist consultation data and artifacts
- manage review, finalization, audit, and exports

#### Infrastructure Layer

- authentication
- API ingress
- WebSocket session transport
- storage
- orchestration
- logging, metrics, and security

## 4. Recommended AWS Architecture

### Required AWS Services

- `Amazon Cognito`
- `Amazon CloudFront`
- `Amazon API Gateway HTTP API`
- `Amazon API Gateway WebSocket API`
- `AWS Lambda`
- `AWS Step Functions Standard`
- `Amazon DynamoDB`
- `Amazon S3`
- `Amazon EventBridge`
- `Amazon SQS`
- `Amazon SNS`
- `AWS Budgets`
- `AWS Secrets Manager`
- `AWS KMS`
- `Amazon CloudWatch`

### Optional AWS Services

- `AWS WAF`
- `AWS X-Ray`

### Service Roles

#### Cognito

- native user authentication
- email + password only
- user pool only
- social and federated providers disabled
- password reset and email verification supported

#### CloudFront

- delivery layer for the public website and authenticated frontend assets
- cache and distribute static HTML, CSS, JavaScript, and other frontend assets

#### API Gateway HTTP API

- standard request/response endpoints
- authentication-protected frontend API
- BFF entrypoint

#### API Gateway WebSocket API

- real-time consultation session transport
- transcript event delivery
- session control messages
- backend-to-client notifications during an active consultation

#### Lambda

- BFF handlers
- core domain handlers
- provider adapters
- export generation
- webhook or callback handlers when needed

#### Step Functions Standard

- consultation completion workflow
- transcript consolidation
- AI generation orchestration
- retries and failure handling

#### DynamoDB

- metadata store
- workflow state store
- audit-oriented event records
- UI configuration storage when small and lookup-oriented

#### S3

- audio storage
- transcript artifact storage
- generated JSON artifact storage
- export storage
- larger frontend configuration blobs when useful

#### SNS

- notification channel for budget alerts and important operational alerts

#### AWS Budgets

- monthly cost alerting
- must notify the team if AWS spend exceeds `$5`

## 5. Environments

Only two environments exist in the MVP:

- `dev`
- `prod`

Rules:

- do not create a `staging` environment for the MVP
- all infrastructure must be isolated per environment
- Cognito, API Gateway, Lambda, DynamoDB, S3, and secrets must be separated between `dev` and `prod`
- treat `dev` as an AWS-hosted development environment, not as localhost runtime
- local developer machine execution is separate from AWS environment definitions
- if `dev` and `prod` share one AWS account, apply hardening controls:
  - environment tags on resources
  - environment-scoped budget filters
  - termination protection on `prod` stacks

Naming examples:

- `deskai-dev-api`
- `deskai-dev-consultations`
- `deskai-prod-api`
- `deskai-prod-consultations`

## 6. Frontend Architecture

### Stack

- public website:
  - standard HTML
  - CSS
  - minimal JavaScript only when needed
- authenticated app:
  - React
  - TypeScript
  - Vite

### Frontend Design Rule

The frontend is intentionally dumb.

That means:

- no business rules in the frontend client
- no domain calculations in the frontend
- no hardcoded workflow decisions in the frontend
- no hardcoded important product copy if it can be backend-configured
- no backend data reshaping in the frontend beyond small presentational mapping

### Frontend Split

#### Public Website

- used for landing pages, sales pages, and marketing pages
- built as standard HTML for strong SEO characteristics
- should avoid unnecessary SPA behavior
- should prioritize crawlability, performance, and simple deployment

#### Authenticated App

- used for the logged-in product area
- built as a React website
- consumes BFF APIs and real-time consultation endpoints
- handles authenticated product workflows only

### What The Frontend Is Allowed To Do

- local view state
- form input state
- connection state display
- browser audio device access
- audio buffering required for live streaming
- rendering backend-provided data
- rendering backend-provided UI configuration

### What The Frontend Must Not Do

- decide which fields are required based on business logic
- decide which insight types exist
- decide which review states are allowed
- embed clinic-specific copy or workflow rules in code
- transform raw backend domain objects into complex view models without the BFF

### Frontend Security Rules

- use secure authentication flows for browser-based login
- keep sensitive tokens out of persistent insecure storage when possible
- validate all client-to-backend requests on the server side
- use HTTPS everywhere
- apply CSP and related web security headers where practical

## 7. BFF Architecture

The BFF exists to keep the frontend simple and backend-driven.

### BFF Responsibilities

- authenticate and authorize frontend requests
- expose UI-oriented endpoints
- aggregate multiple backend responses
- convert domain objects into presentation objects
- attach UI configuration and text configuration
- shield the frontend from internal backend changes

### BFF Output Types

The BFF may return:

- screen payloads
- view models
- UI text bundles
- field schemas
- feature flags
- section ordering
- visibility rules
- action availability

### Configuration Over Code

For the MVP, prefer backend-managed configuration for:

- labels
- helper text
- warning banners
- field ordering
- section ordering
- feature visibility
- template variants
- clinic-specific text differences when needed later

Recommended rule:

- the frontend should render what the BFF tells it to render whenever possible

### Feature Flag Rule

- the MVP must include a feature flag system
- feature flags must support controlled rollout and rollback
- important product capabilities must be turnable on and off without frontend redeploys when practical
- feature flag evaluation should happen in backend or BFF layers, not in scattered frontend logic

## 8. Core Backend Architecture

### Language And Runtime

- Python 3.12
- AWS Lambda execution model

### Recommended Python Libraries

- `aws-lambda-powertools`
- `pydantic`
- `boto3`
- `httpx`
- `tenacity`

### Core Backend Modules

- `auth`
- `consultation`
- `session`
- `transcription`
- `ai_pipeline`
- `review`
- `export`
- `audit`
- `config`
- `shared`

### Core Backend Responsibilities

- consultation creation
- real-time session creation and termination
- provider session orchestration
- transcript normalization
- AI schema generation
- review persistence
- finalization
- export generation
- audit event creation
- UI configuration delivery to the BFF

### Backend Implementation Rules

- keep domain logic inside the core layer
- keep adapters for AWS services, external providers, and transport layers outside the domain core
- expose use cases through clear application services
- use retries for transient failures only
- always log failures with enough context for diagnosis
- prefer idempotent operations for async flows
- never hide errors silently

## 9. Authentication And Identity

### MVP Authentication Rule

- authentication is email + password only

### AWS Recommendation

- use Cognito User Pool native users
- use email as the login identifier
- disable Google, Facebook, Apple, and all other social providers
- disable SAML and OIDC federation for the MVP

### Login UX Recommendation

Preferred option:

- Cognito managed login or hosted login with only native email/password enabled

Alternative option:

- custom BFF login flow backed by Cognito APIs

Preferred default:

- use Cognito managed login to reduce auth complexity

### Required Auth Features

- email verification
- forgot password
- reset password
- account disablement by administrators later if needed

### Authorization And Plan Types

- authorization must support plan-aware permissions
- the supported doctor plan types are:
  - `free_trial`
  - `plus`
  - `pro`
- user permissions and feature access may vary by plan type
- role and permission checks must be enforced in backend or BFF layers, not only in the frontend

## 10. Real-Time Consultation Flow

This is the primary MVP flow.

### End-To-End Flow

1. User signs in with email and password.
2. Frontend creates a consultation through the BFF.
3. The authenticated React app opens a real-time consultation session.
4. Frontend streams audio chunks through the real-time path defined by the backend.
5. Backend forwards or brokers the stream to the selected transcription provider.
6. Backend receives partial transcript events.
7. BFF pushes transcript updates to the frontend.
8. When the consultation ends, backend finalizes transcript consolidation.
9. Backend stores transcript artifacts in S3.
10. Backend runs AI generation with strict schemas.
11. Backend stores generated artifacts in S3 and metadata in DynamoDB.
12. BFF returns structured, frontend-ready review payloads.
13. Physician reviews and edits outputs.
14. Backend stores the final confirmed version and audit data.

### Technical Notes

- partial transcript events may be persisted for resilience if needed
- final transcript must be normalized before AI generation
- AI generation runs after the consultation closes, not continuously during every audio chunk

## 11. Future Secondary Flow

This flow is not primary in the MVP.

### Post-Consultation Upload

Possible later addition:

- record locally
- upload after consultation
- process asynchronously
- use as fallback for weak connectivity or lower-cost operation

## 12. Transcription Provider Layer

The transcription provider must be abstracted behind an internal interface.

### Selected Provider

- ElevenLabs Scribe v2 Realtime (see ADR-006)

### Alternative Providers (if switching is needed)

- Google Cloud Speech-to-Text
- Azure AI Speech
- Deepgram

### Provider Interface

Implement an internal adapter contract with:

- `start_realtime_session(...)`
- `send_audio_chunk(...)`
- `finish_realtime_session(...)`
- `get_session_state(...)`
- `fetch_final_transcript(...)`

Future secondary methods:

- `submit_batch_job(...)`
- `get_batch_job_status(...)`

### Normalized Transcript Model

All provider responses must be normalized into one internal structure.

Required normalized fields:

- consultation_id
- provider_name
- provider_session_id
- language
- transcript_text
- speaker_segments
- timestamps_when_available
- confidence_metadata_when_available

## 13. AI Processing Layer

Use strict-schema processing only.

The LLM provider for the MVP is Claude API (Anthropic). See `docs/requirements/05-decision-log.md` DEC-007.

### Required Modules

- conversation parser
- medical history generator
- summary generator
- insight generator

### Rules

- prompts are authored in English
- schemas are authored in English
- generated clinical content returned to the product is in `pt-BR`
- every insight includes evidence references
- no free-form unstructured output should be trusted as final

## 14. Data Storage Strategy

### Storage Decision

Use:

- DynamoDB for metadata and operational records
- S3 for large artifacts and JSON outputs

Do not use PostgreSQL in the MVP.

### Why This Is The MVP Choice

- fully serverless
- low idle-cost risk
- no database operations burden
- suitable for consultation-centric access patterns
- scalable from small traffic without replatforming

### When To Reconsider PostgreSQL Later

- many relational joins become essential
- BI/reporting needs become relational and ad hoc
- operational queries no longer fit clear DynamoDB access patterns

## 15. DynamoDB Model

### Table Strategy

- prefer a single-table design for the MVP

### Main Table Example

- table name: `deskai-{env}-consultation-records`

### Keys

- partition key: `PK`
- sort key: `SK`

### Entity Patterns

- clinic metadata
  - `PK=CLINIC#<clinic_id>`
  - `SK=METADATA`
- consultation metadata
  - `PK=CLINIC#<clinic_id>`
  - `SK=CONSULTATION#<consultation_id>`
- consultation artifact pointer
  - `PK=CONSULTATION#<consultation_id>`
  - `SK=ARTIFACT#<artifact_type>`
- consultation audit event
  - `PK=CONSULTATION#<consultation_id>`
  - `SK=AUDIT#<timestamp>`
- doctor consultation access entity
  - `PK=DOCTOR#<doctor_id>`
  - `SK=CONSULTATION#<date_time>#<consultation_id>`
- UI configuration entity
  - `PK=CONFIG#<scope>`
  - `SK=VERSION#<version>`

### Suggested GSIs

- consultations by doctor and date
- consultations by status
- consultations by patient

### What Lives In DynamoDB

- consultation metadata
- workflow state
- provider selection
- finalization metadata
- audit events
- S3 object references
- compact summary/search fields
- UI configuration metadata

## 16. S3 Layout

### What Lives In S3

- raw audio artifacts
- transcript artifacts
- generated JSON artifacts
- exported files
- larger UI configuration payloads when needed

### Backup And Disaster Recovery

- core consultation metadata in DynamoDB must use point-in-time recovery
- S3 buckets for core artifacts must use versioning when appropriate
- define restore procedures for critical consultation data
- define recovery priorities for:
  - consultation metadata
  - final reviewed notes
  - generated artifacts
  - raw audio when retained by policy
- disaster recovery design can remain lightweight in the MVP, but it must exist

### Key Layout Example

```text
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/audio/raw.<ext>
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/transcripts/raw.json
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/transcripts/normalized.json
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/ai/medical_history.json
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/ai/summary.json
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/ai/insights.json
s3://<bucket>/clinics/<clinic_id>/consultations/<consultation_id>/exports/final.pdf
```

## 17. API Contract Shape

The frontend should speak primarily to the BFF, not to deep domain services directly.

### HTTP Endpoints

- `POST /v1/auth/session`
- `DELETE /v1/auth/session`
- `GET /v1/me`
- `POST /v1/patients`
- `GET /v1/patients`
- `POST /v1/consultations`
- `GET /v1/consultations`
- `GET /v1/consultations/{consultation_id}`
- `POST /v1/consultations/{consultation_id}/session/start`
- `POST /v1/consultations/{consultation_id}/session/end`
- `GET /v1/consultations/{consultation_id}/review`
- `PUT /v1/consultations/{consultation_id}/review`
- `POST /v1/consultations/{consultation_id}/finalize`
- `POST /v1/consultations/{consultation_id}/export`
- `GET /v1/ui-config`

### WebSocket Routes

- `$connect`
- `$disconnect`
- `session.init`
- `audio.chunk`
- `session.stop`
- `client.ping`

### BFF Response Style

BFF responses should be:

- frontend-ready
- explicit
- versionable
- stable
- locale-aware

### CORS Policy

- define an explicit CORS policy
- do not use wildcard origins in production unless there is a documented exception
- allow only the minimum required origins, headers, and methods
- keep dev and prod CORS settings separated

## 18. UI Configuration Strategy

The backend should own important frontend configuration.

### Backend-Driven UI Items

- labels
- helper copy
- warnings
- field groups
- section order
- card order
- default visibility
- review page composition

### Recommended Storage

Use:

- DynamoDB for small configuration metadata and active versions
- S3 for larger versioned JSON configuration documents

### Frontend Rule

- frontend renders backend-provided config
- frontend may have minimal fallback strings only for technical failure states

## 19. Security And Privacy

### Required Controls

- TLS everywhere
- KMS encryption for S3 and DynamoDB
- least-privilege IAM roles
- secrets in Secrets Manager
- tenant-aware access control
- audit logs for critical actions
- configurable audio retention
- sensitive data masking or obfuscation where practical

### IAM Rule

- follow least-privilege IAM for all AWS resources
- separate permissions by service responsibility
- do not share broad wildcard permissions across unrelated Lambda functions
- review IAM permissions whenever new infrastructure or providers are added

### Logging Rules

- do not log raw audio
- do not log full transcript text by default
- minimize PHI in logs
- use structured logs with request ids and consultation ids

## 20. Observability

Track at minimum:

- sign-in success and failure rate
- consultation creation count
- session start success rate
- audio ingestion success rate
- transcript provider latency
- transcript provider failure rate
- AI generation success and failure rate
- consultation processing time
- review completion time
- export success rate

Alert on:

- Lambda error spikes
- Step Functions failures
- WebSocket disconnect spikes
- SQS dead-letter queue growth
- provider outage or sustained high failure rate

### Error Handling Rule

- all critical errors must be logged with structured context
- retries must be automatic only for transient failures
- retry policies must use bounded attempts and backoff
- see `docs/requirements/04-failure-behavior-matrix.md` for concrete retry budgets, backoff strategies, and user-facing error messages per failure path

## 21. Cost Strategy

- keep the architecture serverless
- keep only `dev` and `prod`
- use DynamoDB on-demand
- store large artifacts in S3
- avoid RDS in MVP
- avoid Kubernetes in MVP
- avoid Redis in MVP
- avoid OpenSearch in MVP
- keep the BFF thin and focused

### Cost Guardrail

- create an AWS budget alert that notifies the team if monthly spend exceeds `$5`
- route the alert through SNS or another simple notification channel

## 22. Infrastructure As Code

Use AWS CDK.

### Required Rule

- all AWS infrastructure for the MVP must be defined in AWS CDK

### Language Recommendation

- use AWS CDK with Python to stay aligned with the backend stack

### CDK Scope

CDK should provision:

- CloudFront distributions
- Cognito
- HTTP API
- WebSocket API
- Lambda functions
- Step Functions
- DynamoDB tables
- S3 buckets
- EventBridge rules
- SQS queues
- SNS topics
- AWS Budgets alerting resources when supported by the chosen CDK approach
- KMS keys
- Secrets Manager entries
- CloudWatch alarms and dashboards where practical

## 23. Testing Strategy

### TDD Workflow

All code where tests are applicable must follow strict Test-Driven Development:

1. **Red** — Write a failing test that defines the expected behavior. Run it. It must fail.
2. **Green** — Write the minimum implementation code to make the test pass.
3. **Refactor** — Clean up the code while keeping all tests green.

Rules:

- Every new function, module, endpoint, adapter, handler, or infrastructure construct gets its test first.
- Every bug fix starts with a failing test that reproduces the bug before fixing it.
- No speculative implementation code that is not driven by a test.
- All tests must pass before committing.
- No production code may be merged without corresponding tests passing in CI.

### Test Types and Scope

| Type | Scope | Tools | TDD Applies |
| --- | --- | --- | --- |
| Unit | Domain entities, value objects, services, business rules | pytest | Yes — always |
| Application | Use cases with mocked port interfaces | pytest, unittest.mock | Yes — always |
| Integration (adapter) | DynamoDB, S3, Cognito, Secrets Manager adapters against emulated services | pytest, moto or localstack | Yes — write expected behavior first |
| Integration (handler) | Lambda handlers with event fixtures and context mocks | pytest | Yes — write expected response first |
| BFF | View models, feature flag evaluation, UI config assembly | pytest | Yes — always |
| Infrastructure | CDK stack synthesis resource and property assertions | unittest, aws_cdk.assertions | Yes — assert resource properties before adding constructs |
| Contract | YAML schema validation, API response shape compliance | pytest, schema validators | Yes — validate contract compliance before implementation |
| API | HTTP request/response round-trips against running or mocked endpoints | pytest, httpx or test client | Yes — write expected status and body first |
| End-to-end | Full consultation lifecycle through the deployed stack | pytest (integration suite) | Acceptance-driven — write expected outcomes first |

### What Does Not Require TDD

- Pure configuration files (`.env`, `cdk.json`, YAML configs without logic).
- Static assets (HTML, CSS, images, fonts).
- One-off migration scripts — but must have verification tests before execution.
- Exploratory prototypes — but tests must exist before merging to main.

### Test Organization

```
backend/
├── tests/
│   ├── unit/
│   │   ├── domain/                # Pure unit tests, no mocks needed
│   │   ├── application/           # Use case tests, mocked ports
│   │   └── bff/                   # View model and feature flag tests
│   ├── integration/
│   │   ├── adapters/              # Adapter tests against emulated services
│   │   └── handlers/              # Lambda handler tests with event fixtures
│   └── conftest.py                # Shared fixtures

infra/
├── tests/
│   ├── test_config.py             # Environment configuration assertions
│   └── test_stacks.py             # CDK stack synthesis assertions

app/
├── src/**/*.test.ts               # Frontend component and integration tests (colocated)

contracts/
├── tests/                         # Contract schema validation tests
```

### Test Quality Rules

- Tests must be deterministic. No flaky tests. No time-dependent assertions without mocking.
- Tests must be fast. Unit tests should complete in under one second each. Integration tests should complete in under ten seconds each.
- Tests must be isolated. No shared mutable state between tests. Each test sets up and tears down its own context.
- Test names must clearly describe the expected behavior, not the implementation.
- Prefer explicit assertions over broad catch-all checks.
- Test coverage is a signal, not a target. One hundred percent coverage is not required, but untested critical paths are not acceptable.

### Per-Layer Testing Rules

These complement the existing rules in `docs/architecture/02-backend-architecture.md` section 9:

- Domain tests are pure unit tests. No mocks needed because domain has no external dependencies.
- Application tests mock port interfaces using standard Python mocking. The port contract is the test boundary.
- Adapter integration tests use moto or localstack to emulate AWS services. They validate that the adapter correctly translates domain operations into service calls.
- Handler tests use Lambda event fixtures that match the API Gateway or Step Functions event format. They validate routing, input parsing, and response shape.
- BFF tests verify view model transformation, feature flag evaluation, and UI configuration assembly without real backend calls.
- Infrastructure tests use CDK assertions to validate synthesized CloudFormation templates. They guard structural invariants like encryption, access controls, and resource counts.
- Contract tests validate that backend responses match the YAML contract schemas in `contracts/`.
- E2E tests are driven by acceptance criteria from task files. They exercise the full flow from API request to storage and back.

## 24. Technical Non-Goals For MVP

Do not include in the MVP:

- social login
- SSO federation
- PostgreSQL
- Kubernetes
- multi-region deployment
- deep EHR integration
- complex analytics warehouse
- search infrastructure
- frontend-owned business logic

## 25. ADRs

### ADR-001: Storage Model

- decision: use `DynamoDB + S3` instead of PostgreSQL in the MVP
- reason: lower operational burden, lower idle-cost risk, better fit for serverless-first delivery

### ADR-002: Frontend Role

- decision: keep the frontend intentionally dumb and backend-driven
- reason: centralize product behavior, reduce duplication, and allow configuration over code

### ADR-003: Backend Architecture Style

- decision: backend follows Hexagonal Architecture principles
- reason: keep business rules independent from AWS services, frameworks, and delivery mechanisms

### ADR-004: Environments

- decision: use only `dev` and `prod` in the MVP
- reason: reduce operational cost and complexity during the early stage

### ADR-005: Infrastructure As Code

- decision: use AWS CDK
- reason: keep AWS infrastructure defined as code and aligned with the project stack

### ADR-006: Transcription Provider

- decision: use ElevenLabs Scribe v2 Realtime as the first transcription provider
- previous decision: Deepgram Nova-2 Medical (superseded — higher WER for pt-BR, lower benchmark accuracy)
- reason: lowest WER for pt-BR (3.1% FLEURS), 150ms latency, native WebSocket streaming, keyterm prompting for medical vocabulary (up to 1,000 terms), 90+ languages, HIPAA/SOC 2/GDPR compliant
- reversibility: high — provider is behind an adapter interface
- reference: `docs/requirements/05-decision-log.md` DEC-001

### ADR-007: LLM Provider

- decision: use Claude API (Anthropic) for the AI processing pipeline
- reason: strong structured output capabilities, schema-strict generation support, aligns with project guidance
- reversibility: high — LLM is behind an adapter interface
- reference: `docs/requirements/05-decision-log.md` DEC-007

### ADR-008: Plan Entitlement Model

- decision: all three plans share core features; differentiation is by usage limits only (consultation count, session duration, audio retention)
- reason: MVP prioritizes reliability over feature segmentation; billing is post-MVP
- reversibility: high — limits are feature-flag-driven configuration
- reference: `docs/requirements/03-plan-entitlements.md`

### ADR-009: Repository Layout

- decision: monorepo with flat top-level packages (`backend/`, `app/`, `website/`, `contracts/`, `infra/`)
- reason: small team benefits from colocation; flat structure keeps navigation simple; shared contracts prevent schema drift
- reversibility: medium — moving to separate repos is possible but requires CI/CD changes
- reference: `docs/architecture/01-repository-layout.md`

### ADR-010: Backend Module Organization

- decision: domain-first hexagonal layout with centralized ports and grouped adapters by infrastructure concern
- reason: keeps domain logic pure and framework-free; adapters are replaceable per concern; avoids premature per-feature module isolation for a small team
- reversibility: high — modules can be split further as the team grows
- reference: `docs/architecture/02-backend-architecture.md`

### ADR-011: Dependency Injection

- decision: use constructor injection with simple factory functions in `container.py`, no DI framework
- reason: minimal complexity for MVP; factory functions are easy to test and replace; avoids framework lock-in
- reversibility: high — can adopt a DI library later without changing domain or application code
- reference: `docs/architecture/02-backend-architecture.md` section 10

### ADR-012: Contract Location

- decision: shared schemas in a top-level `contracts/` directory, separate from backend and frontend code
- reason: single source of truth for API shapes, consumed by both backend (validation) and frontend (type generation); prevents schema drift
- reversibility: high — schemas can be moved closer to consumers if the shared approach becomes unwieldy
- reference: `docs/architecture/03-contract-inventory.md`

### ADR-013: UI Configuration and Feature Flag Flow

- decision: UI configuration and feature flags are stored in DynamoDB, assembled by the BFF layer, and delivered to the frontend as ready-to-render payloads; the frontend never evaluates plan-based limits, computes flag values, or hardcodes business labels
- reason: centralizes product behavior in the backend; allows config changes without frontend deploys; enforces the backend-driven frontend principle (ADR-002) with a concrete mechanism
- reversibility: high — storage can move from DynamoDB to S3 or a config service without changing the BFF-to-frontend contract
- reference: `docs/architecture/04-data-flow-and-configuration.md`

### ADR-014: Patient Endpoints

- decision: add minimal `POST /v1/patients` and `GET /v1/patients` endpoints to the API contract
- reason: consultations require a `patient_id`; without patient CRUD, consultations cannot be created without hardcoding IDs
- reversibility: high — endpoints can be extended with more fields later
- reference: `docs/architecture/03-contract-inventory.md` section 2, resolves OPEN-005

### ADR-015: Authenticated App Icon Library

- decision: use `lucide-react` as the authenticated app icon library
- reason: small tree-shakeable React icon package, simple accessibility handling, and enough neutral medical-product UI icons for MVP primitives
- reversibility: high — icons are wrapped by the app-local `Icon` primitive in `app/src/components/ui`
- reference: `tasks/017-create-authenticated-app-design-system.md`

### ADR-016: Authenticated App Query Cache

- decision: use `@tanstack/react-query` for in-memory HTTP server-state caching in the authenticated React app
- reason: centralizes request loading, error, refetch, mutation, and invalidation behavior while keeping page components presentation-focused
- safeguards: cache persistence is disabled; global retries are disabled by default; sign-out clears the query client; WebSocket session state remains explicit and outside the HTTP query cache
- reversibility: high — endpoint transport remains in `app/src/api/endpoints.ts`, and app-local query hooks wrap the dependency boundary
- reference: `tasks/019-add-frontend-query-cache-and-loading-states.md`

## 26. AI Agent Notes

If an AI agent uses this file as project context, assume the following:

- load `docs/ai-context-rules.md` first
- the frontend is intentionally dumb
- the public website is standard HTML for SEO-sensitive pages
- the logged-in product area is a React website
- the BFF is mandatory, not optional
- UI configuration should be backend-driven whenever practical
- email/password auth is mandatory
- only `dev` and `prod` environments exist
- AWS CDK is mandatory for infrastructure changes
- DynamoDB + S3 is the approved MVP storage model
- real-time streaming is the primary MVP workflow
- post-consultation upload is secondary and later
- use `docs/requirements/01-requirements-traceability-matrix.md` to verify implementation completeness against business rules
- use `docs/requirements/04-failure-behavior-matrix.md` for concrete retry budgets and error handling behavior
