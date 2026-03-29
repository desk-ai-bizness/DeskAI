# Backend Architecture

## Purpose

This document defines the internal architecture of the Python backend, including hexagonal layers, domain module boundaries, port and adapter definitions, and the BFF assembly layer.

---

## 1. Hexagonal Architecture Overview

The backend follows Hexagonal Architecture (ports and adapters). The core principle: business rules are independent from frameworks, AWS services, and delivery mechanisms.

```
┌───────────────────────────────────────────────────────────────────┐
│                     Inbound Adapters                              │
│   ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│   │ HTTP Handlers    │  │ WebSocket        │  │ Step Function │   │
│   │ (Lambda)         │  │ Handlers         │  │ Handlers      │   │
│   └────────┬────────┘  └────────┬─────────┘  └──────┬───────┘   │
│            │                    │                    │            │
│            ▼                    ▼                    ▼            │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                    BFF Layer                             │    │
│   │    View models · UI config assembly · Feature flags      │    │
│   └───────────────────────┬─────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                 Application Layer                        │    │
│   │         Use cases · orchestration · transactions         │    │
│   └───────────────────────┬─────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                   Domain Layer                           │    │
│   │      Entities · Value Objects · Domain Services           │    │
│   │      Domain Events · Business Rules · Exceptions          │    │
│   │      Port Interfaces (abstract)                           │    │
│   └───────────────────────┬─────────────────────────────────┘    │
│                           │ depends on ports                     │
│                           ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                 Outbound Adapters                         │    │
│   │   DynamoDB · S3 · Deepgram · Claude · Cognito · Events   │    │
│   └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
```

### Layer Rules

| Layer | May Depend On | Must Not Depend On |
|-------|---------------|-------------------|
| Domain | Nothing (pure Python, stdlib only) | Application, Adapters, Handlers, BFF, AWS SDK, frameworks |
| Application | Domain, Ports | Adapters, Handlers, BFF, AWS SDK |
| Ports | Domain (for type hints) | Adapters, Handlers, BFF, AWS SDK |
| Adapters | Domain, Ports, AWS SDK, external libs | Handlers, BFF |
| BFF | Domain, Application, Ports | Adapters (receives adapter results through application layer) |
| Handlers | Application, BFF, Domain (for types) | Direct adapter usage (goes through application layer) |

---

## 2. Domain Layer

The domain layer contains pure business logic with zero framework dependencies.

### Directory Structure

```
src/deskai/domain/
├── __init__.py
├── consultation/
│   ├── __init__.py
│   ├── entities.py                # Consultation entity, status enum
│   ├── value_objects.py           # ConsultationId, Specialty, PatientId, etc.
│   ├── services.py                # Consultation domain services
│   ├── events.py                  # Domain events (ConsultationCreated, etc.)
│   ├── rules.py                   # Business rule validators
│   └── exceptions.py              # Domain-specific exceptions
├── session/
│   ├── __init__.py
│   ├── entities.py                # Session entity, session state
│   ├── value_objects.py           # SessionId, AudioChunk, etc.
│   ├── services.py                # Session lifecycle rules
│   └── exceptions.py
├── transcription/
│   ├── __init__.py
│   ├── entities.py                # Transcript, TranscriptSegment
│   ├── value_objects.py           # NormalizedTranscript, SpeakerSegment
│   └── exceptions.py
├── ai_pipeline/
│   ├── __init__.py
│   ├── entities.py                # MedicalHistory, Summary, Insight
│   ├── value_objects.py           # EvidenceExcerpt, InsightCategory
│   └── exceptions.py
├── review/
│   ├── __init__.py
│   ├── entities.py                # ReviewState, PhysicianEdit
│   ├── services.py                # Review and finalization rules
│   └── exceptions.py
├── export/
│   ├── __init__.py
│   ├── entities.py                # ExportRequest, ExportArtifact
│   └── exceptions.py
├── auth/
│   ├── __init__.py
│   ├── entities.py                # Doctor, Clinic, PlanType
│   ├── value_objects.py           # DoctorId, ClinicId, PlanEntitlements
│   └── exceptions.py
├── audit/
│   ├── __init__.py
│   ├── entities.py                # AuditEvent, AuditAction
│   └── value_objects.py           # EventType, EventPayload
└── config/
    ├── __init__.py
    └── entities.py                # UIConfig, FeatureFlag
```

