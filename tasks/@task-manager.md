# Task Manager

## 1. Purpose

This file is the central progress tracker for all task files inside `/tasks`.

It is designed for both humans and artificial intelligence to:
- understand the current project status quickly
- identify the next highest-value task
- detect blockers and dependencies
- maintain a consistent summary of delivery progress

## 2. Instructions for AI

When reading or updating this file, follow these rules:

- Treat this file as the source of truth for task progress summaries.
- Keep summaries short, factual, and implementation-oriented.
- Update this file whenever a task is created, started, blocked, completed, canceled, or materially changed.
- Do not duplicate the full content of task files here. Only keep high-signal summaries.
- Preserve the exact section structure and table formats unless there is a strong reason to change them.
- Prefer explicit statuses over vague language.
- If a task file and this manager conflict, note the conflict in `Open Issues`.
- Always reference task files by filename.
- Keep tasks ordered by task number.
- Do not include speculative work as committed scope unless it exists in a task file.

## 3. Status Definitions

Use only one of these statuses:

- `planned`: task exists but work has not started
- `in_progress`: task is actively being worked on
- `blocked`: task cannot proceed until a dependency or decision is resolved
- `done`: task is completed
- `canceled`: task is intentionally not being pursued

## 4. Project Snapshot

### Current Phase
Task 013 has been decomposed into Tasks 026 through 030 for public sales website design system, Figma design, static interface implementation, entry-flow/API integration, and final validation.

### Overall Progress
99% complete

### Summary
- Task 001 completed: requirements baseline, consultation lifecycle, plan entitlements, failure matrix, and decision log documented
- Task 002 completed: repository layout, backend hexagonal architecture, contract inventory, data flow and configuration architecture documented
- Six new ADRs added (ADR-009 through ADR-014): repository layout, module organization, DI strategy, contract location, UI config/feature flag flow, patient endpoints
- OI-006 resolved: patient endpoints added to API contract (ADR-014)
- Task 003 completed: monorepo scaffold, backend/app/website/infra bootstrap, contracts baseline, lint/format conventions, and CI placeholders are in place
- Task 004 completed: AWS CDK baseline provisioned for `dev` and `prod` with isolated stacks for security, storage, auth, APIs, compute, orchestration, monitoring, CDN, and budget alerting
- Task 004 follow-up refinement completed: clarified that AWS `dev` is not localhost, updated deployed-origin config/CORS/callbacks, and aligned docs/tasks with this environment distinction
- Task 004 same-account hardening completed: added shared-account guardrails (environment tags, scoped budgets, and prod termination protection) for safer `dev`/`prod` coexistence in one AWS account
- Task 005 completed: email/password auth via Cognito, doctor profile resolution via DynamoDB, plan-aware entitlements, auth middleware, BFF user view, feature flag evaluator, HTTP handlers for login/logout/password-reset/me, unauthenticated CDK routes, 49 tests passing
- Task 005 post-completion fix (OI-007): Lambda packaging, env var alignment (`SECRET_ARN` → `SECRET_NAME`, `CONSULTATION_TABLE` → `DYNAMODB_TABLE`), CDK test repair, stage prefix stripping in BFF handler
- AWS `dev` environment deployed to `us-east-1` (account `183992492124`) — all 9 stacks live, health endpoint verified at `https://i0dueykjuc.execute-api.us-east-1.amazonaws.com/dev/health`
- Task 006 completed: consultation domain model with 7-state machine, patient and audit entities, DynamoDB repos (consultation/patient/audit), S3 artifact key strategy, 5 use cases, HTTP handlers for consultations and patients, BFF views, BFF router upgrade with path parameter support, container wiring, 117 new tests (271 total), zero regressions
- OI-010 resolved: BFF router upgraded with regex-based parameterized routing for `/v1/consultations/{id}` style endpoints
- OI-005 addressed: Specialty enum implemented with `general_practice` as initial value, expandable via configuration
- Task 007 completed: BFF contracts with UI config endpoint (GET /v1/ui-config), pt-BR labels (10 UI labels, 7 status labels, 3 insight categories), review screen config (4 sections with order/editable/visible), consultation list config, action availability per consultation status (7 actions), enhanced consultation detail views with actions and warnings, user profile view with feature flags, container and BFF router wiring, 62 new tests (333 total), zero regressions, lint clean
- Task 008 completed: real-time session transport with session domain layer (Session entity, 6-state SessionState, AudioChunk/ConnectionInfo VOs, SessionService with 6 validation methods, 7 exception types), port interfaces (SessionRepository, ConnectionRepository), HTTP session handlers (POST .../session/start, POST .../session/end), BFF session views (SessionStartView, SessionEndView), 6 WebSocket handlers ($connect, $disconnect, session.init, audio.chunk, session.stop, client.ping), WebSocket Lambda router, DynamoDB session/connection adapters, CDK WebSocket API Gateway with ManageConnections IAM, ApiGatewayManagement helper, stub transcript delivery, container and BFF router wiring, settings expanded (websocket_url, max_session_duration_minutes), 128 new tests (461 total), zero regressions, lint clean
- Task 009 completed: ElevenLabs Scribe v2 transcription provider integrated through internal adapter interface. Transcription domain layer (NormalizedTranscript entity, SpeakerSegment/PartialTranscript/CompletenessStatus VOs, TranscriptionNormalizer service, 5 exception types). ElevenLabs adapter with HTTP batch upload for Lambda compatibility, tenacity retry, Secrets Manager config. S3 artifact persistence (S3Client, S3ArtifactRepository, S3TranscriptRepository) with existing key strategy. TranscriptionProvider port extended to 5 methods. ProcessAudioChunk and FinalizeTranscript use cases. WebSocket handlers updated (audio.chunk forwards to provider, session.stop triggers finalization). Container wired with all new dependencies. 108 new tests (569 total), zero regressions, lint clean
- Task 010 completed: AI processing pipeline with Claude API (Anthropic) generating medical history, SOAP summary, and evidence-backed insights. Domain layer (6 exceptions, InsightCategory/InsightSeverity enums, EvidenceExcerpt/Insight/GenerationMetadata/ArtifactResult VOs, PipelineResult entity, ArtifactValidator and EvidenceLinker services). ClaudeLLMProvider adapter with tenacity retry and Secrets Manager config, LazyLLMProvider for deferred initialization, SecretsManagerClient adapter. RunPipelineUseCase orchestrating sequential 3-step pipeline (anamnesis → summary → insights) with schema validation, evidence linking, partial completion support, and audit trail. Pipeline Lambda handler for Step Functions/EventBridge trigger. Container wired: StubLLMProvider replaced with LazyLLMProvider backed by ClaudeLLMProvider. anthropic dependency added. 145 new tests (951 total), zero regressions, lint clean
- Task 011 completed: Review, finalization, and export workflows. Review domain (InsightAction enum, InsightReviewItem/ReviewPayload/FinalizedRecord entities, finalization guards, 5 exception types, ReviewUpdate VO). Export domain (ExportRequest/ExportArtifact entities, ExportGenerationError, S3 key builders). 4 use cases (OpenReview with draft→review transition, UpdateReview with per-field audit, FinalizeConsultation with idempotency, GenerateExport with presigned URLs). PdfExportGenerator adapter (replaces stub, no external deps). S3StorageProvider with presigned URL generation. HTTP handlers for GET/PUT review, POST finalize, POST export. BFF views (ReviewView, FinalizeView, ExportView). Middleware exception map + BFF router wired. Container updated with 4 new use cases. 164 new tests (1115 total), zero regressions, lint clean
- Task 012 completed: authenticated React app delivered with sign-in/session restore/sign-out, consultation list and creation, live session with microphone + WebSocket connection handling, review/edit/finalize/export flow, backend-driven labels/status/action rendering, and frontend test suite (11 tests) using Vitest + Testing Library. App docs updated.
- Task 012 post-completion fix completed: local dev CORS login issue addressed by adding Vite API proxy support (`/api`), updating local app env defaults, and allowing `X-Contract-Version` in API Gateway CORS headers (infra stack + synthesis test coverage).
- Task 012 post-completion polish completed: login page visual redesign and copy refresh for a more production-ready experience, including removal of developer-facing authentication text.
- Task 012 post-completion polish (phase 2) completed: richer login motion system and interaction design with ambient animated background, staggered section entrances, hover depth, CTA micro-interactions, and reduced-motion fallback.
- Task 012 post-completion polish (phase 3) completed: desktop-first side-by-side layout restored for login and expanded into reusable responsive two-column layouts across consultations, live session, and review pages.
- Tasks 016 through 019 created: frontend-only Notter branding, authenticated app design system, page-level facelift, and query cache/loading-state improvements.
- Task 016 completed: authenticated app visible branding now uses Notter with logo assets while internal DeskAI technical identifiers remain unchanged.
- Task 017 completed: authenticated app design system primitives, tokens, icon wrapper, tests, docs, and ADR are in place.
- Task 018 completed: authenticated app pages now use the design system across shell, login, consultation, live session, review, finalization, and export surfaces.
- Task 019 completed: TanStack Query-backed request state, mutation invalidation, loading buttons, cache clearing on sign-out, tests, docs, and ADR-016 are in place.
- Task 020 completed: authenticated app neutral gray surfaces, corrected pt-BR copy, and login logo light treatment delivered with frontend and BFF tests.
- Tasks 020 through 024 created: authenticated app polish/copy/logo fixes, patient CPF/search/history contracts, staged consultation entry flow, realtime consultation data feed, and unified Anamnese consultation workspace.
- Task 021 completed: CPF-required patient identity, CPF/name search, masked CPF views, duplicate CPF conflict handling, patient detail/history endpoint, current-doctor-only history filtering, frontend API/type readiness, 409 contract response, and patient HTTP schema contract tests delivered.
- Task 022 completed: staged patient-first consultation entry flow delivered with `/` and post-login routing into `/nova-consulta`, a list-only `/consultations` history screen, existing-patient search, patient detail/history with "Iniciar nova consulta", new-patient quick start using today's local date, updated navigation, frontend docs, and 70 app tests passing.
- 2026-04-19 planning session:
  - Task 023 scope locked: client-side ElevenLabs Realtime streaming (Path A) with `POST /v1/consultations/{id}/transcription-token`; async post-session finalization via EventBridge (resolves OI-015); `session.pause`/`session.resume` actions and `session.status=paused`; schema-only `insight.provisional` + `autofill.candidate` events (emitter in Task 024); audio chunk S3 key uniqueness fix or full retirement of the backend `audio.chunk` path (new OI-018); stub transcript removal (resolves OI-016).
  - Task 024 updated to explicitly own the runtime emitter and frontend rendering of the provisional events defined in Task 023.
  - Task 025 created for auth token delivery hardening (resolves OI-007) — now scheduled after the public sales website split completes in Task 030 and before Task 014 so the security hardening pass inherits the new token strategy.
  - Stale `fix-normalized-transcript-serialization.md` deleted (already fixed on `main`). Standalone `fix-audio-chunk-accumulation.md` deleted; its remaining concurrency work is tracked by OI-018 and folded into Task 023.
  - Housekeeping: `.idea/`, `scripts/test_transcription.py`, `backend/_analyze_coverage.py`, and `backend/tests/AUDIT_REPORT.md` added to `.gitignore`; superseded `docs/audit-prompt.md` v1 deleted.
