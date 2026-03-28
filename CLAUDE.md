# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DeskAI — Medical AI Scribe** for Brazilian physicians. Captures doctor-patient consultation audio, transcribes with speaker diarization, generates structured summaries, and stores them for physician review and approval.

**Status:** Pre-MVP — planning complete, ready to begin implementation (Task 001).

**Core principle:** Report, never interpret. The AI summarizes what was said, never what it means. Every summary requires physician approval before permanent storage.

## Architecture

AWS serverless, Hexagonal Architecture. Four layers:

1. **Web Frontend** — React app (authenticated) + public marketing site. Presentation only; must be "as dumb as possible" with backend-driven UI configuration.
2. **BFF Layer** — Frontend-specific APIs on AWS Lambda. Shapes backend data into UI-friendly payloads, injects UI config/labels.
3. **Core Backend** — Python on AWS Lambda. Owns domain logic: consultation lifecycle, transcription integration, AI pipeline, review/finalization, audit.
4. **Infrastructure** — Cognito (auth), API Gateway (HTTP + WebSocket), DynamoDB + S3 (data), Step Functions (orchestration), EventBridge/SQS/SNS (events).

Key AWS services: Cognito, CloudFront, API Gateway (HTTP + WebSocket), Lambda, Step Functions, DynamoDB, S3, EventBridge, SQS, SNS, Secrets Manager, KMS, CloudWatch.

## Tech Stack (MVP)

| Layer | Technology |
|-------|------------|
| Frontend | React (authenticated app) + public website |
| Backend | Python, AWS Lambda |
| IaC | AWS CDK |
| Auth | Amazon Cognito (email+password only, no social login) |
| Database | DynamoDB + S3 |
| ASR | Deepgram (Nova-2 Medical, pt-BR) |
| LLM | Claude API (Anthropic) |
| Orchestration | AWS Step Functions |
| Events | EventBridge, SQS, SNS |
| Environments | `dev`, `prod` |

**Note:** The root-level `TECHNICAL_PLAN.md` and `blueprint-medical-ai.md` reference an older stack (FastAPI, PostgreSQL, Railway/Supabase, Celery+Redis). The `v2/` directory is the current source of truth.

## Language Rules

- **Code, comments, variable names, commits, PRs, docs:** English.
- **AI prompts and output templates (scribe pipeline):** Brazilian Portuguese (pt-BR).
- **User-facing strings and product content:** Brazilian Portuguese (pt-BR).

## Source of Truth (v2/)

All implementation decisions live in `v2/`. Read these before any implementation work:

1. `v2/docs/ai-context-rules.md` — Engineering principles and AI behavior rules
2. `v2/docs/mvp-business-rules.md` — Product boundaries, plan types, consultation rules
3. `v2/docs/mvp-technical-specs.md` — Architecture, AWS services, ADRs
4. `v2/tasks/@task-manager.md` — Progress tracker and priority queue
5. `v2/implementation-prompt.md` — Task execution protocol

When implementing a task, follow the execution protocol in `v2/implementation-prompt.md`: read context files in order, implement the assigned task file fully, update `@task-manager.md` when done.

## Task Workflow

Tasks are in `v2/tasks/` numbered 001–015. The task manager (`v2/tasks/@task-manager.md`) tracks status using: `planned`, `in_progress`, `blocked`, `done`, `canceled`.

Current next step: Task 001 (refine MVP requirements and delivery decisions).

## Backend Design Rules

- Hexagonal Architecture: business rules independent from frameworks and AWS services.
- Ports and adapters boundaries between domain and infrastructure.
- Use `asyncio` for handling async external API calls (not `httpx`).
- Async/event-driven where it improves resilience or decoupling.
- Idempotent operations for async and distributed flows.
- Business logic in backend services, never in frontend.
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

## Commit Messages

Conventional commits:
```
feat: add consultation upload endpoint
fix: handle empty transcript from Deepgram
chore: update dependencies
docs: add API documentation
test: add consultation service tests
```
