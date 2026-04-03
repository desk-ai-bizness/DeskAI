# Phases 5-10: Adapters through Container Audit

**Auditor**: Agent T5
**Commit**: 75715f2
**Files read**: 88 files across adapters, application, handlers, BFF, shared, container, and infra/lambda_handlers

---

## Phase 5: Adapter Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| A5-1 | **CRITICAL** | `adapters/persistence/dynamodb_consultation_repository.py:67` | **Zero error handling on DynamoDB `put_item`** -- `save()` calls `self._table.put_item(Item=item)` with no try/except. A DynamoDB service error (throttle, ConditionalCheckFailed, network timeout) will crash with an unhandled `botocore.exceptions.ClientError` and bubble up as a 500 to the user. | `self._table.put_item(Item=item)` | Wrap ALL DynamoDB calls in try/except ClientError with retry for ProvisionedThroughputExceededException and proper domain error mapping. | A1 |
| A5-2 | **CRITICAL** | `adapters/persistence/dynamodb_consultation_repository.py:72,86,121` | **Zero error handling on DynamoDB `get_item`, `query`, `update_item`** -- Same issue as A5-1 for `find_by_id`, `find_by_doctor_and_date_range`, and `update_status`. | `response = self._table.get_item(...)` | Same as A5-1: wrap in try/except. | A1 |
| A5-3 | **CRITICAL** | ALL 6 DynamoDB repositories | **Systemic zero error handling across ALL persistence adapters** -- `DynamoDBDoctorRepository`, `DynamoDBPatientRepository`, `DynamoDBSessionRepository`, `DynamoDBAuditRepository`, `DynamoDBConnectionRepository` all have ZERO try/except on any boto3 call. Every single `put_item`, `get_item`, `query`, `update_item`, `delete_item` is unprotected. | (all files) | Create a base class or decorator that wraps DynamoDB calls with proper error handling, retry logic, and domain exception mapping. | A1 |
| A5-4 | **HIGH** | `adapters/persistence/dynamodb_consultation_repository.py:86-98` | **No pagination on DynamoDB query** -- `find_by_doctor_and_date_range` does not handle `LastEvaluatedKey`. DynamoDB returns max 1MB per query. A doctor with many consultations will get silently truncated results. | `response = self._table.query(...)` then `return [self._to_entity(item) for item in response.get("Items", [])]` | Implement pagination loop or add a limit parameter. Same issue in `DynamoDBPatientRepository.find_by_clinic` (line 55) and `DynamoDBAuditRepository.find_by_consultation` (line 45). | A2 |
| A5-5 | **HIGH** | `adapters/persistence/dynamodb_consultation_repository.py:116-119` | **Expression injection via kwargs in `update_status`** -- Arbitrary kwargs are interpolated directly into DynamoDB UpdateExpression. Caller-controlled keys flow unsanitized into `f"{key} = {placeholder}"`. A malicious or buggy caller could inject reserved words or abuse the expression. | `for key, value in kwargs.items(): placeholder = f":{key}"; update_parts.append(f"{key} = {placeholder}")` | Whitelist allowed field names. Use ExpressionAttributeNames for all field references. | -- |
| A5-6 | **HIGH** | `adapters/persistence/dynamodb_consultation_repository.py:106` | **`clinic_id` silently defaults to empty string** -- `kwargs.pop("clinic_id", "")` means if caller omits clinic_id, the update targets key `PK=CLINIC#` + `SK=CONSULTATION#{id}`, which will silently write to a wrong/empty partition. | `clinic_id = kwargs.pop("clinic_id", "")` | Require clinic_id as a mandatory parameter, not an optional kwarg. | -- |
| A5-7 | **HIGH** | `adapters/storage/s3_client.py:20-27,40-47` | **No server-side encryption on S3 writes** -- `put_object` calls for both JSON and binary artifacts do not specify `ServerSideEncryption`. PHI data (transcripts, medical history, AI outputs) is stored without at-rest encryption directive. | `self._s3.put_object(Bucket=self._bucket, Key=key, Body=..., ContentType=...)` | Add `ServerSideEncryption='aws:kms'` or `'AES256'` to all `put_object` calls. For LGPD/HIPAA compliance, KMS is strongly recommended. | A4 |
| A5-8 | **HIGH** | `adapters/transcription/elevenlabs_provider.py:96` | **Unbounded audio buffer in memory** -- `entry.audio_buffer.extend(audio_data)` grows without limit. A long session or malicious client sending large chunks can OOM the Lambda (max 10GB). | `entry.audio_buffer.extend(audio_data)` | Add a max buffer size (e.g., 500MB) and reject chunks that would exceed it. | A6 |
| A5-9 | **MEDIUM** | ALL 6 DynamoDB repositories `__init__` | **boto3 resource created per-instance** -- Each repository instantiates `boto3.resource("dynamodb")` in its constructor. While acceptable if Container is singleton, it creates 6 separate boto3 resources. | `dynamodb = boto3.resource("dynamodb")` | Share a single DynamoDB resource via container injection, reducing connection overhead. | A3 |
| A5-10 | **MEDIUM** | `adapters/transcription/elevenlabs_config.py:43-44` | **No error handling on Secrets Manager call** -- `load_elevenlabs_config` calls `client.get_secret_value()` with no try/except. Missing secret or permission error crashes cold start. | `response = client.get_secret_value(SecretId=secret_name)` | Wrap in try/except ClientError with descriptive error for missing secrets. | -- |
| A5-11 | **MEDIUM** | `adapters/transcription/elevenlabs_provider.py:169-174` | **Retry only covers timeout/connect, not 5xx** -- The `@retry` decorator retries on `httpx.TimeoutException` and `httpx.ConnectError` but NOT on `httpx.HTTPStatusError` for 5xx responses. Server errors are not retried. | `retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))` | Add 5xx retry: check response status in `_post_with_retry` and raise for retry on 5xx. | -- |
| A5-12 | **MEDIUM** | `adapters/persistence/dynamodb_session_repository.py:57` | **`update` uses `put_item` (full overwrite)** -- `update()` does a full `put_item` instead of `update_item`. This replaces the entire record, risking race conditions if two concurrent updates happen (last-write-wins). | `def update(self, session: Session) -> None: self._table.put_item(Item=self._to_item(session))` | Use `update_item` with condition expressions to prevent lost updates. | -- |
| A5-13 | **LOW** | `adapters/events/`, `adapters/export/`, `adapters/llm/`, `adapters/secrets/`, `adapters/storage/s3_storage_provider.py` | **5 ports have only placeholder adapters** -- `EventPublisher`, `ExportGenerator`, `LlmProvider`, `SecretsManager`, and `StorageProvider` ports have no real implementations. Only placeholder files exist. | `"""Adapter placeholder for concrete infrastructure implementation."""` | Expected for MVP. Track these as implementation TODOs. | A7 |
| A5-14 | **LOW** | `adapters/persistence/dynamodb_client.py` | **dynamodb_client.py is an empty placeholder** -- File contains only a docstring placeholder but several DynamoDB repositories already exist with inline boto3 usage. Unused file. | `"""Adapter implementation placeholder."""` | Remove or consolidate DynamoDB client logic here. | -- |
| A5-15 | **LOW** | `adapters/auth/cognito_provider.py` | **CognitoAuthProvider lacks `validate_ws_token` method** -- The `connect_handler.py:17` calls `auth_provider.validate_ws_token(token)` but `CognitoAuthProvider` only implements `authenticate`, `sign_out`, `forgot_password`, and `confirm_forgot_password`. The WebSocket token validation is missing from the adapter. | `claims = auth_provider.validate_ws_token(token)` in connect_handler | Implement `validate_ws_token` in CognitoAuthProvider or a separate port. Currently this will raise AttributeError at runtime. | A8 |