### Domain Module Responsibilities

| Module | Owns | Key Entities |
|--------|------|-------------|
| `consultation` | Consultation lifecycle, status transitions, creation rules | `Consultation`, `ConsultationStatus`, `ConsultationId` |
| `session` | Real-time audio session lifecycle, reconnection, grace period | `Session`, `SessionState`, `AudioChunk` |
| `transcription` | Transcript normalization model, provider-agnostic structures | `NormalizedTranscript`, `SpeakerSegment`, `TranscriptSegment` |
| `ai_pipeline` | AI artifact structures, evidence linking, insight categories | `MedicalHistory`, `Summary`, `Insight`, `EvidenceExcerpt` |
| `review` | Physician edit tracking, finalization guards, versioning | `ReviewState`, `PhysicianEdit`, `FinalizedRecord` |
| `export` | Export request model, export content assembly | `ExportRequest`, `ExportArtifact` |
| `auth` | Doctor and clinic identity, plan entitlements, access rules | `Doctor`, `Clinic`, `PlanType`, `PlanEntitlements` |
| `audit` | Audit event structure, event type catalog | `AuditEvent`, `AuditAction` |
| `config` | UI configuration model, feature flag model | `UIConfig`, `FeatureFlag` |

### Domain Design Rules

- Entities are mutable within their aggregate. Value objects are immutable.
- Domain services contain logic that doesn't belong to a single entity.
- Domain events describe state changes. They are data objects, not handlers.
- Business rule validators in `rules.py` return `Result` types (success or error), never raise exceptions for expected business violations.
- Domain exceptions are for programming errors and invariant violations, not business rule failures.
- No `import boto3`, no `import httpx`, no framework imports in the domain layer.

---

## 3. Port Interfaces

Ports are abstract interfaces that the domain and application layers depend on. Adapters implement them.

### Directory Structure

```
src/deskai/ports/
├── __init__.py
├── consultation_repository.py     # Consultation CRUD
├── session_repository.py          # Session state persistence
├── transcript_repository.py       # Transcript storage and retrieval
├── artifact_repository.py         # AI artifact storage
├── audit_repository.py            # Audit event persistence
├── patient_repository.py          # Patient CRUD
├── config_repository.py           # UI config and feature flag storage
├── transcription_provider.py      # External transcription service
├── llm_provider.py                # External LLM service
├── auth_provider.py               # Authentication verification
├── storage_provider.py            # Object storage (S3)
├── event_publisher.py             # Domain event publishing
└── export_generator.py            # Export document generation
```

### Port Categories

#### Repository Ports (Data Access)

```python
# Example: consultation_repository.py
from abc import ABC, abstractmethod
from deskai.domain.consultation.entities import Consultation
from deskai.domain.consultation.value_objects import ConsultationId

class ConsultationRepository(ABC):
    @abstractmethod
    def save(self, consultation: Consultation) -> None: ...

    @abstractmethod
    def find_by_id(self, consultation_id: ConsultationId) -> Consultation | None: ...

    @abstractmethod
    def find_by_doctor_and_date_range(
        self, doctor_id: str, start_date: str, end_date: str
    ) -> list[Consultation]: ...
```

#### Provider Ports (External Services)

```python
# Example: transcription_provider.py
from abc import ABC, abstractmethod

class TranscriptionProvider(ABC):
    @abstractmethod
    def start_realtime_session(self, session_id: str, language: str) -> dict: ...

    @abstractmethod
    def send_audio_chunk(self, session_id: str, audio_data: bytes) -> None: ...

    @abstractmethod
    def finish_realtime_session(self, session_id: str) -> dict: ...

    @abstractmethod
    def get_session_state(self, session_id: str) -> dict: ...

    @abstractmethod
    def fetch_final_transcript(self, session_id: str) -> dict: ...
```