- Task 023 completed: client-side ElevenLabs Realtime streaming via single-use tokens, async two-step finalization (EventBridge + Step Functions), session pause/resume with PAUSED state, committed segment relay via app WebSocket + DynamoDB persistence, provisional event schemas (emitter deferred to Task 024), `audio.chunk` route fully retired, stub transcript removed, event versioning added, frontend direct streaming with auto token refresh, ADR-017 and DEC-009 documented. OI-015, OI-016, OI-018 resolved.
- Task 024 completed: `/consultations/:id/live` is now the primary consultation workspace with inline Anamnese, transcript, provisional autofill/insight rendering, pause/resume, stop confirmation, same-screen review/finalization/export, and legacy `/review` redirection.
- OI-017 resolved: review payload aggregation now includes transcript data, persisted insight actions, finalized-read access, and frontend-aligned summary/status fields for the unified workspace.
- Task 013 canceled/superseded: original public website scope split into Tasks 026 through 030 for staged sales website delivery.

### Immediate Next Step
Start `026-create-sales-website-design-system.md`

## 5. Priority Queue

List the most important tasks to work on next, in order.

| Rank | Task File | Title | Status | Reason |
| --- | --- | --- | --- | --- |
| 1 | `026-create-sales-website-design-system.md` | Create sales website design system | planned | Reuse authenticated app colors, spacing, and Notter logos before designing the sales website |
| 2 | `027-create-sales-website-figma-design.md` | Create sales website Figma design | planned | Produce the Figma layout with Codex Figma Plugin before implementation |
| 3 | `028-build-sales-website-interface-from-figma.md` | Build sales website interface from Figma | planned | Implement the approved static website interface in `website/` |
| 4 | `029-integrate-sales-website-entry-flows-and-javascript.md` | Integrate sales website entry flows and JavaScript | planned | Wire app entry links, lightweight JavaScript, and allowed API/config integrations |
| 5 | `030-revalidate-public-sales-website.md` | Revalidate public sales website | planned | Final design, copy, SEO, accessibility, responsive, and entry-flow validation |
| 6 | `025-harden-auth-token-delivery.md` | Harden authentication token delivery | planned | Moves refresh token to HttpOnly cookie and drops sessionStorage before security hardening pass (OI-007) |
| 7 | `014-add-observability-security-privacy-and-cost-controls.md` | Add observability, security, privacy, and cost controls | planned | Dashboards, alarms, retention, IAM tightening |
| 8 | `015-run-end-to-end-hardening-and-release-readiness.md` | Run end-to-end hardening and release readiness | planned | End-to-end validation and release packaging after remaining frontend/security work |

## 6. Active Blockers

List only blockers that currently prevent progress.

| Task File | Blocker | Depends On | Owner | Next Action |
| --- | --- | --- | --- | --- |
| None | No active blockers | N/A | N/A | Start Task 026 implementation |

## 7. Task Index

Use one row per real task. Do not include `000-task-template.md` as a delivery task.