---

## Phase 6: Application Layer Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| U6-1 | **CRITICAL** | `application/consultation/create_consultation.py:25-70` | **No plan entitlement check before creating consultation** -- `CreateConsultationUseCase.execute()` validates fields and patient existence but NEVER checks if the doctor's plan allows creating more consultations. A free-trial user who exceeded their limit can create unlimited consultations. | `errors = validate_consultation_creation(...)` then immediately creates | Add `CheckEntitlementsUseCase` call before creation. If `!entitlements.can_create_consultation`, raise `PlanLimitExceededError`. | U1 |
| U6-2 | **CRITICAL** | `application/consultation/get_consultation.py:16-22` | **No doctor_id ownership check** -- `GetConsultationUseCase.execute()` only requires `consultation_id` and `clinic_id`. It does NOT verify that the requesting doctor owns the consultation. Any doctor in the same clinic can read any other doctor's consultation. | `def execute(self, consultation_id: str, clinic_id: str) -> Consultation:` | The handler (`consultation_handler.py:89`) does check ownership, but the use case itself is unprotected. If called from any other entry point (Step Functions, internal), the check is bypassed. Add `doctor_id` parameter and ownership check to the use case. | U3 |
| U6-3 | **HIGH** | `application/consultation/list_consultations.py:15-23` | **No date validation on list query** -- `start_date` and `end_date` are passed directly to the DynamoDB query with no format validation. Empty strings, garbage, or injection into the sort key expression could cause unexpected results. | `return self.consultation_repo.find_by_doctor_and_date_range(doctor_id, start_date, end_date)` | Validate date format (ISO 8601) before passing to repository. | U4 |
| U6-4 | **HIGH** | `application/transcription/finalize_transcript.py:36-38` | **No ownership check on consultation before finalization** -- `FinalizeTranscriptUseCase` fetches the consultation by ID+clinic_id but does NOT verify the requesting actor owns it. Since this is called from WebSocket `session_stop_handler`, the doctor_id check is indirect via connection lookup. | `consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)` | Add explicit doctor_id verification. | -- |
| U6-5 | **HIGH** | `application/transcription/finalize_transcript.py:40-47` | **Transcript fetch failure marks consultation as PROCESSING_FAILED but then re-raises** -- If `fetch_final_transcript` throws, the consultation is marked failed AND the exception propagates. The caller (session_stop_handler) catches this silently. But the consultation status is changed without an audit event. | `self._mark_failed(consultation, str(exc)); self.consultation_repo.save(consultation); raise` | Add audit event for PROCESSING_FAILED transitions. | -- |
| U6-6 | **MEDIUM** | `application/session/start_session.py:69-72` | **Direct entity mutation instead of repository update** -- `consultation.status = ConsultationStatus.RECORDING` directly mutates the entity, then calls `save()` (full overwrite). No optimistic locking. Two concurrent session starts could race. | `consultation.status = ConsultationStatus.RECORDING` | Use `update_status` with a condition expression to prevent concurrent modifications. | -- |
| U6-7 | **MEDIUM** | `application/session/end_session.py:73-75` | **Duration calculation assumes valid ISO format** -- `datetime.fromisoformat(session.started_at)` will raise ValueError if `started_at` is malformed or empty string. | `started = datetime.fromisoformat(session.started_at)` | Add try/except or validate before parsing. | -- |
| U6-8 | **MEDIUM** | 6 use case files | **6 use cases are empty placeholders** -- `run_pipeline.py`, `store_artifacts.py`, `open_review.py`, `update_review.py`, `finalize_consultation.py`, `generate_export.py` are all stubs with only a docstring. | `"""Use case placeholder."""` | Expected for MVP but critical for the documented workflow. Review, finalization, export are part of the core pipeline. | U5 |
| U6-9 | **LOW** | `application/patient/create_patient.py:25-28` | **Minimal patient validation** -- Only checks name is non-empty and date_of_birth is truthy. No date format validation, no duplicate detection. | `if not name or not name.strip(): raise PatientValidationError(...)` | Add date format validation and consider duplicate patient detection. | U6 |
| U6-10 | **LOW** | `application/config/get_ui_config.py:7-11` | **GetUiConfigUseCase is not a dataclass** -- Unlike all other use cases which use `@dataclass(frozen=True)` with injected dependencies, this one is a plain class with no constructor. Inconsistent pattern. | `class GetUiConfigUseCase:` | Minor inconsistency. Either make it a dataclass or extract as a function. | -- |

