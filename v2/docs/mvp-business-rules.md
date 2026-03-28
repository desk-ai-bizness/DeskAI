# MVP Business Rules

## 1. MVP Purpose

The MVP exists to support physicians during consultation documentation by:

- producing a transcript of the consultation
- generating a draft structured medical history
- generating a consultation summary
- highlighting reviewable documentation, consistency, and clinical attention flags

The MVP is a documentation support tool. It is not a clinical decision-maker.

## 2. Target User and Initial Scope

- The initial target user is a physician.
- The MVP operates in Brazil.
- The MVP is limited to general practice/generalist consultations.
- Each consultation belongs to one physician, one patient, and one clinic context.
- The MVP supports one specialty per consultation.

## 3. Language Rules

- The frontend must be presented in Brazilian Portuguese (`pt-BR`).
- Consultation transcripts must be generated in Brazilian Portuguese (`pt-BR`).
- Patient-facing and physician-facing product content inside the app must default to Brazilian Portuguese (`pt-BR`).
- Code, code comments, and project documentation must be written in English.

## 4. Authentication Rules

- Users must log in with email and password.
- The MVP must not offer Google login.
- The MVP must not offer Facebook login.
- The MVP must not offer social login or SSO alternatives.

## 5. Plan And Access Rules

- Each doctor client must belong to one plan type.
- The available MVP plan types are:
  - `free_trial`
  - `plus`
  - `pro`
- Access rules and product permissions may vary by plan type.
- The system must always know which plan type is assigned to each doctor client.
- Plan-based access control is part of the MVP business model and must be enforced consistently.

## 6. Allowed MVP Inputs

- The MVP accepts consultation audio captured during the consultation.
- The consultation must be processed as a single encounter tied to a specific patient and physician.
- The system may use consultation metadata such as date, time, specialty, patient identifier, and physician identifier.

## 7. Required MVP Outputs

For every successfully processed consultation, the MVP must produce:

- a raw transcript
- a draft structured medical history
- a consultation summary
- a list of flagged insights for review
- evidence excerpts linking each flagged insight to the related consultation dialogue

If any output cannot be produced reliably, the system must mark the item as incomplete or pending review instead of inventing content.

## 8. Structured Medical History Rules

The structured medical history is a draft prepared for physician review.

Business rules:

- The medical history must reflect only information present in the consultation.
- Missing or unclear information must be marked as absent, unknown, or needing confirmation.
- The system must separate confirmed facts from uncertain or incomplete information.
- The system must preserve clinically relevant negatives only when they were explicitly stated.
- The system must not fabricate symptoms, diagnoses, medications, allergies, findings, or plans.
- The system may identify missing information that would normally be expected in documentation.

## 9. Summary Rules

- The summary must represent the consultation in concise clinical language.
- The summary must stay faithful to the transcript and draft medical history.
- The summary must not introduce new facts not supported by the consultation.
- Follow-up items and patient instructions may be drafted only as reviewable content, never as final medical direction without physician confirmation.

## 10. Insight Rules

Insights are review flags, not conclusions.

The MVP may generate only these insight categories:

- documentation gaps
- consistency issues
- clinical attention flags based on explicit statements in the consultation

Business rules for insights:

- Every insight must include supporting evidence from the consultation.
- Every insight must be reviewable by the physician before being accepted.
- Insights must be phrased as observations, missing information, or inconsistencies.
- Clinical attention flags must never be presented as diagnoses.
- The system must not recommend treatment, prescribe medication, or make autonomous clinical decisions.

## 11. Physician Review and Approval Rules

- No AI-generated output is final until reviewed by the physician.
- The physician must be able to edit the draft medical history, summary, and insights.
- The final consultation record must require explicit physician confirmation.
- The system must clearly indicate that all AI-generated content is subject to medical review.
- The final signed or confirmed version is the only version considered complete for business purposes.

## 12. MVP Boundaries and Exclusions

The MVP must not:

- generate automatic diagnoses
- generate automatic prescriptions
- act without physician review
- support multi-specialty handling within the same consultation
- deeply integrate with external medical record systems as part of the MVP
- present clinical suggestions as authoritative decisions

The MVP is limited to documentation assistance and review support.

## 13. Transcription Provider Rules

- The MVP must use a transcription provider that supports Brazilian Portuguese (`pt-BR`).
- English-only medical transcription services must not be used in the MVP for production consultation transcription in Brazil.
- Candidate transcription providers for the MVP include Google Cloud Speech-to-Text, Azure AI Speech, and Deepgram, provided they meet product, privacy, and performance requirements.

## 14. Evidence and Traceability Rules

- Flagged insights must be traceable to specific excerpts from the consultation.
- The system must preserve a clear distinction between source conversation content and generated summaries.
- Edits and final approval actions must remain attributable to the responsible human user.

## 15. Privacy and Retention Rules

- Consultation data must be handled as sensitive health information.
- Access to consultation data must be limited to authorized users within the correct clinic context.
- The product must support retaining or deleting audio according to clinic policy.
- The clinic may retain the final reviewed note even if audio is deleted.
- Logs and operational records must avoid unnecessary exposure of patient-identifiable information.

## 16. Consultation Status Rules

A consultation may move through these business states:

- started
- in processing
- draft generated
- under physician review
- finalized

Business rules:

- A consultation cannot be finalized before physician review.
- A finalized consultation must have a responsible physician associated with it.
- If processing fails or remains incomplete, the consultation must not be treated as finalized.

## 17. MVP Success Criteria

The MVP should be evaluated primarily on:

- time saved in consultation documentation
- reliability of transcript and draft note generation
- ease and speed of physician review
- percentage of usable draft content
- frequency of necessary physician corrections
- usefulness and trustworthiness of review flags

For MVP success, the priority is reliability and reviewability over automation depth.
