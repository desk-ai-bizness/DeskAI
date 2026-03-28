# DeskAI — Medical AI Scribe

An AI-powered consultation assistant that acts as a **smart medical scribe** for physicians.

## What It Does

The service listens to doctor-patient consultations, transcribes the audio with speaker labels, generates a structured summary of everything discussed, and stores it for the doctor to review and approve.

```
Doctor talks to patient
        |
Audio captured (browser)
        |
Real-time transcription with speaker diarization
        |
AI generates structured summary
        |
Doctor reviews, edits, approves
        |
Stored securely (DynamoDB + S3)
```

## What It Is NOT

This is **not** an AI doctor. It does not:
- Diagnose conditions
- Interpret symptoms
- Suggest ICD-10 codes
- Make any clinical decisions

The AI **observes and organizes**. It does not **interpret or diagnose**. Every summary requires physician review and approval before being saved.

## Target Market

Brazilian physicians and clinics — built for Portuguese-first medical vocabulary and documentation standards.

### Key Numbers

| Metric | Value |
|--------|-------|
| Active physicians in Brazil | ~500,000 |
| EHR penetration | ~8% of institutions |
| Documentation time per consultation | ~7 minutes (AI reduces to ~2 min) |
| Physicians using telemedicine | 68% |

## Architecture

AWS serverless with Hexagonal Architecture across four layers:

1. **Web Frontend** — React app (authenticated) + public marketing site
2. **BFF Layer** — Frontend-specific APIs on AWS Lambda
3. **Core Backend** — Python on AWS Lambda (domain logic, consultation lifecycle, AI pipeline)
4. **Infrastructure** — Cognito, API Gateway, DynamoDB, S3, Step Functions, EventBridge

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React (authenticated app) + public website |
| Backend | Python, AWS Lambda |
| IaC | AWS CDK |
| Auth | Amazon Cognito |
| Database | DynamoDB + S3 |
| ASR | Deepgram (Nova-2 Medical, pt-BR) |
| LLM | Claude API (Anthropic) |
| Orchestration | AWS Step Functions |
| Events | EventBridge, SQS, SNS |
| Environments | `dev`, `prod` |

## Project Status

**Status:** Pre-MVP — planning complete, ready to begin implementation.

### Implementation Roadmap (15 Tasks)

- [ ] 001 — Refine MVP requirements and delivery decisions
- [ ] 002 — Design system architecture and project structure
- [ ] 003 — Bootstrap repository and engineering foundation
- [ ] 004 — Provision AWS foundation with CDK
- [ ] 005 — Implement authentication and plan access control
- [ ] 006 — Model consultation domain, persistence, and audit
- [ ] 007 — Build BFF contracts, UI config, and feature flags
- [ ] 008 — Implement real-time consultation session transport
- [ ] 009 — Integrate transcription provider and normalization
- [ ] 010 — Build AI processing pipeline and artifacts
- [ ] 011 — Implement review, finalization, and export workflows
- [ ] 012 — Build authenticated React app
- [ ] 013 — Build public website and entry flows
- [ ] 014 — Add observability, security, privacy, and cost controls
- [ ] 015 — Run end-to-end hardening and release readiness

## Documentation

All current documentation lives in [`v2/`](./v2/):

- **[`v2/docs/ai-context-rules.md`](./v2/docs/ai-context-rules.md)** — Engineering principles and AI behavior rules
- **[`v2/docs/mvp-business-rules.md`](./v2/docs/mvp-business-rules.md)** — Product boundaries, plan types, consultation rules
- **[`v2/docs/mvp-technical-specs.md`](./v2/docs/mvp-technical-specs.md)** — Architecture, AWS services, and ADRs
- **[`v2/tasks/@task-manager.md`](./v2/tasks/@task-manager.md)** — Task progress tracker and priority queue
- **[`v2/implementation-prompt.md`](./v2/implementation-prompt.md)** — Task execution protocol

## Economics

| Item | Per Consultation |
|------|------------------|
| Deepgram (~15 min) | $0.09 |
| Claude (summary) | $0.02 |
| Infrastructure | $0.01 |
| **Total** | **$0.12** |

Target pricing: R$199-349/month per doctor (50-70% cheaper than human scribes).

## Design Principles

1. **Report, never interpret** — summarize what was said, never what it means
2. **Doctor always in control** — every summary requires human approval
3. **Zero learning curve** — one button to start, one to stop
4. **Works on any device** — phone, tablet, computer
5. **Portuguese-first** — Brazilian medical vocabulary

## License

Private — all rights reserved.