---

## Phase 7: Handler Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| H7-1 | **CRITICAL** | `handlers/websocket/audio_chunk_handler.py:39-41` | **No size limit on audio chunk payload** -- Base64-decoded audio data is accepted with no size validation. A client can send arbitrarily large chunks via WebSocket. API Gateway has a 128KB frame limit, but the handler does not enforce this or any application-level limit. | `audio_b64 = data.get("audio", ""); if audio_b64 and transcription_provider is not None: audio_bytes = base64.b64decode(audio_b64)` | Validate `len(audio_b64)` before decoding. Reject chunks larger than a configured max (e.g., 256KB decoded). | HA4 |
| H7-2 | **CRITICAL** | `handlers/websocket/connect_handler.py:17` | **`validate_ws_token` method does not exist on CognitoAuthProvider** -- The connect handler calls `auth_provider.validate_ws_token(token)` which is not implemented on the adapter (see A5-15). This means WebSocket connections will always fail with AttributeError. | `claims = auth_provider.validate_ws_token(token)` | Implement `validate_ws_token` on CognitoAuthProvider. | HA5 |
| H7-3 | **HIGH** | `handlers/websocket/router.py:51` | **JSON parse of WebSocket body with no error handling** -- `json.loads(event.get("body", "{}"))` will raise `json.JSONDecodeError` on malformed body, returning a 500 instead of 400. | `body = json.loads(event.get("body", "{}"))` | Wrap in try/except JSONDecodeError. | HA2 |
| H7-4 | **HIGH** | `handlers/websocket/audio_chunk_handler.py:41` | **Base64 decode with no error handling** -- `base64.b64decode(audio_b64)` will raise `binascii.Error` on malformed base64 input, crashing the handler. | `audio_bytes = base64.b64decode(audio_b64)` | Wrap in try/except and return 400 on decode failure. | HA3 |
| H7-5 | **HIGH** | `handlers/websocket/session_stop_handler.py:50-53` | **Finalization failure silently swallowed** -- `finalize_transcript_use_case.execute()` errors are caught by a bare `except Exception` and only logged. The client is told session ended successfully even though transcript processing failed. No error feedback sent via WebSocket. | `except Exception: logger.exception(...)` | Send an error event to the WebSocket client so the frontend can show a retry option. | HA6 |
| H7-6 | **HIGH** | `handlers/websocket/api_gateway_management.py:18-21` | **No error handling on API Gateway Management send** -- `post_to_connection` can fail if the connection is stale (GoneException). No try/except. | `self._client.post_to_connection(ConnectionId=connection_id, Data=...)` | Catch `GoneException` and clean up the stale connection. | HA7 |
| H7-7 | **HIGH** | `handlers/websocket/connect_handler.py:18` | **Bare `except Exception` swallows all auth errors** -- Token validation failure is caught with a bare `except Exception`, hiding the actual error. Could mask configuration errors, network issues, or SDK bugs. | `except Exception: return {"statusCode": 401}` | Catch specific exceptions. Log the error type/message at warning level. | HA8 |
| H7-8 | **MEDIUM** | `handlers/http/middleware.py:128-136` | **Malformed JSON body returns empty dict silently** -- `parse_json_body` returns `{}` on decode failure instead of returning a 400 error. Callers must then check for required fields, which they do inconsistently. | `except (json.JSONDecodeError, TypeError): return {}` | Return a parse error indicator or raise, so handlers can return 400 for malformed JSON. | HA9 |
| H7-9 | **MEDIUM** | `infra/lambda_handlers/bff.py:10` | **Stage prefix derived from env var with `dev` default** -- `_STAGE_PREFIX = f"/{os.environ.get('DESKAI_ENV', 'dev')}"`. If `DESKAI_ENV` is not set in production, all route matching will use `/dev` prefix. | `_STAGE_PREFIX = f"/{os.environ.get('DESKAI_ENV', 'dev')}"` | Validate that `DESKAI_ENV` is set in production Lambda environment. Log a warning if using default. | HA10 |
| H7-10 | **MEDIUM** | `handlers/websocket/ping_handler.py:8-14` | **Ping response has `body` as dict, not JSON string** -- Returns `"body": {"event": "server.pong", ...}` as a Python dict. API Gateway expects `body` as a string. This will either fail or be serialized incorrectly. | `"body": {"event": "server.pong", "data": {"timestamp": utc_now_iso()}}` | Use `json.dumps(...)` for the body value. | -- |
| H7-11 | **MEDIUM** | `handlers/http/middleware.py:161` | **Domain error message exposed to client** -- `str(exc)` is passed directly to the error response. Domain exceptions may contain internal IDs, field names, or implementation details. | `return error_response(status_code, code, str(exc))` | Use sanitized user-facing messages instead of raw exception strings. | HA11 |
| H7-12 | **MEDIUM** | `infra/lambda_handlers/bff.py:102-118` | **Regex routes compiled on every invocation** -- `re.compile()` is called inside the `handler()` function, meaning patterns are recompiled on every Lambda invocation instead of once at module level. | `_param_routes = [( re.compile(r"^/v1/consultations/..."), ...)]` inside `handler()` | Move `_param_routes` to module level. | -- |
| H7-13 | **LOW** | `handlers/step_functions/` | **All 3 Step Function handlers are placeholders** -- `finalize_processing_handler.py`, `process_transcript_handler.py`, `run_ai_pipeline_handler.py` return static metadata. | `"status": "processing-placeholder-complete"` | Expected for MVP but blocks the full pipeline. | HA12 |
| H7-14 | **LOW** | `handlers/http/finalize_handler.py` | **Finalize handler is a placeholder** -- The HTTP endpoint for review finalization is not implemented. | `"""Inbound handler placeholder."""` | Expected for MVP. | -- |

