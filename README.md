# DeskAI MVP

DeskAI is a medical documentation assistant for Brazilian physicians.

The MVP listens to doctor-patient consultations, generates a transcript, produces draft documentation artifacts for physician review, and stores the finalized record with auditability.

## Product Boundary

DeskAI is a documentation support tool, not a clinical decision-maker.

It must not:

- diagnose conditions
- prescribe medication
- suggest ICD codes as authoritative output
- make autonomous clinical decisions

Core rule: report what was said, never interpret what it means.

## Primary Workflow

1. The physician starts a consultation session.
2. The browser captures live audio.
3. The backend orchestrates real-time transcription in `pt-BR`.
4. After session closure, the AI pipeline generates draft artifacts with strict schema validation.
5. The physician reviews, edits, and explicitly finalizes the consultation.
6. Only the finalized record is treated as complete and exportable.

## MVP Scope Snapshot

- Market: Brazil
- Primary user: physician
- Primary mode: real-time consultation support
- Frontend: public website + authenticated React app
- Backend: Python on AWS Lambda
- Infrastructure: AWS CDK, Cognito, API Gateway, DynamoDB, S3, Step Functions, EventBridge/SQS/SNS
- Environments: `dev`, `prod`

Environment distinction:
- `dev` and `prod` are AWS deployment environments.
- Local execution on developer machines is separate and does not define a third AWS environment.

## Non-Negotiables

- User-facing content must default to Brazilian Portuguese (`pt-BR`).
- Code, comments, and technical documentation must be written in English.
- Consultation data must be treated as sensitive health information.
- No AI-generated artifact is final without physician review.
- Unsupported or uncertain content must be marked as incomplete or pending review, never invented.
- Insights are review flags only and must include supporting evidence from the consultation.

## Source Of Truth

Use the files below as the canonical MVP definition:

1. [`docs/ai-context-rules.md`](/Users/gabrielsantiago/Documents/DeskAI/docs/ai-context-rules.md)
2. [`docs/mvp-business-rules.md`](/Users/gabrielsantiago/Documents/DeskAI/docs/mvp-business-rules.md)
3. [`docs/mvp-technical-specs.md`](/Users/gabrielsantiago/Documents/DeskAI/docs/mvp-technical-specs.md)
4. [`tasks/@task-manager.md`](/Users/gabrielsantiago/Documents/DeskAI/tasks/@task-manager.md)
5. [`docs/implementation-prompt.md`](/Users/gabrielsantiago/Documents/DeskAI/docs/implementation-prompt.md)

## Repository Layout

```text
DeskAI/
├── backend/      # Python backend (core + BFF + handlers)
├── app/          # Authenticated React + TypeScript app
├── website/      # Public static website
├── contracts/    # Shared API and schema contracts
├── infra/        # AWS CDK infrastructure
├── tools/        # Repo-level helper scripts
├── docs/         # Product and architecture documentation
└── tasks/        # Task execution tracking
```

## Quick Start

1. Read [`docs/local-development.md`](/Users/gabrielsantiago/Documents/DeskAI/docs/local-development.md).
2. Copy root and package `.env.example` files as needed.
3. Install and run package-level commands:
   - `backend/`: `make install`, `make lint`, `make test`
   - `infra/`: `make install`, `make synth`
   - `app/`: `npm install`, `npm run dev`
   - `website/`: `npm install`, `npm run dev`

## Current Delivery State

- Task `001` completed: requirements, lifecycle, entitlements, failure behavior, and decision log.
- Task `002` completed: architecture and project structure decisions.
- Task `003` establishes repository scaffolding, tooling conventions, local setup docs, and CI placeholders.

For execution progress, use [`tasks/@task-manager.md`](/Users/gabrielsantiago/Documents/DeskAI/tasks/@task-manager.md).
