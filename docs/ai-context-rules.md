# AI Context Rules

## 1. Purpose

This file must be loaded as context before any prompt, task, implementation, refactor, or architectural change in this project.

Use this file together with:

- `docs/mvp-business-rules.md`
- `docs/mvp-technical-specs.md`

Priority:

1. business rules
2. technical specs
3. this AI context rules file

## 2. How The AI Must Work In This Project

- always respect the business boundaries defined in `mvp-business-rules.md`
- always respect the technical source of truth defined in `mvp-technical-specs.md`
- do not invent product behavior that is not documented
- prefer small, maintainable, explicit solutions
- prefer clarity over cleverness
- prefer consistency over novelty
- when in doubt, keep decisions reversible

## 3. Core Engineering Principles

- always apply SOLID principles where appropriate
- always avoid unnecessary duplication and prefer DRY solutions
- always preserve Separation of Concerns
- prefer Convention over Configuration when it improves consistency and simplicity
- prefer Composition over Inheritance
- keep modules highly cohesive and loosely coupled
- use design patterns only when they clearly improve maintainability, extensibility, or clarity
- prefer domain-oriented design for complex business rules, even without fully adopting DDD
- design for testability, observability, and replaceability from the start

## 4. Backend Design Expectations

- keep business rules independent from frameworks and delivery mechanisms
- keep infrastructure concerns outside the domain core whenever possible
- avoid leaking AWS service details into core business logic
- favor explicit ports and adapters boundaries
- favor async and event-driven interactions when they improve resilience, scale, or decoupling

## 5. Reliability And Quality Expectations

- always implement error handling deliberately
- always log failures with enough context for diagnosis
- use retries only when they make technical and operational sense
- prefer idempotent operations for async and distributed flows
- do not hide failures silently

## 6. Security Expectations

- always treat consultation and user data as sensitive
- always minimize exposure of sensitive data
- prefer obfuscation or masking of sensitive data in logs, traces, and debugging outputs
- always follow least-privilege access principles
- never introduce broader permissions than necessary

## 7. Change Management Expectations

- document important technical decisions as short ADR entries in `docs/mvp-technical-specs.md`
- keep ADRs summarized, explicit, and easy to scan
- if a new feature may need controlled rollout, prefer using feature flags instead of hard-coded branching

## 8. What Belongs In Other Files

These items belong in `docs/mvp-technical-specs.md`, not here:

- concrete architecture decisions
- AWS service choices
- IAM strategy
- CORS policy
- feature flag implementation details
- backup and disaster recovery strategy
- budget alerts and infrastructure spending guardrails
- testing strategy decisions

These items belong in `docs/mvp-business-rules.md`, not here:

- plan types
- commercial boundaries
- user permissions by plan
- product limitations and business constraints