```python
# Example: llm_provider.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_medical_history(self, transcript: str, schema: dict) -> dict: ...

    @abstractmethod
    def generate_summary(self, transcript: str, schema: dict) -> dict: ...

    @abstractmethod
    def generate_insights(self, transcript: str, medical_history: dict, schema: dict) -> dict: ...
```

#### Infrastructure Ports

```python
# Example: event_publisher.py
from abc import ABC, abstractmethod
from deskai.domain.audit.entities import AuditEvent

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: AuditEvent) -> None: ...
```

---

## 4. Application Layer

The application layer orchestrates domain logic and port interactions. Each use case is a single function or class.

### Directory Structure

```
src/deskai/application/
├── __init__.py
├── consultation/
│   ├── __init__.py
│   ├── create_consultation.py     # Create a new consultation
│   ├── get_consultation.py        # Retrieve consultation details
│   └── list_consultations.py      # List consultations for a doctor
├── session/
│   ├── __init__.py
│   ├── start_session.py           # Start real-time audio session
│   └── end_session.py             # End session, trigger processing
├── transcription/
│   ├── __init__.py
│   ├── process_transcript.py      # Consolidate and normalize transcript
│   └── store_transcript.py        # Persist transcript artifacts
├── ai_pipeline/
│   ├── __init__.py
│   ├── run_pipeline.py            # Orchestrate AI generation
│   └── store_artifacts.py         # Persist generated artifacts
├── review/
│   ├── __init__.py
│   ├── open_review.py             # Open review screen
│   ├── update_review.py           # Apply physician edits
│   └── finalize_consultation.py   # Lock and finalize
├── export/
│   ├── __init__.py
│   └── generate_export.py         # Generate PDF export
├── auth/
│   ├── __init__.py
│   ├── authenticate.py            # Verify identity and plan
│   └── check_entitlements.py      # Plan-based access check
└── config/
    ├── __init__.py
    └── get_ui_config.py           # Retrieve UI config for frontend
```

### Use Case Pattern

Each use case follows this pattern:

```python
class CreateConsultation:
    def __init__(
        self,
        consultation_repo: ConsultationRepository,
        patient_repo: PatientRepository,
        audit_repo: AuditRepository,
        event_publisher: EventPublisher,
    ):
        self._consultation_repo = consultation_repo
        self._patient_repo = patient_repo
        self._audit_repo = audit_repo
        self._event_publisher = event_publisher

    def execute(self, command: CreateConsultationCommand) -> Consultation:
        # 1. Validate business rules
        # 2. Create domain entity
        # 3. Persist through ports
        # 4. Publish domain events
        # 5. Return result
        ...
```

### Rules

- Use cases receive ports through constructor injection.
- Use cases work with domain objects, never raw AWS responses.
- Use cases are the transaction boundary. If multiple writes must succeed together, the use case coordinates them.
- Use cases must not import adapter code directly.

---

## 5. Adapter Layer

Adapters implement port interfaces using concrete infrastructure.

### Directory Structure

```
src/deskai/adapters/
├── __init__.py
├── persistence/
│   ├── __init__.py
│   ├── dynamodb_consultation_repository.py
│   ├── dynamodb_session_repository.py
│   ├── dynamodb_audit_repository.py
│   ├── dynamodb_patient_repository.py
│   ├── dynamodb_config_repository.py
│   └── dynamodb_client.py         # Shared DynamoDB client wrapper
├── storage/
│   ├── __init__.py
│   ├── s3_transcript_repository.py
│   ├── s3_artifact_repository.py
│   ├── s3_storage_provider.py
│   └── s3_client.py               # Shared S3 client wrapper
├── transcription/
│   ├── __init__.py
│   └── deepgram_provider.py       # Deepgram Nova-2 Medical adapter
├── llm/
│   ├── __init__.py
│   └── claude_provider.py         # Claude API (Anthropic) adapter
├── auth/
│   ├── __init__.py
│   └── cognito_provider.py        # Cognito token verification
├── events/
│   ├── __init__.py
│   └── eventbridge_publisher.py   # EventBridge event publishing
├── export/
│   ├── __init__.py
│   └── pdf_generator.py           # PDF export generator
└── secrets/
    ├── __init__.py
    └── secrets_manager.py         # AWS Secrets Manager client
```

