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
Architecture design complete — ready for repository bootstrap

### Overall Progress
20% complete

### Summary
- Task 001 completed: requirements baseline, consultation lifecycle, plan entitlements, failure matrix, and decision log documented
- Task 002 completed: repository layout, backend hexagonal architecture, contract inventory, data flow and configuration architecture documented
- Five new ADRs added (ADR-009 through ADR-013): repository layout, module organization, DI strategy, contract location, patient endpoints
- OI-006 resolved: patient endpoints added to API contract (ADR-013)
- One open decision remains (OI-005: specialty list) — needed before Task 006

### Immediate Next Step
Start `003-bootstrap-repository-and-engineering-foundation.md`

## 5. Priority Queue

List the most important tasks to work on next, in order.

| Rank | Task File | Title | Status | Reason |
| --- | --- | --- | --- | --- |
| 1 | `003-bootstrap-repository-and-engineering-foundation.md` | Bootstrap repository and engineering foundation | planned | The repo still needs its actual working packages, tooling, and local development foundation |
| 2 | `004-provision-aws-foundation-with-cdk.md` | Provision AWS foundation with CDK | planned | Core AWS infrastructure is required before auth, sessions, storage, and workflows can be implemented safely |
| 3 | `005-implement-authentication-and-plan-access-control.md` | Implement authentication and plan access control | planned | Secure physician access and backend-enforced plan rules are prerequisites for all protected product flows |
| 4 | `006-model-consultation-domain-persistence-and-audit.md` | Model consultation domain, persistence, and audit | planned | Consultation domain model, state machine, and audit events are prerequisites for all feature work |
| 5 | `007-build-bff-contracts-ui-config-and-feature-flags.md` | Build BFF contracts, UI config, and feature flags | planned | Exposes frontend-ready APIs, backend-driven UI configuration, and centralized feature flag behavior |

## 6. Active Blockers

List only blockers that currently prevent progress.

| Task File | Blocker | Depends On | Owner | Next Action |
| --- | --- | --- | --- | --- |
| None | No active blockers | N/A | N/A | Begin Task 002 |

## 7. Task Index

Use one row per real task. Do not include `000-task-template.md` as a delivery task.

| Task # | Task File | Title | Type | Priority | Status | Depends On | Progress % | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | `001-refine-mvp-requirements-and-delivery-decisions.md` | Refine MVP requirements and delivery decisions | Full Stack | Critical | done | None | 100 | Requirements baseline, consultation lifecycle, plan entitlements, failure matrix, and decision log documented. All four open issues resolved. Two new open decisions identified (specialty list, patient management). |
| 002 | `002-design-system-architecture-and-project-structure.md` | Design system architecture and project structure | Full Stack | Critical | done | `001-refine-mvp-requirements-and-delivery-decisions.md` | 100 | Repository layout, hexagonal backend architecture, contract inventory, data flow, and 5 new ADRs documented. OI-006 resolved. |
| 003 | `003-bootstrap-repository-and-engineering-foundation.md` | Bootstrap repository and engineering foundation | DevOps | High | planned | `002-design-system-architecture-and-project-structure.md` | 0 | Creates the working repo layout, tooling, package scaffolding, and local development conventions |
| 004 | `004-provision-aws-foundation-with-cdk.md` | Provision AWS foundation with CDK | Infrastructure | Critical | planned | `001-refine-mvp-requirements-and-delivery-decisions.md`, `002-design-system-architecture-and-project-structure.md`, `003-bootstrap-repository-and-engineering-foundation.md` | 0 | Provisions isolated `dev` and `prod` AWS foundations with security, storage, APIs, and monitoring baselines |
| 005 | `005-implement-authentication-and-plan-access-control.md` | Implement authentication and plan access control | Security | Critical | planned | `004-provision-aws-foundation-with-cdk.md` | 0 | Implements email/password auth, doctor and clinic context resolution, and backend-enforced plan authorization |
| 006 | `006-model-consultation-domain-persistence-and-audit.md` | Model consultation domain, persistence, and audit | Backend | Critical | planned | `001-refine-mvp-requirements-and-delivery-decisions.md`, `004-provision-aws-foundation-with-cdk.md`, `005-implement-authentication-and-plan-access-control.md` | 0 | Builds the consultation domain model, storage patterns, status rules, and attributable audit foundation |
| 007 | `007-build-bff-contracts-ui-config-and-feature-flags.md` | Build BFF contracts, UI config, and feature flags | Full Stack | High | planned | `005-implement-authentication-and-plan-access-control.md`, `006-model-consultation-domain-persistence-and-audit.md` | 0 | Exposes frontend-ready APIs, backend-driven UI configuration, and centralized feature flag behavior |
| 008 | `008-implement-realtime-consultation-session-transport.md` | Implement real-time consultation session transport | Backend | Critical | planned | `006-model-consultation-domain-persistence-and-audit.md`, `007-build-bff-contracts-ui-config-and-feature-flags.md` | 0 | Implements session lifecycle, WebSocket routes, audio ingestion, and processing handoff for live consultations |
| 009 | `009-integrate-transcription-provider-and-normalization.md` | Integrate transcription provider and normalization | Backend | Critical | planned | `008-implement-realtime-consultation-session-transport.md` | 0 | Adds the first `pt-BR` transcription provider, transcript normalization, and artifact persistence |
| 010 | `010-build-ai-processing-pipeline-and-artifacts.md` | Build AI processing pipeline and artifacts | Backend | Critical | planned | `006-model-consultation-domain-persistence-and-audit.md`, `009-integrate-transcription-provider-and-normalization.md` | 0 | Orchestrates transcript-to-artifact generation with strict schemas, evidence linking, and failure handling |
| 011 | `011-implement-review-finalization-and-export-workflows.md` | Implement review, finalization, and export workflows | Backend | Critical | planned | `007-build-bff-contracts-ui-config-and-feature-flags.md`, `010-build-ai-processing-pipeline-and-artifacts.md` | 0 | Adds physician edits, explicit final approval, audit attribution, and export generation from finalized content |
| 012 | `012-build-authenticated-react-app.md` | Build authenticated React app | Frontend | Critical | planned | `005-implement-authentication-and-plan-access-control.md`, `007-build-bff-contracts-ui-config-and-feature-flags.md`, `008-implement-realtime-consultation-session-transport.md`, `011-implement-review-finalization-and-export-workflows.md` | 0 | Builds the physician-facing app for login, live consultation, review, editing, and finalization in `pt-BR` |
| 013 | `013-build-public-website-and-entry-flows.md` | Build public website and entry flows | Frontend | Medium | planned | `003-bootstrap-repository-and-engineering-foundation.md`, `004-provision-aws-foundation-with-cdk.md` | 0 | Delivers the static marketing website and login entrypoints with MVP-accurate messaging and SEO-friendly structure |
| 014 | `014-add-observability-security-privacy-and-cost-controls.md` | Add observability, security, privacy, and cost controls | Security | High | planned | `004-provision-aws-foundation-with-cdk.md`, `008-implement-realtime-consultation-session-transport.md`, `009-integrate-transcription-provider-and-normalization.md`, `010-build-ai-processing-pipeline-and-artifacts.md`, `011-implement-review-finalization-and-export-workflows.md` | 0 | Adds dashboards, alarms, retention controls, PHI-aware logging, IAM tightening, and budget enforcement |
| 015 | `015-run-end-to-end-hardening-and-release-readiness.md` | Run end-to-end hardening and release readiness | QA | Critical | planned | `005-implement-authentication-and-plan-access-control.md`, `008-implement-realtime-consultation-session-transport.md`, `009-integrate-transcription-provider-and-normalization.md`, `010-build-ai-processing-pipeline-and-artifacts.md`, `011-implement-review-finalization-and-export-workflows.md`, `012-build-authenticated-react-app.md`, `013-build-public-website-and-entry-flows.md`, `014-add-observability-security-privacy-and-cost-controls.md` | 0 | Validates the integrated MVP, closes blockers, and prepares the release, rollback, and runbook package |

