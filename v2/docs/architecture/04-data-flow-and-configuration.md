# Data Flow and Configuration

## Purpose

This document explains how backend-driven UI configuration and feature flags flow from storage through the BFF to the frontend. It also covers the primary data flows for the consultation lifecycle.

---

## 1. UI Configuration Flow

### Storage → BFF → Frontend

```
┌──────────────────────────────────┐
│        DynamoDB / S3             │
│  (UI config, labels, flags)      │
└───────────────┬──────────────────┘
                │ read
                ▼
┌──────────────────────────────────┐
│       Config Repository          │
│     (adapter, implements port)   │
└───────────────┬──────────────────┘
                │ domain objects
                ▼
┌──────────────────────────────────┐
│         BFF UI Config            │
│        Assembler                 │
│  - resolves labels for locale    │
│  - evaluates feature flags       │
│  - assembles screen config       │
│  - applies plan-based overrides  │
└───────────────┬──────────────────┘
                │ UIConfigView
                ▼
┌──────────────────────────────────┐
│       HTTP Response              │
│    GET /v1/ui-config             │
│    (or embedded in other         │
│     BFF responses)               │
└───────────────┬──────────────────┘
                │ JSON
                ▼
┌──────────────────────────────────┐
│        Frontend App              │
│  - reads config                  │
│  - renders labels                │
│  - shows/hides sections          │
│  - respects feature flags        │
│  - never computes business logic │
└──────────────────────────────────┘
```

### How It Works

1. **On app load**, the frontend calls `GET /v1/ui-config` to fetch the full UI configuration.
2. **On each BFF response**, the BFF may embed relevant UI config inline (e.g., review screen config is embedded in the `GET /v1/consultations/{id}/review` response).
3. **The frontend stores the config in local state** (React context or similar) and uses it to render labels, section ordering, visibility, and feature availability.
4. **The frontend never hardcodes** labels, section ordering, insight categories, or feature availability. If the config is missing, it shows a minimal fallback (error state or loading state), not hardcoded business content.

### What the Frontend Does with Config

| Config Item | Frontend Behavior |
|-------------|------------------|
| `labels.*` | Displays the label text as-is in `pt-BR` |
| `review_screen.section_order` | Renders review sections in the specified order |
| `review_screen.sections.*.visible` | Shows or hides the section |
| `review_screen.sections.*.editable` | Enables or disables editing for the section |
| `insight_categories.*` | Renders insight badges with the correct label and icon |
| `status_labels.*` | Displays consultation status with the correct `pt-BR` label |
| `feature_flags.*` | Shows or hides features based on flag values |

### Config Update Strategy

- For the MVP, UI config is updated by modifying DynamoDB items directly or through a backend admin endpoint (post-MVP).
- Config changes take effect on the next frontend request. There is no real-time push of config updates.
- Config is versioned. The frontend includes the config version in requests so the BFF can detect stale clients.

---

## 2. Feature Flag Flow

### Evaluation Flow

```
┌──────────────────────────────────┐
│     Frontend Request             │
│  (includes auth token)           │
└───────────────┬──────────────────┘
                │
                ▼
┌──────────────────────────────────┐
│     Handler (Lambda)             │
│  - extracts user context         │
│  - calls application use case    │
└───────────────┬──────────────────┘
                │
                ▼
┌──────────────────────────────────┐
│     BFF Feature Flag Evaluator   │
│  1. Load flag definitions        │
│  2. Get user plan_type           │
│  3. Resolve flag values:         │
│     - check plan-level override  │
│     - fall back to default       │
│  4. Compute derived flags:       │
│     - consultations_remaining    │
│     - trial_expired              │
└───────────────┬──────────────────┘
                │ evaluated flags
                ▼
┌──────────────────────────────────┐
│     BFF Response                 │
│  (includes entitlements object)  │
└──────────────────────────────────┘
```

### Flag Resolution Rules

1. **Global flags** have a single value for all users (e.g., `export.pdf.enabled`).
2. **Plan-scoped flags** have a default value and optional per-plan overrides (e.g., `consultation.monthly_limit`).
3. **Computed flags** are derived from stored data and user context at evaluation time (e.g., `trial_expired` is computed from `created_at + trial.duration_days`).

