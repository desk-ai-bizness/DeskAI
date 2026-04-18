# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Project Overview

DeskAI is an AI-assisted medical documentation product for Brazilian physicians.

The MVP supports consultation documentation by:

- producing a consultation transcript
- generating a draft structured medical history
- generating a consultation summary
- highlighting reviewable documentation, consistency, and clinical attention flags

DeskAI is a documentation support tool. It is not a clinical decision-maker.

Core rule: report what was said, never interpret what it means.

## Current Source Of Truth

The repository root, together with `./docs` and `./tasks`, is the current planning and implementation source of truth for this project.

If older notes or files elsewhere in the repository conflict with those files, prefer the root `README.md`, `./docs`, and `./tasks`.

Read these files before planning, implementing, refactoring, or making architectural decisions:

1. `docs/ai-context-rules.md`
2. `docs/mvp-business-rules.md`
3. `docs/mvp-technical-specs.md`
4. The task file being implemented
5. `tasks/@task-manager.md`

Priority order when rules conflict:

1. `docs/mvp-business-rules.md`
2. `docs/mvp-technical-specs.md`
3. `docs/ai-context-rules.md`
4. `tasks/@task-manager.md`
5. this `AGENTS.md`

## Language Rules

- Code, code comments, and technical documentation must be written in English.
- User-facing product content must be written in Brazilian Portuguese (`pt-BR`).
- Consultation transcripts must be generated in Brazilian Portuguese (`pt-BR`).
- AI prompts and output templates for the medical scribe flow should remain in Brazilian Portuguese (`pt-BR`) where applicable.

## Product Boundaries

- The MVP operates in Brazil.
- The initial target user is a physician.
- The MVP is limited to general practice/generalist consultations.
- Each consultation belongs to one physician, one patient, and one clinic context.
- The MVP supports one specialty per consultation.
- Authentication is email + password only.
- Do not add Google login, Facebook login, social login, or SSO alternatives.
- The supported MVP plan types are `free_trial`, `plus`, and `pro`.
- Plan-based access control is part of the MVP business model and must be enforced consistently.

The MVP must not:

- generate automatic diagnoses
- generate automatic prescriptions
- act without physician review
- support multi-specialty handling within the same consultation
- present clinical suggestions as authoritative decisions
- deeply integrate with external medical record systems as part of the MVP

## Required Output Rules

For each successfully processed consultation, the MVP must produce:

- a raw transcript
- a draft structured medical history
- a consultation summary
- a list of flagged insights for review
- evidence excerpts linking each flagged insight to the related consultation dialogue

If an output cannot be produced reliably, mark it as incomplete or pending review instead of inventing content.

## Physician Review Rules

- No AI-generated output is final until reviewed by the physician.
- The physician must be able to edit draft medical history, summary, and insights.
- Finalization must be an explicit physician action.
- A finalized consultation is immutable and locked from further edits.
- Only finalized consultations may be exported.

## Architecture Rules

The MVP uses an AWS serverless-first architecture with four layers:

1. Web frontend
2. BFF layer
3. Core backend layer
4. Infrastructure and data layer

Implementation rules:

- Backend language: Python
- Authenticated app: React + TypeScript + Vite
- Public website: standard HTML/CSS with minimal JavaScript when needed
- Infrastructure as code: AWS CDK
- Primary data storage: DynamoDB + S3
- Environments: `dev` and `prod` only

Design constraints:

- Follow Hexagonal Architecture principles.
- Keep business rules independent from frameworks, AWS services, and delivery mechanisms.
- Keep infrastructure concerns outside the domain core whenever possible.
- Favor explicit ports and adapters boundaries.
- Keep business logic out of the frontend.
- Keep the frontend as backend-driven as practical.
- Prefer configuration over hardcoded frontend workflow behavior where practical.
- Prefer async and event-driven interactions when they improve resilience, scale, or decoupling.

## Engineering Rules

- Do not invent product behavior that is not documented.
- Prefer small, maintainable, explicit solutions.
- Prefer clarity over cleverness.
- Prefer consistency over novelty.
- When in doubt, keep decisions reversible.
- Apply SOLID where appropriate.
- Avoid unnecessary duplication and prefer DRY solutions.
- Preserve separation of concerns.
- Prefer composition over inheritance.
- Keep modules highly cohesive and loosely coupled.
- Design for testability, observability, and replaceability from the start.