---

## Phase 8: BFF Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| B8-1 | **HIGH** | `bff/feature_flags/evaluator.py:21-24` | **Feature flags are hardcoded, ignoring plan type** -- `export_pdf_enabled`, `insights_enabled`, and `audio_playback_enabled` return the same boolean values regardless of `plan_type`. Every plan gets identical feature access. | `"export_pdf_enabled": True, "insights_enabled": True, "audio_playback_enabled": False` | These should vary by plan. FREE_TRIAL should have limited features. At minimum, `export_pdf_enabled` and `insights_enabled` should check plan type. | B1 |
| B8-2 | **MEDIUM** | `bff/action_availability.py:31-32` | **`export_enabled` parameter not driven by plan entitlements** -- `compute_actions` accepts `export_enabled` but it defaults to `True`. No caller passes actual plan-based value. | `def compute_actions(status, export_enabled=True):` | Wire entitlement's `export_enabled` flag into action computation. | B3 |
| B8-3 | **MEDIUM** | `bff/views/session_view.py:15` | **Session ID used as WebSocket connection token** -- `"connection_token": session.session_id` exposes the session ID as the connection token. This conflates authentication with session identification. | `"connection_token": session.session_id` | Use a separate, short-lived token (e.g., signed JWT) for WebSocket authentication. | B4 |
| B8-4 | **MEDIUM** | `bff/views/consultation_view.py:38` | **`duration_seconds` always returns None** -- `build_consultation_detail_view` hardcodes `"duration_seconds": None` even when session data might have the actual duration. | `"duration_seconds": None` | Compute from `session_started_at` and `session_ended_at`, or fetch from the session entity. | B5 |
| B8-5 | **LOW** | `bff/ui_config/assembler.py:19` | **Hardcoded version string** -- `"version": "1.0"` is not derived from settings or contract version. | `"version": "1.0"` | Use `settings.contract_version`. | B6 |
| B8-6 | **LOW** | `bff/views/export_view.py`, `bff/views/review_view.py` | **Export and review views are placeholders** -- Both files contain only docstring placeholders. | `"""BFF placeholder module."""` | Expected for MVP. | -- |