### Adapter Design Rules

- Each adapter implements exactly one port interface.
- Adapters translate between domain types and infrastructure types (e.g., DynamoDB items ↔ domain entities).
- Adapters own serialization and deserialization logic for their specific infrastructure.
- Adapters handle retries for transient infrastructure failures (using `tenacity`).
- Adapters log infrastructure errors with structured context (using `aws-lambda-powertools`).
- Adapters must not contain business logic. If logic creeps in, it belongs in the domain or application layer.

### Provider Replaceability

The adapter pattern ensures providers are replaceable:

| Port | Current Adapter | Future Options |
|------|----------------|----------------|
| `TranscriptionProvider` | `DeepgramProvider` | Google Cloud STT, Azure AI Speech |
| `LLMProvider` | `ClaudeProvider` | OpenAI, local models |
| `ConsultationRepository` | `DynamoDBConsultationRepository` | PostgreSQL (if storage model changes) |
| `StorageProvider` | `S3StorageProvider` | GCS (if cloud changes) |

---

## 6. Handler Layer (Inbound Adapters)

Handlers are Lambda entry points that receive HTTP or WebSocket events.

### Directory Structure

```
src/deskai/handlers/
├── __init__.py
├── http/
│   ├── __init__.py
│   ├── auth_handler.py            # POST/DELETE /v1/auth/session
│   ├── me_handler.py              # GET /v1/me
│   ├── consultation_handler.py    # POST/GET /v1/consultations, GET /v1/consultations/{id}
│   ├── session_handler.py         # POST /v1/consultations/{id}/session/start|end
│   ├── review_handler.py          # GET/PUT /v1/consultations/{id}/review
│   ├── finalize_handler.py        # POST /v1/consultations/{id}/finalize
│   ├── export_handler.py          # POST /v1/consultations/{id}/export
│   ├── patient_handler.py         # POST/GET /v1/patients
│   ├── ui_config_handler.py       # GET /v1/ui-config
│   └── middleware.py              # Auth middleware, error handling, logging
├── websocket/
│   ├── __init__.py
│   ├── connect_handler.py         # $connect
│   ├── disconnect_handler.py      # $disconnect
│   ├── session_init_handler.py    # session.init
│   ├── audio_chunk_handler.py     # audio.chunk
│   ├── session_stop_handler.py    # session.stop
│   └── ping_handler.py            # client.ping
└── step_functions/
    ├── __init__.py
    ├── process_transcript_handler.py  # Transcript consolidation step
    ├── run_ai_pipeline_handler.py     # AI generation step
    └── finalize_processing_handler.py # Processing completion step
```

### Handler Responsibilities

- Parse the incoming event (HTTP request, WebSocket message, Step Functions input).
- Extract authentication context and validate authorization.
- Call the appropriate application use case.
- Pass the result through the BFF layer for response formatting.
- Return the formatted response.

### Handler Rules

- Handlers are thin. They parse input, call a use case, format output.
- Handlers must not contain business logic.
- Authentication verification happens in middleware, not in each handler.
- Error handling follows a consistent pattern: catch domain exceptions → map to HTTP status codes.
- Each handler file corresponds to one Lambda function (or a small router within one Lambda).

---

## 7. BFF Layer

The BFF layer shapes backend data into frontend-ready payloads.

### Directory Structure