### Where Flags Are Enforced

| Enforcement Point | What Happens |
|-------------------|-------------|
| **BFF response** | Frontend receives evaluated flags in the response. Hides/shows UI elements accordingly. |
| **Application use case** | Use case checks plan entitlements before executing business operations (e.g., consultation creation checks `monthly_limit`). |
| **Handler middleware** | HTTP handlers check plan authorization before calling use cases. Returns 403 with specific error code if denied. |

### What the Frontend Must Not Do with Flags

- Must not evaluate plan-based limits.
- Must not compute `consultations_remaining` or `trial_expired`.
- Must not decide which features are available based on local logic.
- Must only render based on the `entitlements` and `feature_flags` objects received from the BFF.

---

## 3. Consultation Lifecycle Data Flow

### End-to-End Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            CONSULTATION LIFECYCLE                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐   POST /v1/consultations    ┌──────────┐                   │
│  │ Frontend ├───────────────────────────► │ Handler  │                   │
│  └─────────┘                             └────┬─────┘                   │
│                                               │                         │
│                                               ▼                         │
│                                    ┌─────────────────────┐              │
│                                    │ CreateConsultation   │              │
│                                    │ (use case)           │              │
│                                    └──────────┬──────────┘              │
│                                               │                         │
│                          ┌────────────────────┼──────────────────┐      │
│                          ▼                    ▼                  ▼      │
│                  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│                  │ DynamoDB     │  │ AuditRepo    │  │ EventBridge  │  │
│                  │ (metadata)   │  │ (audit event)│  │ (domain evt) │  │
│                  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                         │
│  Status: started                                                        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐   POST .../session/start    ┌──────────┐                  │
│  │ Frontend ├──────────────────────────► │ Handler  │                  │
│  └────┬────┘                             └────┬─────┘                  │
│       │                                       │                         │
│       │ Opens WebSocket                       ▼                         │
│       │                           ┌─────────────────────┐              │
│       │                           │ StartSession         │              │
│       │                           │ (use case)           │              │
│       │                           └──────────┬──────────┘              │
│       │                                      │                         │
│       │                                      ▼                         │
│       │                           ┌──────────────────────┐             │
│       │                           │ TranscriptionProvider │             │
│       │                           │ .start_realtime_      │             │
│       │                           │  session()            │             │
│       │                           └──────────────────────┘             │
│       │                                                                │
│  Status: recording                                                     │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────┐   audio.chunk (WS)     ┌──────────────┐                  │
│  │ Frontend ├──────────────────────► │ WS Handler   │                  │
│  └────┬────┘                         └──────┬───────┘                  │
│       │                                     │                          │
│       │                                     ▼                          │
│       │                          ┌──────────────────────┐              │
│       │                          │ TranscriptionProvider │              │
│       │                          │ .send_audio_chunk()   │              │
│       │                          └──────────┬───────────┘              │
│       │                                     │ partial result           │
│       │ ◄───── transcript.partial ──────────┘                          │
│       │       (WS, server → client)                                    │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────┐   POST .../session/end    ┌──────────┐                   │
│  │ Frontend ├─────────────────────────► │ Handler  │                   │
│  └─────────┘                           └────┬─────┘                   │
│                                              │                         │
│                                              ▼                         │
│                                  ┌─────────────────────┐              │
│                                  │ EndSession           │              │
│                                  │ (use case)           │              │
│                                  └──────────┬──────────┘              │
│                                             │                         │
│                              ┌──────────────┼──────────────┐          │
│                              ▼              ▼              ▼          │
│                      ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│                      │ WS Close   │ │ Final      │ │ Step         │  │
│                      │            │ │ Transcript │ │ Functions    │  │
│                      └────────────┘ │ → S3       │ │ (trigger)    │  │
│                                     └────────────┘ └──────┬───────┘  │
│                                                           │          │
│  Status: in_processing                                    │          │
│                                                           │          │
├───────────────────────────────────────────────────────────┤──────────┤
│                    STEP FUNCTIONS WORKFLOW                 │          │
│                                                           ▼          │
│                                              ┌─────────────────────┐ │
│                                              │ 1. Consolidate      │ │
│                                              │    transcript       │ │
│                                              └──────────┬──────────┘ │
│                                                         │            │
│                                                         ▼            │
│                                              ┌─────────────────────┐ │
│                                              │ 2. Normalize        │ │
│                                              │    → S3             │ │
│                                              └──────────┬──────────┘ │
│                                                         │            │
│                                                         ▼            │
│                                              ┌─────────────────────┐ │
│                                              │ 3. AI Pipeline      │ │
│                                              │    (Claude API)     │ │
│                                              │    → medical_history│ │
│                                              │    → summary        │ │
│                                              │    → insights       │ │
│                                              └──────────┬──────────┘ │
│                                                         │            │
│                                                         ▼            │
│                                              ┌─────────────────────┐ │
│                                              │ 4. Store artifacts  │ │
│                                              │    → S3 + DynamoDB  │ │
│                                              └──────────┬──────────┘ │
│                                                         │            │
│                                    success ─────────────┤            │
│                                                         │            │
│  Status: draft_generated                     failure ───┤            │
│                                                         │            │
│                                              Status: processing_failed│
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────┐  GET .../review         ┌──────────┐                   │
│  │ Frontend ├───────────────────────► │ Handler  │                   │
│  └────┬────┘                         └────┬─────┘                   │
│       │                                   │                          │
│       │                                   ▼                          │
│       │                        ┌─────────────────────┐               │
│       │                        │ OpenReview           │               │
│       │                        │ (use case)           │               │
│       │                        └──────────┬──────────┘               │
│       │                                   │                          │
│       │                          ┌────────┼────────┐                 │
│       │                          ▼        ▼        ▼                 │
│       │                   ┌─────────┐ ┌──────┐ ┌────────┐           │
│       │                   │ DynamoDB│ │  S3  │ │ Audit  │           │
│       │                   │ (meta)  │ │(arts)│ │ (event)│           │
│       │                   └────┬────┘ └──┬───┘ └────────┘           │
│       │                        │         │                           │
│       │                        ▼         ▼                           │
│       │                  ┌────────────────────┐                      │
│       │                  │ BFF ReviewView     │                      │
│       │                  │ + UI config        │                      │
│       │                  │ + feature flags    │                      │
│       │ ◄────────────────┤ + labels           │                      │
│       │                  └────────────────────┘                      │
│                                                                      │
│  Status: under_physician_review                                      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────┐  POST .../finalize      ┌──────────┐                   │
│  │ Frontend ├───────────────────────► │ Handler  │                   │
│  └─────────┘                         └────┬─────┘                   │
│                                           │                          │
│                                           ▼                          │
│                                ┌─────────────────────┐               │
│                                │ Finalize             │               │
│                                │ (use case)           │               │
│                                └──────────┬──────────┘               │
│                                           │                          │
│                          ┌────────────────┼──────────────────┐       │
│                          ▼                ▼                  ▼       │
│                  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│                  │ Lock record  │ │ Store final  │ │ Audit event  │ │
│                  │ (DynamoDB)   │ │ version (S3) │ │              │ │
│                  └──────────────┘ └──────────────┘ └──────────────┘ │
│                                                                      │
│  Status: finalized (terminal, immutable)                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Ownership by Storage