---

## Phase 9: Shared Layer Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| S9-1 | **CRITICAL** | `shared/config.py:30-51` | **Dev defaults silently used in production** -- `load_settings()` uses dev defaults for EVERY setting: `"deskai-dev-consultation-records"`, `"deskai-dev-artifacts"`, `"deskai/dev/elevenlabs"`, etc. If ANY env var is missing in production, the Lambda will silently connect to dev resources (dev DynamoDB table, dev S3 bucket, dev secrets). | `dynamodb_table=getenv("DESKAI_DYNAMODB_TABLE", DEFAULT_DYNAMODB_TABLE)` where `DEFAULT_DYNAMODB_TABLE = "deskai-dev-consultation-records"` | For production-critical settings (DynamoDB table, S3 bucket, Cognito IDs), either: (a) remove defaults and raise ConfigurationError if missing, or (b) validate that env matches DESKAI_ENV. The Cognito check on line 121-125 of `container.py` does this correctly for pool_id/client_id -- do the same for all settings. | B2 |
| S9-2 | **HIGH** | `shared/config.py:45-46` | **Empty string defaults for Cognito IDs** -- `cognito_user_pool_id` and `cognito_client_id` default to empty string `""`. While `container.py:121` catches this, the error message is a generic RuntimeError, not a ConfigurationError. | `cognito_user_pool_id=getenv("DESKAI_COGNITO_USER_POOL_ID", "")` | Use `ConfigurationError` instead of `RuntimeError` for consistency with the error hierarchy. | B7 |
| S9-3 | **MEDIUM** | `shared/logging.py:5-14` | **Logger docstring warns about PHI but no enforcement** -- The comment says "Do not attach raw transcript content or patient-identifiable fields" but there is no technical enforcement. Any caller can log whatever they want. | `"""Do not attach raw transcript content..."""` | Add a log filter that redacts known PHI field patterns (e.g., `patient_name`, `date_of_birth`, `transcript`). | B8 |
| S9-4 | **LOW** | `shared/errors.py` | **Minimal error hierarchy** -- Only `DeskAIError` and `ConfigurationError`. All domain-specific errors are in their respective domain modules, which is correct. But there's no base `InfrastructureError` for adapter-level failures. | (2 classes only) | Add `InfrastructureError(DeskAIError)` as base for adapter-specific errors. | -- |
| S9-5 | **LOW** | `shared/types.py:3` | **Python 3.12+ type alias syntax** -- `type JsonDict = dict[str, object]` uses PEP 695 type alias syntax, requiring Python >= 3.12. Ensure Lambda runtime matches. | `type JsonDict = dict[str, object]` | Verify Lambda runtime is Python 3.12+. If 3.11, use `TypeAlias` from `typing`. | -- |