```
src/deskai/bff/
├── __init__.py
├── views/
│   ├── __init__.py
│   ├── consultation_view.py       # Consultation list and detail views
│   ├── review_view.py             # Review screen payload
│   ├── user_view.py               # User profile and entitlements
│   └── export_view.py             # Export status view
├── ui_config/
│   ├── __init__.py
│   ├── assembler.py               # Assembles UI config from stored config
│   ├── labels.py                  # Label resolution (pt-BR)
│   └── screen_config.py           # Screen composition rules
├── feature_flags/
│   ├── __init__.py
│   ├── evaluator.py               # Evaluate flags for user context
│   └── flags.py                   # Flag definitions and defaults
└── response.py                    # Standard BFF response wrapper
```

### BFF Responsibilities

| Responsibility | Example |
|----------------|---------|
| Shape domain data into view models | `Consultation` → `ConsultationListItem` with display-ready fields |
| Inject UI configuration | Add labels, helper text, section ordering |
| Evaluate feature flags | Compute `can_create_consultation`, `consultations_remaining` |
| Aggregate multiple domain responses | Combine user profile + entitlements + active consultation into one payload |
| Localize display content | Return labels in `pt-BR` |
| Shield frontend from domain changes | Domain field renamed → BFF absorbs the change, frontend contract stays stable |

### BFF Rules

- The BFF never modifies domain state. It reads domain data and formats it.
- The BFF owns the frontend contract shape. Domain models and frontend view models are different types.
- The BFF evaluates feature flags and includes the result in responses.
- The BFF loads UI configuration from the config repository and includes it in responses.
- The frontend renders what the BFF tells it to render.

See `04-data-flow-and-configuration.md` for the full flow.

---

## 8. Shared Module

Cross-cutting utilities that any layer may use.

### Directory Structure

```
src/deskai/shared/
├── __init__.py
├── config.py                      # Environment config loading
├── errors.py                      # Base error types, error codes
├── logging.py                     # Structured logging setup
├── time.py                        # UTC time utilities
├── identifiers.py                 # UUID generation
└── types.py                       # Shared type aliases
```

### Rules

- The shared module contains only pure utilities with no business logic.
- It must not import from domain, application, adapters, handlers, or BFF.
- It may be imported by any layer.

---

## 9. Testing Structure

```
tests/
├── unit/
│   ├── domain/
│   │   ├── consultation/
│   │   │   ├── test_entities.py
│   │   │   ├── test_services.py
│   │   │   └── test_rules.py
│   │   ├── session/
│   │   ├── review/
│   │   └── ...
│   ├── application/
│   │   ├── consultation/
│   │   │   ├── test_create_consultation.py
│   │   │   └── ...
│   │   └── ...
│   └── bff/
│       ├── test_consultation_view.py
│       └── ...
├── integration/
│   ├── adapters/
│   │   ├── test_dynamodb_consultation_repository.py
│   │   ├── test_s3_artifact_repository.py
│   │   └── ...
│   └── handlers/
│       ├── test_consultation_handler.py
│       └── ...
└── conftest.py
```

### Testing Rules

- Domain tests are pure unit tests. No mocks needed (domain has no external dependencies).
- Application tests mock port interfaces using standard Python mocking.
- Adapter integration tests use localstack or test containers.
- Handler tests use Lambda event fixtures.
- BFF tests verify view model shape and feature flag evaluation.

---

## 10. Dependency Injection Strategy

For the MVP, use constructor injection with a simple factory module.

```
src/deskai/
└── container.py                   # Dependency wiring
```

`container.py` creates concrete adapter instances and wires them into use cases:

```python
# Example: container.py
def create_consultation_use_case() -> CreateConsultation:
    return CreateConsultation(
        consultation_repo=DynamoDBConsultationRepository(table_name=get_table_name()),
        patient_repo=DynamoDBPatientRepository(table_name=get_table_name()),
        audit_repo=DynamoDBAuditRepository(table_name=get_table_name()),
        event_publisher=EventBridgePublisher(bus_name=get_bus_name()),
    )
```

### Rules

- No DI framework in the MVP. Simple factory functions are sufficient.
- Handlers call factory functions from `container.py` to get wired use cases.
- Tests can create use cases with mock ports directly, bypassing the container.
- If the project grows beyond what factory functions can manage cleanly, consider a lightweight DI library.