| Task # | Task File | Title | Type | Priority | Status | Depends On | Progress % | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | `001-refine-mvp-requirements-and-delivery-decisions.md` | Refine MVP requirements and delivery decisions | Full Stack | Critical | done | None | 100 | Requirements baseline, consultation lifecycle, plan entitlements, failure matrix, and decision log documented. All four open issues resolved. Two new open decisions identified (specialty list, patient management). |
| 002 | `002-design-system-architecture-and-project-structure.md` | Design system architecture and project structure | Full Stack | Critical | done | `001-refine-mvp-requirements-and-delivery-decisions.md` | 100 | Repository layout, hexagonal backend architecture, contract inventory, data flow, and 5 new ADRs documented. OI-006 resolved. |
| 003 | `003-bootstrap-repository-and-engineering-foundation.md` | Bootstrap repository and engineering foundation | DevOps | High | done | `002-design-system-architecture-and-project-structure.md` | 100 | Monorepo scaffold, package bootstraps, lint/format tooling, shared contracts baseline, setup docs, and CI placeholders delivered |
| 004 | `004-provision-aws-foundation-with-cdk.md` | Provision AWS foundation with CDK | Infrastructure | Critical | done | `001-refine-mvp-requirements-and-delivery-decisions.md`, `002-design-system-architecture-and-project-structure.md`, `003-bootstrap-repository-and-engineering-foundation.md` | 100 | CDK app and stacks implemented for isolated `dev`/`prod` foundations including Cognito, API Gateway HTTP/WS, Lambda baseline, Step Functions, EventBridge, SQS/DLQ, SNS, DynamoDB PITR, S3 versioning/encryption, KMS, Secrets Manager, CloudWatch dashboard/alarms, CloudFront, AWS Budget alerting, and shared-account hardening guardrails |
| 005 | `005-implement-authentication-and-plan-access-control.md` | Implement authentication and plan access control | Security | Critical | done | `004-provision-aws-foundation-with-cdk.md` | 100 | Email/password auth via Cognito, DynamoDB doctor profile resolution, plan-aware entitlements (free_trial/plus/pro), auth middleware, BFF user view, feature flag evaluator, HTTP handlers, unauthenticated CDK routes, 49 tests passing |
| 006 | `006-model-consultation-domain-persistence-and-audit.md` | Model consultation domain, persistence, and audit | Backend | Critical | done | `001-refine-mvp-requirements-and-delivery-decisions.md`, `004-provision-aws-foundation-with-cdk.md`, `005-implement-authentication-and-plan-access-control.md` | 100 | Consultation domain (7-state machine, transitions, guards), patient and audit entities, DynamoDB repos (consultation/patient/audit), S3 artifact key strategy (8 types), 5 use cases (create/get/list consultation, create/list patient), HTTP handlers, BFF views, BFF router with path param support, container wiring, 117 new tests (271 total) |
| 007 | `007-build-bff-contracts-ui-config-and-feature-flags.md` | Build BFF contracts, UI config, and feature flags | Full Stack | High | done | `005-implement-authentication-and-plan-access-control.md`, `006-model-consultation-domain-persistence-and-audit.md` | 100 | BFF UI config endpoint (GET /v1/ui-config), pt-BR labels, review screen config, consultation list config, action availability per status (7 actions), consultation detail views with actions/warnings, user profile with feature flags, container/router wiring, 62 new tests (333 total) |
| 008 | `008-implement-realtime-consultation-session-transport.md` | Implement real-time consultation session transport | Backend | Critical | done | `006-model-consultation-domain-persistence-and-audit.md`, `007-build-bff-contracts-ui-config-and-feature-flags.md` | 100 | Session domain (6-state Session, SessionService, 7 exceptions), ports (SessionRepository, ConnectionRepository), use cases (StartSession, EndSession with idempotency), HTTP handlers (session/start, session/end), 6 WebSocket handlers ($connect, $disconnect, session.init, audio.chunk, session.stop, client.ping), DynamoDB session/connection adapters, CDK WebSocket API + ManageConnections IAM, BFF session views, stub transcript delivery, 128 new tests (461 total) |
| 009 | `009-integrate-transcription-provider-and-normalization.md` | Integrate transcription provider and normalization | Backend | Critical | done | `008-implement-realtime-consultation-session-transport.md` | 100 | ElevenLabs Scribe v2 adapter (HTTP batch for Lambda, tenacity retry, Secrets Manager config), transcription domain (NormalizedTranscript, SpeakerSegment, CompletenessStatus, TranscriptionNormalizer, 5 exceptions), S3 persistence (S3Client, ArtifactRepository, TranscriptRepository), ProcessAudioChunk and FinalizeTranscript use cases, WebSocket handler wiring, container DI updated, 108 new tests (569 total) |
| 010 | `010-build-ai-processing-pipeline-and-artifacts.md` | Build AI processing pipeline and artifacts | Backend | Critical | done | `006-model-consultation-domain-persistence-and-audit.md`, `009-integrate-transcription-provider-and-normalization.md` | 100 | AI pipeline with Claude API: domain layer (6 exceptions, InsightCategory/Severity enums, EvidenceExcerpt/Insight/GenerationMetadata/ArtifactResult VOs, PipelineResult entity, ArtifactValidator/EvidenceLinker services), ClaudeLLMProvider adapter (tenacity retry, Secrets Manager), LazyLLMProvider, SecretsManagerClient, RunPipelineUseCase (3-step sequential: anamnesis→summary→insights, schema validation, evidence linking, partial completion, audit trail), pipeline Lambda handler, container wired, 145 new tests (951 total) |
| 011 | `011-implement-review-finalization-and-export-workflows.md` | Implement review, finalization, and export workflows | Backend | Critical | done | `007-build-bff-contracts-ui-config-and-feature-flags.md`, `010-build-ai-processing-pipeline-and-artifacts.md` | 100 | Review domain (InsightAction, ReviewPayload, FinalizedRecord, finalization guards, 5 exceptions), export domain (ExportRequest, ExportArtifact, PdfExportGenerator), 4 use cases (OpenReview, UpdateReview, FinalizeConsultation, GenerateExport), HTTP handlers (GET/PUT review, POST finalize, POST export), BFF views, middleware + router wired, container updated, 164 new tests (1115 total) |
| 012 | `012-build-authenticated-react-app.md` | Build authenticated React app | Frontend | Critical | done | `005-implement-authentication-and-plan-access-control.md`, `007-build-bff-contracts-ui-config-and-feature-flags.md`, `008-implement-realtime-consultation-session-transport.md`, `011-implement-review-finalization-and-export-workflows.md` | 100 | Authenticated React app completed with login/session flows, consultation list/create, live recording UI, review/edit/finalize/export screens, backend-driven UI rendering, and frontend tests |
| 013 | `013-build-public-website-and-entry-flows.md` | Build public website and entry flows | Frontend | Medium | canceled | `003-bootstrap-repository-and-engineering-foundation.md`, `004-provision-aws-foundation-with-cdk.md` | 0 | Superseded by Tasks 026 through 030 for staged public sales website delivery |
| 014 | `014-add-observability-security-privacy-and-cost-controls.md` | Add observability, security, privacy, and cost controls | Security | High | planned | `004-provision-aws-foundation-with-cdk.md`, `008-implement-realtime-consultation-session-transport.md`, `009-integrate-transcription-provider-and-normalization.md`, `010-build-ai-processing-pipeline-and-artifacts.md`, `011-implement-review-finalization-and-export-workflows.md` | 0 | Adds dashboards, alarms, retention controls, PHI-aware logging, IAM tightening, and budget enforcement |
| 015 | `015-run-end-to-end-hardening-and-release-readiness.md` | Run end-to-end hardening and release readiness | QA | Critical | planned | `005-implement-authentication-and-plan-access-control.md`, `008-implement-realtime-consultation-session-transport.md`, `009-integrate-transcription-provider-and-normalization.md`, `010-build-ai-processing-pipeline-and-artifacts.md`, `011-implement-review-finalization-and-export-workflows.md`, `012-build-authenticated-react-app.md`, `014-add-observability-security-privacy-and-cost-controls.md`, `016-apply-notter-frontend-branding.md`, `017-create-authenticated-app-design-system.md`, `018-apply-authenticated-app-facelift.md`, `019-add-frontend-query-cache-and-loading-states.md`, `020-fix-authenticated-app-polish-copy-and-logo.md`, `021-extend-patient-identity-search-and-history-contracts.md`, `022-build-staged-consultation-entry-and-patient-flow.md`, `023-implement-realtime-consultation-data-feed.md`, `024-redesign-consultation-workspace-with-anamnese-and-inline-review.md`, `025-harden-auth-token-delivery.md`, `026-create-sales-website-design-system.md`, `027-create-sales-website-figma-design.md`, `028-build-sales-website-interface-from-figma.md`, `029-integrate-sales-website-entry-flows-and-javascript.md`, `030-revalidate-public-sales-website.md` | 0 | Validates the integrated MVP, closes blockers, and prepares the release, rollback, and runbook package |
| 016 | `016-apply-notter-frontend-branding.md` | Apply Notter frontend branding | Frontend | High | done | `012-build-authenticated-react-app.md` | 100 | Authenticated app visible branding updated to Notter with logo assets, document title, and regression tests while preserving DeskAI technical identifiers |
| 017 | `017-create-authenticated-app-design-system.md` | Create authenticated app design system | Frontend | High | done | `012-build-authenticated-react-app.md`, `016-apply-notter-frontend-branding.md` | 100 | Reusable UI primitives, design tokens, lucide-backed icon wrapper, tests, README guidance, and ADR-015 are in place |
| 018 | `018-apply-authenticated-app-facelift.md` | Apply authenticated app facelift | Frontend | High | done | `012-build-authenticated-react-app.md`, `016-apply-notter-frontend-branding.md`, `017-create-authenticated-app-design-system.md` | 100 | Design system applied across authenticated shell, login, consultation, live session, review, finalization, and export surfaces with regression tests |
| 019 | `019-add-frontend-query-cache-and-loading-states.md` | Add frontend query cache and loading states | Frontend | Medium | done | `012-build-authenticated-react-app.md`, `017-create-authenticated-app-design-system.md`, `018-apply-authenticated-app-facelift.md` | 100 | TanStack Query-backed request state added with query/mutation hooks, provider setup, cache invalidation, sign-out cache clearing, loading states, tests, docs, and ADR-016 |
| 020 | `020-fix-authenticated-app-polish-copy-and-logo.md` | Fix authenticated app polish, copy, and logo | Full Stack | High | done | `016-apply-notter-frontend-branding.md`, `017-create-authenticated-app-design-system.md`, `018-apply-authenticated-app-facelift.md` | 100 | Neutral gray authenticated app surfaces, corrected pt-BR copy, and login logo light treatment delivered with frontend and BFF tests |
| 021 | `021-extend-patient-identity-search-and-history-contracts.md` | Extend patient identity, search, and history contracts | Full Stack | Critical | done | `006-model-consultation-domain-persistence-and-audit.md`, `011-implement-review-finalization-and-export-workflows.md`, `014-add-observability-security-privacy-and-cost-controls.md` | 100 | CPF-required patient identity, CPF/name search, masked CPF views, duplicate CPF conflict handling, patient detail/history endpoint, current-doctor-only history filtering, frontend API/type readiness, 409 contract response, and patient HTTP schema contract tests delivered |
| 022 | `022-build-staged-consultation-entry-and-patient-flow.md` | Build staged consultation entry and patient flow | Frontend | Critical | done | `021-extend-patient-identity-search-and-history-contracts.md` | 100 | Delivered `/nova-consulta`, patient search/detail/start flows, list-only consultation history, default home redirect changes, docs updates, and frontend regression coverage |
| 023 | `023-implement-realtime-consultation-data-feed.md` | Implement realtime consultation data feed | Full Stack | Critical | done | `008-implement-realtime-consultation-session-transport.md`, `009-integrate-transcription-provider-and-normalization.md`, `010-build-ai-processing-pipeline-and-artifacts.md` | 100 | Client-side ElevenLabs Realtime streaming via single-use tokens, async two-step finalization (EventBridge + Step Functions), session pause/resume with PAUSED state, committed segment relay via WebSocket + DynamoDB, provisional event schemas, `audio.chunk` retired, stub transcript removed, event versioning, ADR-017 and DEC-009 documented. OI-015, OI-016, OI-018 resolved. |
| 024 | `024-redesign-consultation-workspace-with-anamnese-and-inline-review.md` | Redesign consultation workspace with Anamnese and inline review | Full Stack | Critical | done | `021-extend-patient-identity-search-and-history-contracts.md`, `022-build-staged-consultation-entry-and-patient-flow.md`, `023-implement-realtime-consultation-data-feed.md` | 100 | `/consultations/:id/live` now serves as the unified consultation workspace with inline Anamnese, provisional events, same-screen review/finalization/export, and legacy `/review` compatibility redirect |
| 025 | `025-harden-auth-token-delivery.md` | Harden authentication token delivery | Full Stack | High | planned | `005-implement-authentication-and-plan-access-control.md`, `012-build-authenticated-react-app.md`, `030-revalidate-public-sales-website.md` | 0 | Replaces `sessionStorage` token storage with in-memory access token plus HttpOnly/Secure/SameSite=Strict refresh cookie, adds `/v1/auth/refresh` endpoint, updates login/logout handlers, CORS, and CloudFront; resolves OI-007 before Task 014 |
| 026 | `026-create-sales-website-design-system.md` | Create sales website design system | Frontend | High | planned | `016-apply-notter-frontend-branding.md`, `017-create-authenticated-app-design-system.md`, `018-apply-authenticated-app-facelift.md`, `020-fix-authenticated-app-polish-copy-and-logo.md` | 0 | Reuses authenticated app tokens, spacing, and Notter logo assets to create the public sales website design-system baseline |
| 027 | `027-create-sales-website-figma-design.md` | Create sales website Figma design | Frontend | High | planned | `026-create-sales-website-design-system.md` | 0 | Uses the Codex Figma Plugin and prior tokens to design desktop and mobile sales website layouts |
| 028 | `028-build-sales-website-interface-from-figma.md` | Build sales website interface from Figma | Frontend | High | planned | `027-create-sales-website-figma-design.md` | 0 | Implements the approved Figma layout as static HTML/CSS in `website/` with SEO-friendly, responsive pages |
| 029 | `029-integrate-sales-website-entry-flows-and-javascript.md` | Integrate sales website entry flows and JavaScript | Full Stack | High | planned | `028-build-sales-website-interface-from-figma.md`, `005-implement-authentication-and-plan-access-control.md`, `012-build-authenticated-react-app.md` | 0 | Wires app entry links, lightweight JavaScript, allowed API/config integrations, and public Notter URL metadata without internal DeskAI renames |
| 030 | `030-revalidate-public-sales-website.md` | Revalidate public sales website | QA | High | planned | `029-integrate-sales-website-entry-flows-and-javascript.md` | 0 | Final validation of design fidelity, copy, entry flows, responsiveness, SEO, accessibility, performance, and public domain status |