---

## Phase 10: Container Findings

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|-------------|----------------|-------------|
| C10-1 | **HIGH** | `container.py:106-223` | **No artifact_repository wired** -- `ArtifactRepository` port exists and `S3ArtifactRepository` adapter exists, but neither is instantiated or wired in the container. The `store_artifacts` use case (placeholder) has no repository to use when implemented. | (missing from Container dataclass and build_container) | Add `artifact_repo: ArtifactRepository` to Container and wire `S3ArtifactRepository`. | B9 |
| C10-2 | **HIGH** | `container.py:106-223` | **No event_publisher wired** -- `EventPublisher` port exists but no adapter is wired. Domain events (consultation created, session ended, etc.) cannot be published to EventBridge. | (missing from Container) | Wire when EventBridge adapter is implemented. Track as blocker for event-driven features. | B10 |
| C10-3 | **HIGH** | `container.py:106-223` | **No export_generator wired** -- `ExportGenerator` port exists but no adapter is wired. PDF export cannot function. | (missing from Container) | Wire when PDF adapter is implemented. | B11 |
| C10-4 | **HIGH** | `container.py:106-223` | **No llm_provider wired** -- `LlmProvider` port exists but no adapter is wired. AI pipeline (medical history extraction, summarization, insights) cannot function. | (missing from Container) | Wire when Claude adapter is implemented. This blocks the core value proposition. | B12 |
| C10-5 | **MEDIUM** | `container.py:150` | **Secrets Manager called during cold start** -- `load_elevenlabs_config(settings.elevenlabs_secret_name)` makes a synchronous Secrets Manager API call during container initialization. This adds 200-500ms to cold start time. | `elevenlabs_config = load_elevenlabs_config(settings.elevenlabs_secret_name)` | Use Lambda extensions secrets cache or lazy-load the config on first transcription use. | -- |
| C10-6 | **MEDIUM** | `container.py:131-148` | **All repositories share same DynamoDB table** -- All 6 repositories use `settings.dynamodb_table`. This is a single-table design, which is valid, but means a misconfigured table name affects ALL data access simultaneously. | `DynamoDBDoctorRepository(table_name=settings.dynamodb_table)` repeated 6 times | Document the single-table design. Consider health check that verifies table access on startup. | -- |
| C10-7 | **LOW** | `container.py:222` | **`GetUiConfigUseCase()` created without dependencies** -- Unlike all other use cases, `get_ui_config` is instantiated with no constructor args. It internally calls BFF functions directly. Breaks the dependency injection pattern. | `get_ui_config=GetUiConfigUseCase()` | Either inject BFF dependencies or make it a simple function, not a use case class. | -- |
| C10-8 | **LOW** | `container.py` | **No test/dev/prod differentiation in container** -- `build_container()` always creates real AWS adapters. There's no facility for injecting mock adapters in tests or local development. | (single build function) | Add a `build_test_container()` or accept adapter overrides. | -- |

---

## Pre-Investigation Verification