## Testing and TDD Rules

All code where tests are applicable must follow strict Test-Driven Development.

TDD workflow:

1. **Red** — Write a failing test that defines the expected behavior. Run it. It must fail.
2. **Green** — Write the minimum implementation code to make the test pass.
3. **Refactor** — Clean up while keeping all tests green.

Mandatory rules:

- Never write implementation code without a failing test first.
- Every new function, module, endpoint, adapter, handler, or infrastructure construct gets its test first.
- Every bug fix starts with a failing test that reproduces the bug before fixing it.
- All tests must pass before committing.
- No production code may be merged without corresponding tests passing in CI.

TDD applies to all test types, not just unit tests:

- Unit tests — domain entities, value objects, services, business rules.
- Application tests — use cases with mocked port interfaces.
- Integration tests — adapters against real or emulated services (localstack, moto).
- Handler tests — Lambda handlers with event fixtures.
- BFF tests — view models, feature flag evaluation, UI config assembly.
- Infrastructure tests — CDK stack synthesis assertions.
- Contract tests — YAML schema validation, API response shape.
- API tests — HTTP request/response round-trips.
- End-to-end tests — acceptance-driven, write expected outcomes first.

TDD does not apply to:

- Pure configuration files (`.env`, `cdk.json`, YAML configs).
- Static assets (HTML, CSS, images).
- Exploratory prototypes — but tests must exist before merging to main.

See `docs/mvp-technical-specs.md` section 23 for the full testing strategy.

## Reliability Rules

- Always implement error handling deliberately.
- Always log failures with enough context for diagnosis.
- Never hide failures silently.
- Use retries only when they make technical and operational sense.
- Prefer idempotent operations for async and distributed flows.

## Security And Privacy Rules

- Always treat consultation and user data as sensitive health information.
- Always minimize exposure of sensitive data.
- Never log raw medical content, CPF, PII, or unnecessary patient-identifiable data.
- Prefer masking or obfuscation in logs, traces, and debugging outputs.
- Follow least-privilege IAM and access principles.
- Never introduce broader permissions than necessary.
- Access to consultation data must be limited to authorized users in the correct clinic context.
- Preserve auditability for edits, approvals, and sensitive access.

## AI Pipeline Rules

- Enforce the report-only rule: summarize what was said, never what it means.
- Do not fabricate symptoms, diagnoses, medications, allergies, findings, plans, or follow-up instructions.
- Separate confirmed facts from uncertain or incomplete information.
- Insights are review flags, not conclusions.
- Insight categories are limited to documentation gaps, consistency issues, and clinical attention flags based on explicit consultation statements.
- Every insight must include supporting evidence from the consultation.
- Clinical attention flags must never be presented as diagnoses.
- Use strict schema validation before accepting generated artifacts.
- Keep timestamps and confidence metadata when available from the provider or pipeline.
- If support is insufficient, surface the output as incomplete or needing review rather than inventing content.

## Task Workflow

Tasks live in `tasks/` and the progress tracker is `tasks/@task-manager.md`.

When working on a task:

- treat the task file as the implementation scope
- implement the task end to end, not partially
- include required code, configuration, infrastructure, schema, tests, and documentation changes within scope
- update `tasks/@task-manager.md` whenever a task is created, started, blocked, completed, canceled, or materially changed
- preserve the task manager structure and table formats unless there is a strong reason to change them
- keep task summaries short, factual, and implementation-oriented
- reference task files by filename
- if a task file and the manager conflict, note the conflict in `Open Issues`

Task manager statuses:

- `planned`
- `in_progress`
- `blocked`
- `done`
- `canceled`

Current next step: `013-build-public-website-and-entry-flows.md`

## Change Management

- Document important technical decisions as short ADR entries in `docs/mvp-technical-specs.md`.
- Keep ADRs concise, explicit, and easy to scan.
- If a new feature may need controlled rollout, prefer feature flags instead of hardcoded branching.

## Commit Messages

Use conventional commit style when creating or proposing commits.

Examples:

- `feat: add consultation review endpoint`
- `fix: handle incomplete transcript artifact state`
- `docs: update MVP architecture guidance`
- `test: add consultation lifecycle unit tests`
- `chore: align tooling configuration`