## 8. Milestones

Track major delivery checkpoints for the MVP.

| Milestone | Target Outcome | Status | Notes |
| --- | --- | --- | --- |
| Project Setup | Task system ready for execution | done | Template and manager files created |
| Infrastructure Ready | AWS baseline in place | done | Tasks 003 and 004 completed. Dev environment deployed 2026-04-02: 9 stacks live in us-east-1, health endpoint verified. Lambda packaging and env var issues from Task 005 fixed (OI-007). |
| Backend Ready | Core API and business logic in place | done | Tasks 005 through 011 completed. All core backend endpoints implemented: auth, consultations, sessions, transcription, AI pipeline, review, finalization, export. 1115 tests passing. |
| Frontend Ready | Core MVP interface in place | in_progress | Authenticated app workflow corrections advanced through Task 024. Tasks 026 through 030 now own the staged public sales website work. |
| MVP Ready | End-to-end usable first version | planned | Covered by Tasks 014 and 015 |

## 9. Open Issues

Track cross-task decisions, missing information, or conflicts.

| ID | Issue | Impact | Status | Next Action |
| --- | --- | --- | --- | --- |
| OI-001 | The first production transcription provider has not been selected from the approved candidates yet | Provider integration, cost analysis, and credential setup cannot be finalized | resolved | ElevenLabs Scribe v2 Realtime selected (supersedes Deepgram Nova-2 Medical). See `docs/requirements/05-decision-log.md` DEC-001 and ADR-006. |
| OI-002 | Plan entitlement differences between `free_trial`, `plus`, and `pro` are not fully defined | Backend authorization and feature-flag behavior may need rework | resolved | All plans share core features; differentiation by usage limits. See `docs/requirements/03-plan-entitlements.md`. |
| OI-003 | Clinic audio retention defaults and deletion timing are not explicitly defined | Storage lifecycle, retention automation, and compliance behavior remain ambiguous | resolved | Plan-based retention: 7/30/90 days. See `docs/requirements/05-decision-log.md` DEC-003. |
| OI-004 | Export output scope beyond the finalized note is not fully specified | Export implementation could diverge from stakeholder expectations | resolved | PDF with metadata + finalized history + summary + accepted insights. No transcript. See DEC-004. |
| OI-005 | Specialty list and validation approach not defined | Domain model cannot validate specialty field | resolved | `Specialty` enum with `GENERAL_PRACTICE` implemented in Task 006. Expandable via configuration. |
| OI-006 | Patient CRUD endpoints not defined in API contract | Cannot create consultations without patient management | resolved | Minimal `POST /v1/patients` and `GET /v1/patients` added to API contract. See ADR-014 and `docs/architecture/03-contract-inventory.md`. |
| OI-007 | Token delivery strategy (body vs HttpOnly cookie) | XSS risk for browser-based clients if refresh_token stays in JSON body | open | Resolve in `025-harden-auth-token-delivery.md`: in-memory access token + HttpOnly/Secure/SameSite=Strict refresh cookie + `/v1/auth/refresh`. Scheduled after Task 030 and before Task 014. |
| OI-008 | `DoctorProfile.created_at` is `str` instead of `datetime` | Every consumer must parse ISO strings; domain model is not self-descriptive | resolved | Refactored: `created_at` is now `datetime`, `compute_entitlements` accepts `datetime` directly, DynamoDB adapter handles serialization. 14 files updated, 951 tests passing. |
| OI-009 | BFF Lambda `sys.path` manipulation is fragile | Lambda packaging changes will silently break imports | resolved | Fixed: Makefile build step bundles `lambda_handlers/` + `backend/src/deskai/` + pip deps into `infra/.build/lambda/`. `sys.path` hack removed from `bff.py`. |
| OI-010 | BFF router does not support path parameters | Cannot route `/v1/consultations/{id}` style endpoints | resolved | Fixed in Task 006: BFF router upgraded with regex-based parameterized routing. Path parameters extracted and injected into event['pathParameters']. |
| OI-011 | Lambda packaging did not include backend code or runtime dependencies | BFF Lambda failed at runtime with `ModuleNotFoundError: No module named 'deskai'` | resolved | Fixed: Makefile build step bundles `lambda_handlers/` + `backend/src/deskai/` + pip deps into `infra/.build/lambda/`. Env var names aligned between `compute_stack.py` and `config.py` (`SECRET_ARN` → `SECRET_NAME`, `CONSULTATION_TABLE` → `DYNAMODB_TABLE`). CDK tests repaired (3 missing kwargs from Task 005). Stage prefix stripping added to BFF handler. |
| OI-012 | Orphaned `deskai/dev/deepgram` secret in CloudFormation state | CloudFormation skipped resource via `continue-update-rollback --resources-to-skip`. The resource is no longer tracked or deletable by CloudFormation. Harmless (secret doesn't exist in AWS), but state is dirty. | resolved | Secret no longer exists in AWS. CloudFormation state cleaned up by subsequent deploys. No action needed. |
| OI-013 | `unsafe_plain_text` placeholder committed to git history | `SecretValue.unsafe_plain_text("see-elevenlabs-secret")` was committed in e0681d9 (now superseded by f35425c). Not a real key, but the pattern is a code smell in version control. | resolved | Not a real secret (placeholder text only). Git history cannot be rewritten. Pattern avoided in subsequent CDK code. No action needed. |
| OI-014 | WebSocket container wiring uses dependency stubs, not full container resolution | `router.py` has `_get_transcription_provider()` and `_get_finalize_transcript_use_case()` stubs that raise `NotImplementedError`. WebSocket handlers don't go through the full `build_container()` path yet. | resolved | Fixed in PR #51: WebSocket router now uses `_get_container()` for all routes (session.init, audio.chunk, session.stop). Authorizer handler added. Route dispatch normalised for named routes and $default. Tested live: session.init and audio.chunk work end-to-end. |
| OI-015 | Finalization runs synchronously inside `session.stop` handler | `FinalizeTranscriptUseCase` is called inline after session ends. Long transcriptions could exceed Lambda 30s timeout. Handler catches and logs exceptions to avoid breaking the stop response. | resolved | Fixed in Task 023: `session.stop` now only transitions state and emits EventBridge event. Finalization runs in a two-step Step Functions workflow (transcript finalization → AI pipeline) triggered by EventBridge, with retries and DLQ. |
| OI-016 | Stub `transcript.partial` still sent in `audio.chunk` handler | Real-time partial transcripts from ElevenLabs require persistent WebSocket or callback. Current handler still sends `[stub transcript]` placeholder. The actual transcription happens in batch when `fetch_final_transcript` is called. | resolved | Fixed in Task 023: `audio.chunk` handler deleted, stub transcript removed from all code paths and tests. Frontend now receives real transcripts directly from ElevenLabs via client-side streaming. |
| OI-018 | In-memory audio chunk buffer `_SessionEntry.chunk_count` is not globally unique across concurrent Lambda containers | S3 audio chunk keys can collide when multiple warm Lambda containers handle `audio.chunk` messages for the same session, causing chunks to overwrite each other and `session.stop` to report `audio_bytes: 0`. | resolved | Fixed in Task 023: backend `audio.chunk` route fully retired. Audio streams directly from browser to ElevenLabs via client-side streaming. No backend audio chunk storage needed. |
| OI-017 | Review payload contract drift (`ReviewView`) | Frontend must use defensive fallbacks because backend `build_review_view` currently omits or weakly-types fields expected by contract (`transcript`, `ui_config`, `summary.content` shape mismatch). | resolved | Resolved in Task 024 by aligning the review payload with transcript segments, consultation status, summary shape, insight action state, and unified-workspace expectations. |
| OI-019 | Dev/prod frontend custom domains are not yet reachable and must move to the visual `Notter` brand | The AWS `dev` and `prod` frontend URLs remain inaccessible until the domain is purchased and CloudFront/ACM/DNS records are fully configured. When this is implemented, the public-facing domain links must use the `Notter` brand instead of `DeskAI`, but this must be a visual/domain-only change: internal variables, stack names, environment keys, package names, and code components should continue using `DeskAI` to avoid unnecessary internal renames and deployment risk. | open | Handle during `029-integrate-sales-website-entry-flows-and-javascript.md` and validate in `030-revalidate-public-sales-website.md`; if DNS/ACM/CloudFront dependencies remain external, record the exact follow-up while keeping internal naming/code identifiers on `DeskAI`. |

## 10. Recently Updated Tasks

List the most recently changed tasks first.

| Date | Task File | Change |
| --- | --- | --- |
| 2026-04-23 | `@task-manager.md` | Decomposed Task 013 into Tasks 026 through 030, refreshed priority queue/dependencies, and moved the next step to Task 026 |
| 2026-04-23 | `030-revalidate-public-sales-website.md` | Created wrap-up validation task for public sales website design, copy, entry flows, SEO, accessibility, responsiveness, performance, and domain status |
| 2026-04-23 | `029-integrate-sales-website-entry-flows-and-javascript.md` | Created public website entry-flow, lightweight JavaScript, allowed API/config integration, and Notter URL metadata task |
| 2026-04-23 | `028-build-sales-website-interface-from-figma.md` | Created static HTML/CSS implementation task for building the public sales website interface from the Figma layout |
| 2026-04-23 | `027-create-sales-website-figma-design.md` | Created Codex Figma Plugin design task using the prior public website token baseline |
| 2026-04-23 | `026-create-sales-website-design-system.md` | Created public sales website design-system task reusing authenticated app colors, spacing, and Notter logo assets |
| 2026-04-23 | `013-build-public-website-and-entry-flows.md` | Marked as canceled/superseded by Tasks 026 through 030 |
| 2026-04-23 | `013-build-public-website-and-entry-flows.md` | Updated scope to include public-facing `Notter` domains/branding for website and app entrypoints while explicitly preserving internal `DeskAI` naming in code and infrastructure |
| 2026-04-23 | `@task-manager.md` | Updated OI-019: frontend domains must move to the visual `Notter` brand, but the change must stay domain-only and preserve internal `DeskAI` naming in code/infrastructure |
| 2026-04-21 | `@task-manager.md` | Added OI-019 to track missing frontend domain purchase/configuration for dev/prod URLs (`app.dev.deskai.com.br`, `dev.deskai.com.br`, `app.deskai.com.br`, `deskai.com.br`) |
| 2026-04-21 | `024-redesign-consultation-workspace-with-anamnese-and-inline-review.md` | Completed: unified `/live` workspace, inline Anamnese/review, provisional autofill + insight rendering, pause/resume + stop confirmation, finalized read-only behavior, `/review` redirect, review payload alignment, and frontend/backend regression coverage |
| 2026-04-21 | `@task-manager.md` | Marked Task 024 done, resolved OI-017, set next step to Task 013, refreshed priority queue, and updated progress to 99% |
| 2026-04-21 | `024-redesign-consultation-workspace-with-anamnese-and-inline-review.md` | Started implementation: moved to in_progress for unified workspace, inline review, provisional event rendering, and `/review` transition work |
| 2026-04-21 | `022-build-staged-consultation-entry-and-patient-flow.md` | Completed: staged `/nova-consulta` entry, list-only `/consultations`, existing-patient search, patient detail/history, "Iniciar nova consulta", today's-date quick start, navigation/docs updates, and frontend regression coverage |
| 2026-04-21 | `@task-manager.md` | Marked Task 022 done, moved next step to Task 024, refreshed priority queue, and updated progress to 98% |
| 2026-04-20 | `023-implement-realtime-consultation-data-feed.md` | Completed: client-side ElevenLabs streaming via single-use tokens, async two-step finalization, session pause/resume, committed segment relay, provisional event schemas, audio.chunk retired, stub transcript removed, event versioning, ADR-017, DEC-009 |
| 2026-04-20 | `@task-manager.md` | Task 023 done, OI-015/016/018 resolved, priority queue updated (next: Task 022), progress 97% |
| 2026-04-20 | `mvp-technical-specs.md` | Added ADR-017: Client-Side ElevenLabs Realtime Streaming |
| 2026-04-20 | `05-decision-log.md` | Added DEC-009: Client-Side Realtime Streaming Architecture |
| 2026-04-20 | `03-contract-inventory.md` | Added transcription-token endpoint, transcript.commit/session.pause/session.resume actions, insight.provisional/autofill.candidate schemas, event versioning, removed audio.chunk |
| 2026-04-19 | `@task-manager.md` | Reordered priority queue (023 → 022 → 024 → 013 → 025 → 014 → 015); added Task 025, added OI-018 for chunk-key collision, linked OI-007/015/016 to their resolution tasks |
| 2026-04-19 | `025-harden-auth-token-delivery.md` | Created auth token hardening task (OI-007) — in-memory access token + HttpOnly refresh cookie + `/v1/auth/refresh` endpoint |
| 2026-04-19 | `024-redesign-consultation-workspace-with-anamnese-and-inline-review.md` | Clarified ownership of the provisional AI/autofill event emitter and rendering; depends on schemas defined in Task 023 |
| 2026-04-19 | `023-implement-realtime-consultation-data-feed.md` | Locked scope: client-side ElevenLabs Realtime streaming via short-lived token endpoint, async finalization via EventBridge (OI-015), pause/resume, schema-only provisional events, chunk-key collision fix (OI-018), stub transcript removal (OI-016) |
| 2026-04-19 | `tasks/fix-audio-chunk-accumulation.md` | Deleted: remaining concurrency fix folded into Task 023 and tracked as OI-018 |
| 2026-04-19 | `tasks/fix-normalized-transcript-serialization.md` | Deleted: already fixed on main (`S3TranscriptRepository` uses `dataclasses.asdict`) |
| 2026-04-18 | `021-extend-patient-identity-search-and-history-contracts.md` | Corrected completion gap: added duplicate CPF 409 response to patient OpenAPI contract and patient HTTP schema contract tests |
| 2026-04-18 | `021-extend-patient-identity-search-and-history-contracts.md` | Completed: CPF identity/search, duplicate handling, patient detail/history endpoint, frontend API/types, docs, and tests delivered |
| 2026-04-18 | `021-extend-patient-identity-search-and-history-contracts.md` | Started implementation: moved to in_progress for CPF patient identity, search, detail/history contracts, and related backend/frontend/doc updates |
| 2026-04-18 | `020-fix-authenticated-app-polish-copy-and-logo.md` | Completed: neutral gray app surfaces, removed login ambient gradients, corrected authenticated app and BFF pt-BR copy, and added logo/style/copy regression tests |
| 2026-04-18 | `020-fix-authenticated-app-polish-copy-and-logo.md` | Started implementation: moved to in_progress for authenticated app background, pt-BR copy, and logo contrast fixes |
| 2026-04-18 | `@task-manager.md` | Added Tasks 020 through 024 to priority queue and task index; updated current phase, next step, dependencies, milestone notes, and open issue next actions |
| 2026-04-18 | `024-redesign-consultation-workspace-with-anamnese-and-inline-review.md` | Created unified consultation workspace, Anamnese, inline review, finalization, and export redesign task |
| 2026-04-18 | `023-implement-realtime-consultation-data-feed.md` | Created realtime transcript/session feed and provisional update contract task |
| 2026-04-18 | `022-build-staged-consultation-entry-and-patient-flow.md` | Created staged post-login consultation entry and patient flow task |
| 2026-04-18 | `021-extend-patient-identity-search-and-history-contracts.md` | Created CPF-based patient identity, search, and current-doctor history contract task |
| 2026-04-18 | `020-fix-authenticated-app-polish-copy-and-logo.md` | Created authenticated app background, pt-BR copy, and login logo polish task |
| 2026-04-18 | `019-add-frontend-query-cache-and-loading-states.md` | Completed: TanStack Query provider/hooks, query-backed pages, mutation invalidation, sign-out cache clearing, tests, docs, and ADR-016 |
| 2026-04-18 | `019-add-frontend-query-cache-and-loading-states.md` | Started implementation: moved to in_progress for TanStack Query-backed request state and cache clearing |
| 2026-04-18 | `018-apply-authenticated-app-facelift.md` | Completed: design-system primitives applied across authenticated pages with loading, alert, empty, chip, form, and action states verified |
| 2026-04-18 | `018-apply-authenticated-app-facelift.md` | Started implementation: moved to in_progress for page-level design-system adoption |
| 2026-04-18 | `017-create-authenticated-app-design-system.md` | Completed: reusable UI primitives, design tokens, lucide icon wrapper, component tests, README guidance, and ADR-015 |
| 2026-04-18 | `017-create-authenticated-app-design-system.md` | Started implementation: moved to in_progress for reusable UI primitives and design tokens |
| 2026-04-18 | `016-apply-notter-frontend-branding.md` | Completed: Notter branding and logo assets applied to login, app shell, loading shell, and document title with frontend tests and build verification |
| 2026-04-18 | `016-apply-notter-frontend-branding.md` | Started implementation: moved to in_progress for authenticated app Notter branding and logo integration |
| 2026-04-18 | `015-run-end-to-end-hardening-and-release-readiness.md` | Updated dependencies to include authenticated app facelift and query-cache tasks before release readiness |
| 2026-04-18 | `@task-manager.md` | Added Tasks 016 through 019 to priority queue and task index; updated current phase, progress, next step, and frontend milestone notes |
| 2026-04-18 | `019-add-frontend-query-cache-and-loading-states.md` | Created frontend query cache and loading-state task |
| 2026-04-18 | `018-apply-authenticated-app-facelift.md` | Created authenticated app page-level facelift task |
| 2026-04-18 | `017-create-authenticated-app-design-system.md` | Created authenticated app design system task |
| 2026-04-18 | `016-apply-notter-frontend-branding.md` | Created frontend-only Notter branding task |
| 2026-04-15 | `012-build-authenticated-react-app.md` | Post-completion polish (phase 3): fixed login desktop side-by-side composition and applied consistent responsive two-column layout patterns to consultations, live session, and review pages |
| 2026-04-15 | `@task-manager.md` | Updated Task 012 summary and recent updates with cross-page responsive layout polish phase 3 |
| 2026-04-15 | `012-build-authenticated-react-app.md` | Post-completion polish (phase 2): upgraded login page with modern motion/interaction design (ambient animation, staggered entrances, hover depth, animated CTA, and reduced-motion fallback) |
| 2026-04-15 | `@task-manager.md` | Updated Task 012 summary and recent updates with login motion/interaction polish phase 2 |
| 2026-04-12 | `012-build-authenticated-react-app.md` | Post-completion polish: refined login page layout and visual hierarchy, refreshed copy, removed developer-facing authentication note, and added test coverage to prevent technical auth copy from returning |
| 2026-04-12 | `@task-manager.md` | Updated Task 012 summary and recent updates with login page production-readiness polish |
| 2026-04-11 | `012-build-authenticated-react-app.md` | Post-completion fix: resolved localhost login CORS by adding Vite `/api` proxy support, updating local env defaults (`VITE_API_BASE_URL=/api` + `VITE_API_PROXY_TARGET`), and extending API Gateway CORS allow headers with `X-Contract-Version` (with infra test coverage) |
| 2026-04-11 | `@task-manager.md` | Updated snapshot and recent changes with Task 012 CORS post-completion fix details |
| 2026-04-11 | `012-build-authenticated-react-app.md` | Completed: route-based authenticated app (login/session restore/sign-out), consultation list/create + patient helper, live session UI (microphone/WebSocket/transcript/reconnect), review/edit/finalize/export screens, backend-driven UI rendering, app docs update, and 11 frontend tests |
| 2026-04-11 | `@task-manager.md` | Updated for Task 012 completion: status done, progress 93%, priority queue updated, next step set to Task 013, frontend milestone moved to in-progress, OI-017 added |
| 2026-04-11 | `012-build-authenticated-react-app.md` | Started implementation: task moved to in-progress and authenticated app implementation/testing work underway |
| 2026-04-11 | `@task-manager.md` | Updated snapshot, priority queue, and Task 012 status to in-progress |
| 2026-04-04 | `011-implement-review-finalization-and-export-workflows.md` | Completed: Review domain (InsightAction enum, InsightReviewItem/ReviewPayload/FinalizedRecord entities, finalization guards, 5 exceptions, ReviewUpdate VO), export domain (ExportRequest/ExportArtifact, ExportGenerationError, S3 key builders), PdfExportGenerator adapter (replaces stub), S3StorageProvider + presigned URLs, 4 use cases (OpenReview, UpdateReview, FinalizeConsultation, GenerateExport), HTTP handlers (GET/PUT review, POST finalize, POST export), BFF views (ReviewView, FinalizeView, ExportView), middleware exception map + BFF router wired, container updated, 164 new tests (1115 total) |
| 2026-04-04 | `@task-manager.md` | Updated for Task 011 completion: status done, progress 87%, priority queue updated, Backend Ready milestone marked done, next step set to Task 012 |
| --- | --- | --- |
| 2026-04-03 | `010-build-ai-processing-pipeline-and-artifacts.md` | Completed: Claude API pipeline with domain layer (6 exceptions, InsightCategory/Severity enums, 6 VOs, PipelineResult entity, ArtifactValidator + EvidenceLinker services), ClaudeLLMProvider adapter (tenacity retry, Secrets Manager), LazyLLMProvider, SecretsManagerClient, RunPipelineUseCase (3-step anamnesis→summary→insights with schema validation, evidence linking, partial completion, audit trail), pipeline Lambda handler, container wired (StubLLMProvider replaced), anthropic dependency added, 145 new tests (951 total) |
| 2026-04-03 | `@task-manager.md` | Updated for Task 010 completion: status done, progress 80%, priority queue updated, next step set to Task 011 |
| 2026-04-02 | `009-integrate-transcription-provider-and-normalization.md` | Completed: ElevenLabs Scribe v2 adapter (HTTP batch for Lambda, tenacity retry, Secrets Manager config), transcription domain layer (NormalizedTranscript entity, SpeakerSegment/PartialTranscript/CompletenessStatus VOs, TranscriptionNormalizer, 5 exception types), S3 persistence (S3Client, S3ArtifactRepository, S3TranscriptRepository with ports), TranscriptionProvider port extended to 5 methods, ProcessAudioChunk and FinalizeTranscript use cases, WebSocket handlers updated (audio.chunk forwards to provider, session.stop triggers finalization), container wired, 108 new tests (569 total) |
| 2026-04-02 | `@task-manager.md` | Updated for Task 009 completion: status, progress 73%, priority queue, next step set to Task 010 |
| 2026-04-02 | `008-implement-realtime-consultation-session-transport.md` | Completed: session domain (Session entity, 6-state SessionState, SessionService, 7 exceptions), ports (SessionRepository, ConnectionRepository), use cases (StartSession, EndSession with idempotency), HTTP handlers (session/start, session/end), 6 WebSocket handlers, DynamoDB session/connection adapters, CDK WebSocket API + ManageConnections IAM, BFF session views, stub transcript, 128 new tests (461 total) |
| 2026-04-02 | `@task-manager.md` | Updated for Task 008 completion: status, progress 67%, priority queue, next step set to Task 009 |
| 2026-04-02 | `007-build-bff-contracts-ui-config-and-feature-flags.md` | Completed: BFF UI config endpoint, pt-BR labels (10 UI + 7 status + 3 insight categories), review screen config, consultation list config, action availability module (7 actions per status), enhanced consultation detail views with actions/warnings, user profile with feature flags, container/router wiring, 62 new tests (333 total) |
| 2026-04-02 | `@task-manager.md` | Updated for Task 007 completion: status, progress 60%, priority queue, next step set to Task 008 |
| 2026-04-02 | `006-model-consultation-domain-persistence-and-audit.md` | Completed: consultation domain (7-state machine), patient/audit entities, DynamoDB repos, S3 artifact keys, 5 use cases, HTTP handlers, BFF views, router upgrade, container wiring, 117 new tests |
| 2026-04-02 | `@task-manager.md` | Updated for Task 006 completion: status, progress, priority queue, OI-010 resolved, next step set to Task 007 |
| 2026-04-02 | `005-implement-authentication-and-plan-access-control.md` | Post-completion fix: Lambda packaging (Makefile build step), env var alignment, CDK test repair, stage prefix stripping in BFF handler |
| 2026-04-02 | `@task-manager.md` | Added OI-011 for Lambda packaging gap, marked OI-009 resolved, audit fixes applied |
| 2026-03-30 | `005-implement-authentication-and-plan-access-control.md` | Added post-completion follow-ups from PR #12 code review: token delivery, created_at typing, sys.path, GSI naming |
| 2026-03-30 | `006-model-consultation-domain-persistence-and-audit.md` | Added backend notes: BFF router upgrade needed for path params, GSI naming verification |
| 2026-03-30 | `@task-manager.md` | Added OI-007 through OI-010 for deferred PR #12 review items |
| 2026-03-30 | `005-implement-authentication-and-plan-access-control.md` | Completed: Cognito auth, DynamoDB doctor profiles, plan entitlements, middleware, handlers, BFF views, feature flags, CDK route/IAM updates, 49 tests |
| 2026-03-30 | `@task-manager.md` | Updated for Task 005 completion: status, progress, next step, priority queue |
| 2026-03-30 | `004-provision-aws-foundation-with-cdk.md` | Same-account hardening: environment tagging, scoped budgets, forecast alerts, and prod termination protection when `dev`/`prod` share one AWS account |
| 2026-03-30 | `@task-manager.md` | Updated Task 004 summary and recent changes with shared-account hardening follow-up |
| 2026-03-30 | `004-provision-aws-foundation-with-cdk.md` | Refined post-completion: separated AWS `dev` environment origins from localhost development assumptions and aligned CORS/callback configuration |
| 2026-03-30 | `@task-manager.md` | Updated summary and recent changes for Task 004 environment distinction clarification |
| 2026-03-30 | `004-provision-aws-foundation-with-cdk.md` | Completed: isolated `dev`/`prod` CDK foundations delivered with security, storage, API, orchestration, monitoring, CDN, and budget baselines |
| 2026-03-30 | `@task-manager.md` | Updated for Task 004 completion: status, progress, next step, priority queue, and milestone movement |
| 2026-03-30 | `004-provision-aws-foundation-with-cdk.md` | Started implementation: task moved to in-progress and baseline CDK resource provisioning underway |
| 2026-03-30 | `@task-manager.md` | Updated snapshot, priority queue, and Task 004 status to in-progress |
| 2026-03-30 | `003-bootstrap-repository-and-engineering-foundation.md` | Completed: repository scaffold, package bootstraps, linting/formatting conventions, setup docs, and baseline CI workflows |
| 2026-03-30 | `@task-manager.md` | Updated Task 003 to done; refreshed snapshot, priority queue, next step, and progress |
| 2026-03-30 | `003-bootstrap-repository-and-engineering-foundation.md` | Started implementation: task moved to in-progress, bootstrap and tooling work underway |
| 2026-03-30 | `@task-manager.md` | Updated snapshot, priority queue, and Task 003 status to in-progress |
| 2026-03-29 | `002-design-system-architecture-and-project-structure.md` | Completed: repository layout, backend hexagonal architecture, contract inventory, data flow and configuration documented |
| 2026-03-29 | `@task-manager.md` | Updated for Task 002 completion: status, progress, priority queue, OI-006 resolved |
| 2026-03-29 | `mvp-technical-specs.md` | Added ADR-009 through ADR-014, patient endpoints to API contract, UI config/feature flag flow ADR |
| 2026-03-28 | `001-refine-mvp-requirements-and-delivery-decisions.md` | Completed: requirements baseline, lifecycle, entitlements, failure matrix, decision log. OI-001..OI-004 resolved. OI-005, OI-006 added. |
| 2026-03-28 | `@task-manager.md` | Updated for Task 001 completion: status, progress, priority queue, open issues, milestones |
| 2026-03-28 | `mvp-business-rules.md` | Added recording and processing_failed states, finalization immutability rules, export rules section |
| 2026-03-28 | `mvp-technical-specs.md` | Renamed section 13 to AI Processing Layer, added ADR-006 (Deepgram), ADR-007 (Claude API), ADR-008 (plan model) |
| 2026-03-28 | `015-run-end-to-end-hardening-and-release-readiness.md` | Created release-readiness and end-to-end validation task |
| 2026-03-28 | `014-add-observability-security-privacy-and-cost-controls.md` | Created observability, security, retention, and cost-controls task |
| 2026-03-28 | `013-build-public-website-and-entry-flows.md` | Created public website and entry-flow task |
| 2026-03-28 | `012-build-authenticated-react-app.md` | Created authenticated React app task |
| 2026-03-28 | `011-implement-review-finalization-and-export-workflows.md` | Created review, finalization, and export workflow task |
| 2026-03-28 | `010-build-ai-processing-pipeline-and-artifacts.md` | Created AI processing pipeline and artifact task |
| 2026-03-28 | `009-integrate-transcription-provider-and-normalization.md` | Created transcription provider and normalization task |
| 2026-03-28 | `008-implement-realtime-consultation-session-transport.md` | Created real-time session transport task |
| 2026-03-28 | `007-build-bff-contracts-ui-config-and-feature-flags.md` | Created BFF contracts, UI config, and feature flags task |
| 2026-03-28 | `006-model-consultation-domain-persistence-and-audit.md` | Created consultation domain, persistence, and audit task |
| 2026-03-28 | `005-implement-authentication-and-plan-access-control.md` | Created authentication and plan access control task |
| 2026-03-28 | `004-provision-aws-foundation-with-cdk.md` | Created AWS CDK foundation task |
| 2026-03-28 | `003-bootstrap-repository-and-engineering-foundation.md` | Created repository and engineering foundation task |
| 2026-03-28 | `002-design-system-architecture-and-project-structure.md` | Created architecture and project-structure task |
| 2026-03-28 | `001-refine-mvp-requirements-and-delivery-decisions.md` | Created requirements refinement and decision-alignment task |
| 2026-03-28 | `@task-manager.md` | Replaced placeholder tracker entries with the full MVP task plan |
| 2026-03-28 | `@task-manager.md` | Created task manager structure |
| 2026-03-28 | `000-task-template.md` | Created reusable task template |

## 11. AI Update Workflow

When a new real task is created:
1. Add it to `Task Index`.
2. Update `Priority Queue`.
3. Update `Project Snapshot` if overall progress changed.
4. Add or update dependencies and blockers.
5. Add a row to `Recently Updated Tasks`.

When a task status changes:
1. Update the task row in `Task Index`.
2. Update `Active Blockers` if needed.
3. Update `Priority Queue` if prioritization changed.
4. Update milestone status if the task affects a milestone.
5. Add a row to `Recently Updated Tasks`.

When a task is completed:
1. Set status to `done`.
2. Set `Progress %` to `100`.
3. Update `Overall Progress`.
4. Remove it from blockers if applicable.
5. Reflect any milestone movement.

## 12. Recommended Conventions

### Task File Naming
Use this format for real tasks:
- `001-short-task-name.md`
- `002-short-task-name.md`
- `003-short-task-name.md`

### Title Style
- Start with a verb when possible
- Keep it specific
- Keep it short enough to scan quickly

### Summary Style
- One sentence
- Focus on outcome, not process
- Mention blockers only if they affect progress

## 13. Machine-Friendly Task Record Template

Use the structure below when adding a new task summary.

```md
| 001 | `001-example-task.md` | Example task title | Backend | High | planned | None | 0 | Short implementation-ready summary |
```

## 14. Lessons Learned

### Lint Validation Must Match CI Exactly (Task 008)

When agents generate code in parallel, always run the **exact same lint command CI uses** (`make lint` and `make test`) before committing — not a hand-picked file list. During Task 008, agent-generated test files had unsorted imports, unused imports, and `assert False` patterns that passed a narrow manual lint check but failed CI. The fix is simple: run `make lint` and `make test` as the final gate, every time.

### Agents Must Follow Existing Project Conventions (Task 008)

Three classes of errors from parallel agents, all caused by not reading existing patterns closely enough:

1. **Wrong file location.** An agent created the WebSocket Lambda router at `backend/src/deskai/infra/lambda_handlers/websocket.py` — a package path that doesn't exist. The existing pattern (`infra/lambda_handlers/bff.py`) was right there. **Rule:** Agent prompts must explicitly name the existing file to use as a pattern reference, and agents must read it before creating new files in the same area.

2. **Wrong test framework.** An agent wrote tests using `pytest.raises()` and bare pytest-style classes, but CI runs `unittest discover` with no pytest installed. Existing test files all use `unittest.TestCase` with `self.assertRaises()`. **Rule:** Agent prompts must specify the test framework and base class. Include an existing test file as a mandatory read before writing tests.

3. **Lint-dirty code.** Multiple agents produced files with unsorted imports, unused imports, and banned patterns (`assert False`). **Rule:** Each agent must run `make lint` on its own files before reporting completion.

**Root cause:** Agents optimize for speed and correctness of logic but skip convention alignment unless explicitly told. Future agent prompts must include: (a) an existing file to copy the pattern from, (b) the exact CI commands to run before marking done, (c) the test framework and base class to use.

### Always `cdk diff` Before `cdk deploy` (Task 009)

During the ElevenLabs provider migration, a blind `cdk deploy` triggered a cross-stack export failure that cascaded into `UPDATE_ROLLBACK_FAILED` state, required `continue-update-rollback --resources-to-skip` (nuclear last-resort), and resulted in an orphaned resource plus a wildcard IAM regression. A `cdk diff` would have shown the replacement and export deletion in 10 seconds — before any damage.

**Rule:** Treat `cdk diff` like `git diff` — never deploy without it. Never push infra changes directly to main; always use a PR.

### CDK Cross-Stack Reference Renames Require Two-Phase Deploy (Task 009)

Renaming a CDK construct ID (`DeepgramSecret` → `ElevenLabsSecret`) that has cross-stack exports causes CloudFormation to fail: it can't delete the old export while another stack imports it. The fix is two phases:

1. **Phase 1:** Deploy the consumer stack (compute) to stop importing the old export. Use string-literal ARN patterns derived from config instead of cross-stack references.
2. **Phase 2:** Deploy the provider stack (security) to remove the old export and create the new resource.

**Rule:** When renaming CDK constructs with cross-stack references, always plan a two-phase deploy. Avoid cross-stack exports for values that can be derived from config (like secret ARNs).

### IAM Policies Must Use Config-Derived Values, Not Hardcoded Names (Task 009)

An initial fix hardcoded secret names in IAM ARN patterns (`"elevenlabs-*"`). If someone later changes the secret name in config, the IAM policy would grant access to the old name and deny the new one.

**Rule:** Derive IAM resource ARNs from the same config that defines the resource names. Use `config.elevenlabs_secret_name` not `"elevenlabs"`. Single source of truth. Use `-??????` suffix (6 random chars) instead of `-*` for tighter matching.

### Preserve Secret Values During CDK Migration (Task 009)

Deleting a secret to let CDK recreate it causes downtime: between delete and manual `put-secret-value`, every Lambda call to that secret fails.

**Rule:** Before deleting a secret for CDK adoption: (1) save the real value with `get-secret-value`, (2) delete, (3) CDK deploy, (4) immediately restore with `put-secret-value`. Or better: use `cdk import` to adopt the existing resource without any deletion. Zero downtime.

## 15. Notes

- This file summarizes progress. Detailed requirements belong in individual task files.
- The task manager should stay concise even as the number of tasks grows.
- If the project becomes large, keep this file as the executive summary and move detailed reporting into separate supporting files.
