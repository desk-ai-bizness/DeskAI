# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DeskAI — Medical AI Scribe** for Brazilian physicians. Captures consultation audio, transcribes with speaker diarization, generates structured summaries, and stores them for physician review and approval.

**Status:** Pre-MVP — Tasks 001–002 complete (requirements + architecture design). Next: Task 003 (bootstrap repo).

**Core principle:** Report, never interpret. The AI summarizes what was said, never what it means. Every summary requires physician approval before permanent storage.

## Source of Truth

The `v2/` directory is the current source of truth. Root-level `TECHNICAL_PLAN.md` and `blueprint-medical-ai.md` reference an **older, superseded stack** — ignore them.

Before any implementation work, read these files in order:

1. `v2/docs/ai-context-rules.md` — Engineering principles and AI behavior rules
2. `v2/docs/mvp-business-rules.md` — Product boundaries, plan types, consultation rules
3. `v2/docs/mvp-technical-specs.md` — Architecture, AWS services, ADRs
4. The specific task file in `v2/tasks/`
5. `v2/tasks/@task-manager.md` — Progress tracker and priority queue

Follow the execution protocol in `v2/implementation-prompt.md` when implementing tasks.

## Language Rules

- **Code, comments, variable names, commits, PRs, docs:** English.
- **AI prompts and output templates (scribe pipeline):** Brazilian Portuguese (pt-BR).
- **User-facing strings and product content:** Brazilian Portuguese (pt-BR).

## Architecture

AWS serverless, Hexagonal Architecture. Four layers:

1. **Web Frontend** (`app/`) — React + TypeScript + Vite. Presentation only; "as dumb as possible" with backend-driven UI config.
2. **BFF Layer** (`backend/src/deskai/bff/`) — Shapes backend data into UI-friendly payloads, injects UI config/labels/feature flags.
3. **Core Backend** (`backend/src/deskai/`) — Python on Lambda. Owns domain logic: consultation lifecycle, transcription, AI pipeline, review/finalization, audit.
4. **Infrastructure** (`infra/`) — AWS CDK. Cognito, API Gateway (HTTP + WebSocket), DynamoDB, S3, Step Functions, EventBridge/SQS/SNS.

Additional top-level packages:
- `website/` — Static public marketing site
- `contracts/` — Shared API schemas (HTTP, WebSocket, UI config, feature flags)
- `tools/` — Dev scripts and utilities

### Package Dependency Rules

- `contracts/` depends on nothing
- `backend/` depends on `contracts/` only
- `app/` depends on `contracts/` only
- `website/` depends on nothing
- `infra/` depends on `backend/` (Lambda paths)

## Backend Hexagonal Architecture

```
handlers/ → application/ → domain/  (pure Python, no deps)
              ↓                ↑
           ports/  ←────── adapters/  (AWS SDK, external libs)
              ↑
           bff/  (frontend-ready payloads)
```

| Layer | May Depend On | Must Not Depend On |
|-------|---------------|-------------------|
| Domain | Nothing (pure Python, stdlib) | Application, Adapters, Handlers, BFF, AWS SDK |
| Application | Domain, Ports | Adapters, Handlers, BFF, AWS SDK |
| Ports | Domain (type hints only) | Adapters, Handlers, BFF, AWS SDK |
| Adapters | Domain, Ports, AWS SDK, external libs | Handlers, BFF |
| BFF | Domain, Application, Ports | Adapters directly |
| Handlers | Application, BFF, Domain types | Direct adapter usage |
| Shared | Nothing (cross-cutting utils) | Domain, Application, Adapters, Handlers, BFF |

**Dependency injection:** Constructor injection with simple factory (`container.py`). No DI framework. Tests create use cases with mock ports directly.

## Tech Stack (MVP)

| Layer | Technology |
|-------|------------|
| Frontend | React + TypeScript + Vite |
| Backend | Python, AWS Lambda |
| IaC | AWS CDK (Python) |
| Auth | Amazon Cognito (email+password only, no social login) |
| Database | DynamoDB + S3 |
| ASR | Deepgram (Nova-2 Medical, pt-BR) |
| LLM | Claude API (Anthropic) |
| Orchestration | AWS Step Functions |
| Events | EventBridge, SQS, SNS |
| Environments | `dev`, `prod` |

Environment config: resource naming `deskai-{env}-{resource}`, values in `infra/config/`, Lambda reads `DESKAI_ENV`.

## Backend Design Rules

- Hexagonal Architecture: business rules independent from frameworks and AWS services.
- Ports and adapters boundaries between domain and infrastructure.
- Use `asyncio` for async external API calls (not `httpx`).
- Idempotent operations for async and distributed flows.
- Business logic in backend services, never in frontend.
- Domain entities use Result types for expected violations; exceptions only for programming errors.
- ADRs documented in `v2/docs/mvp-technical-specs.md`.

## Security (Non-Negotiable)

- All consultation and user data is sensitive — never log PII, CPF, or medical records.
- Encrypt sensitive fields at rest (KMS). Mask sensitive data in logs/traces.
- Least-privilege IAM. Do not introduce broader permissions than necessary.
- LGPD compliance required — audit trail for every data access.

## AI Pipeline Rules

- System prompt enforces "report only, never interpret" — no diagnoses, no ICD codes, no clinical decisions.
- Every summary field must link to transcript timestamps.
- JSON output validated against schema before storage.
- Flag unclear/uncertain sections with confidence scores.
- If output cannot be produced reliably, mark as incomplete — never fabricate content.

## Task Workflow

Tasks are in `v2/tasks/` numbered 001–015. The task manager (`v2/tasks/@task-manager.md`) tracks status: `planned`, `in_progress`, `blocked`, `done`, `canceled`.

After completing a task: update status, progress %, recent changes, blockers, and milestones in `@task-manager.md`.

## Commit Messages

Conventional commits:
```
feat: add consultation upload endpoint
fix: handle empty transcript from Deepgram
chore: update dependencies
docs: add API documentation
test: add consultation service tests
```
