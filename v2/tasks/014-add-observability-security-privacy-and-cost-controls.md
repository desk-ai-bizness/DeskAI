# Task 014: Add Observability, Security, Privacy, And Cost Controls

## 1. Overview

### Objective
Implement the cross-cutting controls that make the MVP operable and trustworthy in production: observability, structured logging, privacy protections, retention controls, alarms, dashboards, and cost guardrails.

### Why This Matters
The product handles sensitive health information and relies on distributed serverless workflows. The team needs visibility, protection, and cost control before production use.

### Task Type
- Security

### Priority
- High

## 2. Context

### Product Context
Physicians and clinics must be able to trust that consultation data is handled safely, critical failures are visible, and retention behavior respects clinic policy.

### Technical Context
This task builds on the foundational infrastructure and application flows to add the production-grade controls specified in the technical docs.

### Related Systems
- AWS
- Backend API
- Storage
- Observability
- Security

### Dependencies
- `004-provision-aws-foundation-with-cdk.md`
- `008-implement-realtime-consultation-session-transport.md`
- `009-integrate-transcription-provider-and-normalization.md`
- `010-build-ai-processing-pipeline-and-artifacts.md`
- `011-implement-review-finalization-and-export-workflows.md`

## 3. Scope

### In Scope
- Implement structured logging and core metrics across auth, session, provider, AI, review, and export flows.
- Implement CloudWatch dashboards and alarms for the required MVP indicators.
- Implement PHI-aware logging and masking rules.
- Implement configurable audio retention and deletion behavior aligned to clinic policy.
- Implement IAM reviews and permission tightening for service roles.
- Validate budget alerts, DLQs, and failure notifications.

### Out of Scope
- Full compliance certification programs.
- Multi-region disaster recovery.
- Complex SIEM integrations outside MVP needs.

## 4. Requirements

### Functional Requirements
- The team must be able to observe sign-in success/failure, consultation creation, session start, audio ingestion, provider latency/failure, AI generation success/failure, review completion, and export success.
- Critical error spikes, Step Functions failures, disconnect spikes, DLQ growth, and provider outages must trigger alerts.
- Audio retention must be configurable so clinics can retain or delete audio while keeping final notes when allowed.
- Logs must avoid raw audio and full transcript text by default.

### Non-Functional Requirements
- Access and logging controls must minimize PHI exposure.
- Monitoring must be actionable and low-noise for a small team.
- Cost controls must remain lightweight and aligned with serverless MVP operation.

### Business Rules
- Consultation data is sensitive health information.
- Logs and operational records must avoid unnecessary patient-identifiable information.
- The clinic may retain the final reviewed note even if audio is deleted.

### Technical Rules
- Use structured logs with request IDs and consultation IDs.
- Use least-privilege IAM and separate permissions by service responsibility.
- Enforce the `$5` monthly budget guardrail.

## 5. Implementation Notes

### Proposed Approach
Apply a shared logging and metrics standard across Lambdas, define alarm thresholds for required signals, implement retention jobs or lifecycle controls, and perform a permission review on every major service role.

### AWS / Infrastructure Notes
- Validate CloudWatch alarms, SNS notifications, SQS DLQ monitoring, KMS usage, and bucket lifecycle or deletion workflows.

### Backend Notes
- Add structured log fields, error categories, and metric emission points to all critical paths.
- Ensure retention enforcement does not delete finalized notes that must remain.

### Frontend Notes
- Surface user-safe operational messages for critical failure states without exposing internal details.

## 6. Deliverables

The task should produce:
- Logging and metrics standards in code
- Dashboards and alarms
- Retention and deletion control implementation
- IAM tightening updates
- Operational documentation and runbooks

## 7. Acceptance Criteria

- [ ] Required operational metrics and alarms are implemented and validated.
- [ ] Logs avoid raw audio and full transcript text by default and use structured context.
- [ ] Audio retention and deletion behavior is configurable and does not remove required finalized notes.
- [ ] Service permissions are reviewed and tightened to least privilege.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit or integration tests for retention and masking logic
- Alarm and metric validation where practical

### Manual Verification
Trigger representative failures and retention scenarios, confirm alarms fire, inspect logs for masking, and verify finalized notes remain available when audio is deleted.

## 9. Risks and Edge Cases

### Risks
- Overlogging could expose PHI.
- Poor alert tuning could create alert fatigue or miss incidents.
- Retention jobs could accidentally delete data that should persist.

### Edge Cases
- A clinic changes retention policy after consultations already exist.
- An export artifact should remain even after raw audio deletion.
- Provider outages cause cascading failures across real-time and async workflows.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