### DynamoDB Owns

| Entity Pattern | PK | SK | What It Stores |
|---------------|----|----|---------------|
| Clinic metadata | `CLINIC#<clinic_id>` | `METADATA` | Clinic name, config, retention policy |
| Consultation metadata | `CLINIC#<clinic_id>` | `CONSULTATION#<consultation_id>` | Status, timestamps, patient/doctor IDs, specialty |
| Artifact pointer | `CONSULTATION#<consultation_id>` | `ARTIFACT#<artifact_type>` | S3 key, artifact version, completeness flag |
| Audit event | `CONSULTATION#<consultation_id>` | `AUDIT#<timestamp>` | Event type, actor, payload |
| Doctor access | `DOCTOR#<doctor_id>` | `CONSULTATION#<date>#<consultation_id>` | Consultation reference for doctor listing |
| Patient | `CLINIC#<clinic_id>` | `PATIENT#<patient_id>` | Patient name, date of birth |
| UI config | `CONFIG#<scope>` | `VERSION#<version>` | Labels, section order, flag definitions |
| Feature flags | `CONFIG#feature_flags` | `VERSION#current` | Flag values and plan overrides |

### S3 Owns

| Artifact | S3 Key Pattern | Format |
|----------|---------------|--------|
| Raw audio | `clinics/<cid>/consultations/<id>/audio/raw.<ext>` | Audio binary |
| Raw transcript | `clinics/<cid>/consultations/<id>/transcripts/raw.json` | Provider JSON |
| Normalized transcript | `clinics/<cid>/consultations/<id>/transcripts/normalized.json` | Internal JSON |
| Medical history | `clinics/<cid>/consultations/<id>/ai/medical_history.json` | Structured JSON |
| Summary | `clinics/<cid>/consultations/<id>/ai/summary.json` | Text JSON |
| Insights | `clinics/<cid>/consultations/<id>/ai/insights.json` | Structured JSON |
| Physician edits | `clinics/<cid>/consultations/<id>/review/edits.json` | Edit history JSON |
| Final version | `clinics/<cid>/consultations/<id>/review/final.json` | Finalized JSON |
| Export PDF | `clinics/<cid>/consultations/<id>/exports/final.pdf` | PDF binary |

