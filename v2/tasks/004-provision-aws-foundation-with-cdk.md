# Task 004: Provision AWS Foundation With CDK

## 1. Overview

### Objective
Define and provision the MVP’s baseline AWS infrastructure in CDK for `dev` and `prod`, including networking edges, storage, auth, orchestration primitives, encryption, and foundational monitoring.

### Why This Matters
The architecture is explicitly AWS serverless-first. The team needs a repeatable, isolated, and secure cloud baseline before building the core application flows on top of it.

### Task Type
- Infrastructure

### Priority
- Critical

## 2. Context

### Product Context
The MVP must support live consultation capture, async processing, secure storage of sensitive health information, and low-cost operation.

### Technical Context
This task creates the AWS resources that later backend, BFF, frontend, and processing tasks will target. It also establishes naming, encryption, retention, and environment isolation patterns.

### Related Systems
- AWS
- Authentication
- Storage
- Observability
- CI/CD

### Dependencies
- `001-refine-mvp-requirements-and-delivery-decisions.md`
- `002-design-system-architecture-and-project-structure.md`
- `003-bootstrap-repository-and-engineering-foundation.md`

### Required Reading
Before implementing this task, read these documents in addition to the standard reading list in `implementation-prompt.md`:
- `docs/architecture/01-repository-layout.md`
- `docs/architecture/04-data-flow-and-configuration.md`
- `docs/requirements/03-plan-entitlements.md`
- `docs/requirements/04-failure-behavior-matrix.md`

## 3. Scope

### In Scope
- Create CDK app and stacks for `dev` and `prod`.
- Provision Cognito, CloudFront, HTTP API, WebSocket API, Lambda foundations, Step Functions, DynamoDB, S3, EventBridge, SQS, SNS, KMS, Secrets Manager, CloudWatch, and budget alerts.
- Configure DynamoDB PITR, S3 versioning where appropriate, and KMS encryption.
- Define explicit CORS policy and environment-specific origin settings.
- Define IAM roles and permissions boundaries for the initial service set.
- Define basic dashboards, alarms, and DLQ infrastructure.

### Out of Scope
- Full implementation of all business logic handlers.
- Production website and authenticated app assets.
- Deep disaster recovery automation beyond baseline recoverability controls.

## 4. Requirements

### Functional Requirements
- `dev` and `prod` must be fully isolated.
- Core resources must use predictable, environment-specific naming.
- Infrastructure must support the required MVP services and future feature implementation without structural rework.
- The budget alert must notify the team if monthly AWS spend exceeds `$5`.

### Non-Functional Requirements
- IaC must be the source of truth for cloud resources.
- IAM permissions must follow least privilege by responsibility.
- Infrastructure definitions must be easy to inspect, update, and deploy by a small team.

### Business Rules
- Consultation data is sensitive health information and must be protected.
- Audio retention must be configurable according to clinic policy.
- The final reviewed note may be retained even if raw audio is deleted.

### Technical Rules
- Use AWS CDK only for MVP infrastructure.
- Only `dev` and `prod` environments are allowed.
- Primary storage is DynamoDB + S3.
- Use explicit CORS policies and avoid production wildcards.

## 5. Implementation Notes

### Proposed Approach
Create separate environment stacks with shared constructs for auth, APIs, storage, processing, observability, and security. Keep naming and configuration centralized so later stacks can reference common primitives safely.

### AWS / Infrastructure Notes
- Include KMS keys, secrets placeholders, DynamoDB PITR, S3 bucket policies, API stages, SNS topic, alarm set, and budget notification plumbing.
- Decide whether CloudFront distributions for public and authenticated frontend assets are shared or separated and document the choice.

### Backend Notes
- Provide Lambda execution roles and config injection patterns that later services can reuse.

### Frontend Notes
- Define frontend hosting and origin relationships needed for CORS and asset delivery.

## 6. Deliverables

The task should produce:
- CDK app and stack definitions
- Environment configuration and naming strategy
- Security and encryption baselines
- Monitoring and budget baseline resources
- Deployment documentation

## 7. Acceptance Criteria

- [ ] `dev` and `prod` infrastructure definitions exist and are isolated.
- [ ] Required MVP AWS services are provisioned in CDK with least-privilege defaults.
- [ ] DynamoDB and S3 recovery-related settings are configured.
- [ ] Budget alerting is defined for monthly spend above `$5`.
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- CDK synth validation
- Infrastructure unit or snapshot tests where practical

### Manual Verification
Deploy to `dev` and confirm core resources exist, encryption is enabled, alarms are created, and environment-specific names and origins are correct.

## 9. Risks and Edge Cases

### Risks
- Overly broad IAM could expose sensitive data.
- Missing environment isolation could mix dev and prod data.
- Early stack coupling could make later service evolution harder.

### Edge Cases
- Budget resources may require a slightly different provisioning path than the rest of the CDK stack.
- WebSocket and HTTP APIs may need separate deployment and logging settings.
- Some secrets may start as placeholders until provider choices are finalized.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