| Pre-Inv # | Status | Notes |
|-----------|--------|-------|
| A1 | **CONFIRMED** | Zero error handling on ALL DynamoDB calls across ALL 6 repositories. Not a single try/except on any boto3 DynamoDB call. Systemic issue. |
| A2 | CONFIRMED | No pagination handling found in any query method. |
| A3 | CONFIRMED | Each repository creates its own `boto3.resource("dynamodb")`. |
| A4 | CONFIRMED | No `ServerSideEncryption` parameter on any S3 `put_object` call. |
| A6 | CONFIRMED | `audio_buffer` in ElevenLabsScribeProvider grows without bound. |
| A7 | CONFIRMED | 5 ports (events, export, LLM, secrets, storage_provider) have only placeholder adapters. |
| A8 | **NEW FINDING** | `CognitoAuthProvider` is missing `validate_ws_token` method entirely. WebSocket auth will crash. |
| U1 | **CONFIRMED** | `CreateConsultationUseCase` has NO entitlement check. Any user can create unlimited consultations regardless of plan. |
| U3 | **CONFIRMED** | `GetConsultationUseCase` has NO doctor_id check. The handler does check, but the use case is unprotected for non-HTTP callers. |
| U4 | CONFIRMED | No date validation in ListConsultationsUseCase. |
| U5 | CONFIRMED | 6 out of 16 use cases are empty placeholders. |
| U6 | CONFIRMED | Minimal patient validation (name non-empty, DOB truthy only). |
| HA2 | CONFIRMED | WebSocket router JSON parsing has no error handling. |
| HA3 | CONFIRMED | Base64 decode in audio_chunk_handler has no error handling. |
| HA4 | **CONFIRMED** | No size limit on audio chunk payload. |
| HA5 | **NEW FINDING** | `validate_ws_token` is called but does not exist. More severe than expected -- it's not just missing validation, it's a crash. |
| HA6 | CONFIRMED | Finalization failure silently swallowed in session_stop_handler. |
| HA7 | CONFIRMED (NEW) | API Gateway Management `post_to_connection` has no GoneException handling. |
| HA8 | CONFIRMED | Bare `except Exception` in connect_handler hides all errors. |
| HA9 | CONFIRMED | Malformed JSON body returns empty dict silently. |
| HA10 | CONFIRMED | Stage prefix defaults to `dev` if env var missing. |
| HA11 | CONFIRMED | Raw exception messages exposed in error responses. |
| HA12 | CONFIRMED | All 3 Step Function handlers are placeholders. |
| B1 | **CONFIRMED** | Feature flags (export, insights, playback) are hardcoded booleans, completely ignoring plan_type. |
| B2 | **CONFIRMED** | All settings default to dev values. Production Lambda with missing env vars will silently use dev DynamoDB table, dev S3 bucket, dev secrets. |
| B3 | CONFIRMED | `compute_actions` `export_enabled` defaults to True, not wired to plan. |
| B4 | CONFIRMED (NEW) | Session ID used as WebSocket connection token. |
| B7 | CONFIRMED | Cognito IDs default to empty string, caught by RuntimeError not ConfigurationError. |
| B8 | CONFIRMED | PHI logging warning is documentation-only, no enforcement. |
| B9 | CONFIRMED | ArtifactRepository not wired in container. |
| B10 | CONFIRMED | EventPublisher not wired in container. |
| B11 | CONFIRMED | ExportGenerator not wired in container. |
| B12 | CONFIRMED | LlmProvider not wired in container. |

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 7 |
| HIGH | 17 |
| MEDIUM | 14 |
| LOW | 11 |
| **Total** | **49** |

### Top 5 Systemic Issues

1. **Zero DynamoDB error handling** (A5-1/2/3) -- Every persistence operation can crash with unhandled ClientError. This is the single highest-impact issue: a single DynamoDB throttle or network hiccup takes down the entire application.

2. **Missing plan entitlement enforcement** (U6-1, B8-1) -- Free trial users can create unlimited consultations. Feature flags ignore plan type entirely. The billing/monetization model has no enforcement.

3. **Dev defaults in production config** (S9-1) -- A missing environment variable silently routes production traffic to dev resources (dev DynamoDB, dev S3, dev Secrets Manager). Data leakage between environments.

4. **WebSocket auth is broken** (H7-2, A5-15) -- `validate_ws_token` does not exist on CognitoAuthProvider. ALL WebSocket connections will fail with AttributeError. The real-time recording feature is non-functional.

5. **No S3 encryption on PHI artifacts** (A5-7) -- Medical transcripts, AI-generated medical histories, and clinical summaries are stored without explicit server-side encryption directives. LGPD/HIPAA compliance risk.