---

## 5. Request Authentication Flow

Every authenticated request follows this flow:

```
1. Frontend includes Cognito access token in Authorization header
2. API Gateway validates token with Cognito authorizer
3. Handler extracts user claims (doctor_id, email, clinic_id)
4. Handler passes authenticated context to application use case
5. Use case validates ownership (e.g., consultation belongs to this doctor)
6. Use case checks plan entitlements when relevant
7. Use case executes business logic
8. BFF formats response with user-specific config and flags
```

### Auth Context Object

The authenticated context passed through the system:

```python
@dataclass(frozen=True)
class AuthContext:
    doctor_id: str
    email: str
    clinic_id: str
    plan_type: PlanType
```

This is created by handler middleware from the Cognito token claims and passed to every use case that needs authorization.

---

## 6. Event Flow

Domain events flow through EventBridge for decoupled processing.

```
Domain Event (use case)
        │
        ▼
EventBridge Publisher (adapter)
        │
        ▼
EventBridge Bus (deskai-{env}-events)
        │
        ├──► SQS Queue ──► Lambda (async processing)
        ├──► CloudWatch (metrics)
        └──► SNS (operational alerts)
```

### Event Catalog

| Event | Source | Consumers |
|-------|--------|-----------|
| `consultation.created` | CreateConsultation use case | Metrics, audit |
| `session.started` | StartSession use case | Metrics |
| `session.ended` | EndSession use case | Step Functions trigger |
| `processing.completed` | AI pipeline step | Notification, metrics |
| `processing.failed` | AI pipeline step | Alert, dead-letter queue |
| `consultation.finalized` | Finalize use case | Metrics, audit |
| `export.generated` | Export use case | Metrics |

---

## 7. CDK Stack Dependencies

```
┌───────────────────┐
│ security_stack     │   KMS keys, Secrets Manager
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ auth_stack         │   Cognito User Pool
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ storage_stack      │   DynamoDB tables, S3 buckets
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ compute_stack      │   Lambda functions
└────────┬──────────┘
         │
         ▼
┌───────────────────┐  ┌───────────────────┐
│ api_stack          │  │ orchestration_stack│
│ HTTP + WebSocket   │  │ Step Functions     │
│ API Gateway        │  │ EventBridge, SQS   │
└────────┬──────────┘  └────────┬──────────┘
         │                      │
         ▼                      ▼
┌───────────────────┐  ┌───────────────────┐
│ cdn_stack          │  │ monitoring_stack   │
│ CloudFront         │  │ CloudWatch         │
└───────────────────┘  └───────────────────┘
                       ┌───────────────────┐
                       │ budget_stack       │
                       │ AWS Budgets + SNS  │
                       └───────────────────┘
```

### Stack Parameterization

Every stack accepts:
- `environment`: `dev` or `prod`
- `project_name`: `deskai` (used in resource naming)

Resources are named: `{project_name}-{environment}-{resource_purpose}`
