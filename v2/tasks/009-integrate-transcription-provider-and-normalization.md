# Task 009: Integrate Transcription Provider And Normalization

## 1. Overview

### Objective
Implement the transcription provider abstraction, first production-ready provider integration, partial/final transcript handling, and normalized transcript artifact generation.

### Why This Matters
Transcription is a required MVP output and the input for every later AI artifact. The system needs a provider integration that supports Brazilian Portuguese and produces normalized, reusable transcript data.

### Task Type
- Backend

### Priority
- Critical

## 2. Context

### Product Context
For every processed consultation, the MVP must produce a faithful transcript in `pt-BR`. The transcript is the source material for structured history, summary, insights, and evidence references.

### Technical Context
The provider must sit behind an internal adapter interface and all provider output must be normalized before AI generation or review consumption.

### Related Systems
- Backend API
- Storage
- Observability

### Dependencies
- `008-implement-realtime-consultation-session-transport.md`

## 3. Scope

### In Scope
- Select and implement the first transcription provider adapter from the approved candidate set.
- Implement the internal provider contract for session start, audio chunk send, session finish, state lookup, and final transcript fetch.
- Normalize partial and final transcript data into the internal transcript model.
- Persist raw provider responses and normalized transcript artifacts.
- Handle provider errors, retries, and incomplete transcript cases.

### Out of Scope
- Multi-provider failover.
- Batch upload workflow as a primary path.
- Advanced diarization enhancements beyond what the MVP requires.

## 4. Requirements

### Functional Requirements
- The production transcription path must support Brazilian Portuguese (`pt-BR`).
- Partial transcript updates must be available during the session where supported.
- Final transcript output must be normalized and stored before AI generation starts.
- If transcript generation is incomplete or unreliable, the consultation must be marked accordingly instead of inventing content.

### Non-Functional Requirements
- Provider-specific details must remain behind an adapter boundary.
- Failures must be logged with structured context and retried only when transient.
- The normalized transcript contract must be stable for downstream consumers.

### Business Rules
- English-only medical transcription providers must not be used for production consultation transcription in Brazil.
- The transcript must remain faithful to the consultation and cannot introduce facts.
- Source conversation content must stay distinct from generated summaries and insights.

### Technical Rules
- Implement the provider interface defined in the technical specs.
- Normalize provider responses into the required internal transcript structure.
- Store large artifacts in S3 and metadata in DynamoDB.

## 5. Implementation Notes

### Proposed Approach
Create a provider adapter module and a transcript normalizer module. Keep provider response storage separate from normalized artifact storage so diagnosis and debugging do not depend on raw external formats.

### AWS / Infrastructure Notes
- Use Secrets Manager for provider credentials.
- Ensure provider integration failures feed metrics and alerts.

### Backend Notes
- Normalize timestamps, speaker segments, confidence metadata, and transcript text where available.
- Mark transcript completeness and reliability state explicitly for downstream tasks.

### Frontend Notes
- Transcript event payloads delivered to the UI should come from normalized internal structures, not raw provider messages.

## 6. Deliverables

The task should produce:
- Provider adapter implementation
- Transcript normalization pipeline
- Artifact persistence for raw and normalized transcripts
- Error handling and retry logic
- Provider integration documentation

## 7. Acceptance Criteria

- [ ] A supported `pt-BR` transcription provider is integrated through the internal adapter interface.
- [ ] Partial and final transcript data are normalized into the internal transcript model.
- [ ] Raw and normalized transcript artifacts are stored and traceable to the consultation.
- [ ] Failed or incomplete transcript generation is surfaced without fabricated content.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Unit tests for normalization logic
- Integration tests for provider adapter behavior with mocked provider responses

### Manual Verification
Run a consultation through the real-time flow, observe transcript updates, and confirm the final normalized transcript artifact and completeness flags are stored correctly.

## 9. Risks and Edge Cases

### Risks
- Provider behavior may differ from local assumptions around timestamps or speaker segmentation.
- Poor normalization could make downstream evidence linking unreliable.

### Edge Cases
- The provider returns transcript text without speaker segmentation.
- Confidence metadata is missing.
- The provider session finishes successfully but final transcript fetch is delayed.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
