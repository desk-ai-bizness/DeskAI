# Task 010: Build AI Processing Pipeline And Artifacts

## 1. Overview

### Objective
Implement the post-consultation AI processing pipeline that converts normalized transcripts into a draft structured medical history, consultation summary, and evidence-backed review insights.

### Why This Matters
These artifacts are the core value of the MVP. They must be generated reliably, remain faithful to the consultation, and support physician review without introducing unsupported medical content.

### Task Type
- Backend

### Priority
- Critical

## 2. Context

### Product Context
After a consultation ends, the system must produce reviewable documentation outputs that save physician time while preserving human control and factual fidelity.

### Technical Context
The processing layer runs after session closure, uses strict schemas, stores artifacts in S3, tracks status in DynamoDB, and should be orchestrated through Step Functions.

### Related Systems
- AWS
- Backend API
- Storage
- Observability

### Dependencies
- `006-model-consultation-domain-persistence-and-audit.md`
- `009-integrate-transcription-provider-and-normalization.md`

## 3. Scope

### In Scope
- Implement the post-session processing workflow in Step Functions Standard.
- Implement the conversation parser, medical history generator, summary generator, and insight generator.
- Enforce strict-schema outputs and validation before accepting artifacts.
- Persist generated artifacts and update consultation processing status.
- Attach evidence references to every generated insight.
- Mark outputs as incomplete or pending review when confidence or support is insufficient.

### Out of Scope
- Real-time continuous AI generation during every audio chunk.
- Autonomous diagnoses, prescriptions, or treatment recommendations.
- Deep specialty-specific customization beyond the MVP scope.

## 4. Requirements

### Functional Requirements
- The pipeline must start only after consultation closure and transcript consolidation.
- The system must generate a draft structured medical history based only on information present in the consultation.
- The system must generate a faithful concise summary in clinical language.
- The system must generate only allowed insight categories: documentation gaps, consistency issues, and clinical attention flags based on explicit statements.
- Every insight must include supporting evidence excerpts.

### Non-Functional Requirements
- Output validation must reject malformed or schema-incompatible content.
- Workflow execution must support retries for transient failures and explicit failure states for non-recoverable problems.
- Prompts and schemas must remain maintainable and versioned.

### Business Rules
- Missing or unclear information must be marked as absent, unknown, or needing confirmation.
- The system must not fabricate symptoms, diagnoses, medications, allergies, findings, or plans.
- Clinical attention flags must never be presented as diagnoses.
- Follow-up items and patient instructions may only be drafted as reviewable content, never final medical direction.

### Technical Rules
- Use strict-schema processing only.
- Prompts and schemas are authored in English.
- Product-facing generated clinical content is returned in `pt-BR`.
- No free-form output should be trusted as final.

## 5. Implementation Notes

### Proposed Approach
Create one orchestration workflow that validates prerequisites, generates each artifact through explicit schema-constrained steps, writes validated outputs to S3, updates consultation status, and emits metrics for success, latency, and failure.

### AWS / Infrastructure Notes
- Use Step Functions Standard for orchestration and retries.
- Use queues or events only where they improve resilience without overcomplicating the MVP.

### Backend Notes
- Maintain versioned prompt and schema assets.
- Implement a clear artifact validation and error classification layer.

### Frontend Notes
- The frontend should receive output readiness and incompleteness state from the BFF rather than infer generation status from missing fields.

## 6. Deliverables

The task should produce:
- Step Functions processing workflow
- AI generation modules and schema validators
- Artifact persistence and status updates
- Evidence-linking logic for insights
- AI pipeline documentation

## 7. Acceptance Criteria

- [ ] The system generates a draft medical history, summary, and evidence-backed insights after transcript consolidation.
- [ ] All outputs are schema-validated before being accepted.
- [ ] Unsupported or uncertain content is surfaced as incomplete or needing review, not invented.
- [ ] Insight categories are limited to the approved MVP set.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for schema validation and evidence-linking logic
- Integration tests for Step Functions processing with mocked AI responses

### Manual Verification
Complete a consultation, allow the pipeline to run, and confirm the generated artifacts are stored, localized to `pt-BR`, evidence-backed, and aligned with the transcript.

## 9. Risks and Edge Cases

### Risks
- Weak schema enforcement could allow unusable or unsafe output into review flows.
- Prompt drift could reduce faithfulness or consistency.

### Edge Cases
- Transcript quality is too low for reliable artifact generation.
- One artifact succeeds while another fails.
- Evidence references point to a transcript region with limited timestamps.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