## 8. Milestones

Track major delivery checkpoints for the MVP.

| Milestone | Target Outcome | Status | Notes |
| --- | --- | --- | --- |
| Project Setup | Task system ready for execution | done | Template and manager files created |
| Infrastructure Ready | AWS baseline in place | planned | Covered by Tasks 003 and 004 |
| Backend Ready | Core API and business logic in place | planned | Covered by Tasks 005 through 011 |
| Frontend Ready | Core MVP interface in place | planned | Covered by Tasks 012 and 013 |
| MVP Ready | End-to-end usable first version | planned | Covered by Tasks 014 and 015 |

## 9. Open Issues

Track cross-task decisions, missing information, or conflicts.

| ID | Issue | Impact | Status | Next Action |
| --- | --- | --- | --- | --- |
| OI-001 | The first production transcription provider has not been selected from the approved candidates yet | Provider integration, cost analysis, and credential setup cannot be finalized | resolved | Deepgram (Nova-2 Medical) selected. See `docs/requirements/05-decision-log.md` DEC-001 and ADR-006. |
| OI-002 | Plan entitlement differences between `free_trial`, `plus`, and `pro` are not fully defined | Backend authorization and feature-flag behavior may need rework | resolved | All plans share core features; differentiation by usage limits. See `docs/requirements/03-plan-entitlements.md`. |
| OI-003 | Clinic audio retention defaults and deletion timing are not explicitly defined | Storage lifecycle, retention automation, and compliance behavior remain ambiguous | resolved | Plan-based retention: 7/30/90 days. See `docs/requirements/05-decision-log.md` DEC-003. |
| OI-004 | Export output scope beyond the finalized note is not fully specified | Export implementation could diverge from stakeholder expectations | resolved | PDF with metadata + finalized history + summary + accepted insights. No transcript. See DEC-004. |
| OI-005 | Specialty list and validation approach not defined | Domain model cannot validate specialty field | open | Product input needed before Task 006. Recommended: backend-managed enum, initially `general_practice` only. See OPEN-004. |
| OI-006 | Patient CRUD endpoints not defined in API contract | Cannot create consultations without patient management | resolved | Minimal `POST /v1/patients` and `GET /v1/patients` added to API contract. See ADR-013 and `docs/architecture/03-contract-inventory.md`. |

## 10. Recently Updated Tasks

List the most recently changed tasks first.

| Date | Task File | Change |
| --- | --- | --- |
| 2026-03-29 | `002-design-system-architecture-and-project-structure.md` | Completed: repository layout, backend hexagonal architecture, contract inventory, data flow and configuration documented |
| 2026-03-29 | `@task-manager.md` | Updated for Task 002 completion: status, progress, priority queue, OI-006 resolved |
| 2026-03-29 | `mvp-technical-specs.md` | Added ADR-009 through ADR-013, patient endpoints to API contract |
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

## 14. Notes

- This file summarizes progress. Detailed requirements belong in individual task files.
- The task manager should stay concise even as the number of tasks grows.
- If the project becomes large, keep this file as the executive summary and move detailed reporting into separate supporting files.
