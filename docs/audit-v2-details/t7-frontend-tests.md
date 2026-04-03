# Phases 14-16: Frontend + Website + Test Coverage Audit

**Auditor**: Agent T7
**Commit**: 75715f2
**Date**: 2026-04-03

---

## Phase 14: Frontend Findings

### Summary
The frontend (`app/src/`) is a **skeleton/prototype** with 14 source files. It renders a static dashboard with hardcoded status cards and a placeholder consultation page. There is **zero authentication**, **zero test coverage**, and no routing library. The app fetches UI config from the BFF on mount but does not handle auth tokens at all.

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|--------------|----------------|-------------|
| F-01 | CRITICAL | `app/` (global) | **ZERO test files** in entire frontend. No `.test.ts`, `.spec.ts`, or `__tests__/` directory found. No test runner configured (no vitest/jest in package.json). | N/A | Add vitest + @testing-library/react. Write tests for `useUiConfig`, `apiGet`, `format.ts` at minimum. | F1 CONFIRMED |
| F-02 | CRITICAL | `api/client.ts:13-27` | **No authentication token attached to API requests.** No `Authorization` header, no localStorage/sessionStorage token management, no token refresh. All API calls are unauthenticated. | `headers: { 'Content-Type': 'application/json', 'X-Contract-Version': runtimeConfig.contractVersion }` | Implement auth token storage (prefer httpOnly cookies or in-memory), attach `Authorization: Bearer <token>` to all API requests, implement 401 handling with token refresh. | F2 CONFIRMED |
| F-03 | HIGH | `api/client.ts:22-24` | **No 401/403 handling.** When `response.ok` is false, a generic `ApiError` is thrown regardless of status code. No redirect to login on 401, no token refresh attempt. | `if (!response.ok) { throw new ApiError('Falha tecnica...', response.status); }` | Intercept 401/403 specifically: attempt token refresh on 401, redirect to login on refresh failure. |
| F-04 | MEDIUM | `pages/DashboardPage.tsx:3-11` | **Entirely hardcoded values.** Dashboard shows static strings like "Aguardando backend", "Nenhuma", "v1". No data fetching, no live status. | `<StatusCard title="Status de conexao" value="Aguardando backend" />` | Wire to BFF health endpoint and real session data. |
| F-05 | MEDIUM | `pages/ConsultationPage.tsx:1-8` | **Empty placeholder page.** Only displays a static message saying data should come from the BFF. No consultation CRUD, no audio recording, no transcription UI. | `<p>Os dados desta tela devem vir do BFF e da configuracao de UI.</p>` | Implement consultation list, create, and detail views as designed in contracts. |
| F-06 | LOW | `App.tsx:10-24` | **No client-side routing.** Both DashboardPage and ConsultationPage render on the same page. No react-router or equivalent. | `<DashboardPage /><ConsultationPage />` | Add react-router-dom with proper routes for `/dashboard`, `/consultations`, `/consultations/:id`. |
| F-07 | LOW | `components/AppLayout.tsx`, `components/StatusCard.tsx` | **No ARIA attributes, no keyboard navigation.** Semantic HTML (`<header>`, `<main>`, `<article>`) is used correctly, but no `aria-label`, `aria-live`, or focus management. | `<article className="status-card">` | Add `aria-label` to StatusCard, `aria-live="polite"` to loading/error states, ensure keyboard navigation. |
| F-08 | INFO | `config/env.ts:7-11` | **Environment variables use `VITE_` prefix correctly.** Only `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`, `VITE_CONTRACT_VERSION` are exposed. No secrets in env vars. Fallbacks default to localhost. | `apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'` | Acceptable for MVP. Consider removing localhost fallback in production builds. |
| F-09 | INFO | `tsconfig.app.json:8-11` | **`strict: true` enabled.** Also has `noFallthroughCasesInSwitch` and `noUncheckedIndexedAccess`. No `any` types found in source code. Good TypeScript hygiene. | `"strict": true, "noUncheckedIndexedAccess": true` | No action needed. |
| F-10 | INFO | Global | **No XSS risk.** No `dangerouslySetInnerHTML` usage. No user input rendered unsanitized. No console.log statements. No build artifacts committed (`dist/` absent). | N/A | No action needed. |
| F-11 | INFO | `api/consultations.ts` | **fetchConsultations() defined but never called.** The function exists but no component uses it. Dead code. | `export async function fetchConsultations()` | Either implement the consultation list view that uses it, or remove it. |
| F-12 | MEDIUM | `hooks/useUiConfig.ts:19` | **Generic catch swallows error details.** `catch {}` block with no error parameter loses the original error context (type, message, status). | `} catch { if (mounted) { setError('Falha tecnica...'); } }` | Capture error parameter, log it, extract status code for differentiated error messages. |

### Frontend File Inventory
| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `main.tsx` | 10 | React root mount | Complete |
| `App.tsx` | 28 | Root component, renders all pages | Skeleton |
| `index.css` | 51 | Global styles | Complete |
| `vite-env.d.ts` | 1 | Vite type reference | Complete |
| `components/AppLayout.tsx` | 17 | Shell with header/main | Complete |
| `components/StatusCard.tsx` | 13 | Status display card | Complete |
| `pages/DashboardPage.tsx` | 11 | Hardcoded dashboard | Stub |
| `pages/ConsultationPage.tsx` | 8 | Placeholder text | Stub |
| `hooks/useUiConfig.ts` | 38 | Fetches UI config from BFF | Functional |
| `api/client.ts` | 27 | HTTP GET client with error handling | Functional (no auth) |
| `api/consultations.ts` | 11 | Consultation list fetcher | Unused |
| `types/contracts.ts` | 21 | TS types matching backend contracts | Complete |
| `utils/format.ts` | 4 | pt-BR date formatter | Complete |
| `config/env.ts` | 11 | Runtime config from env vars | Complete |

---

## Phase 15: Website Findings

### Summary
Static marketing site with 3 HTML pages, vanilla CSS, and minimal JS (mobile menu toggle only). Content is in pt-BR as expected. Clean, semantic HTML. No external dependencies loaded at runtime (no CDN scripts). Multiple missing SEO and security concerns.

| # | Severity | File:Line | Issue | Code Snippet | Recommendation | Pre-Inv Ref |
|---|----------|-----------|-------|--------------|----------------|-------------|
| W-01 | HIGH | All HTML pages | **No security headers.** No CSP meta tag, no X-Frame-Options, no X-Content-Type-Options. Static pages served via `python3 -m http.server` (dev) with no header configuration. | N/A | Add CSP meta tag to all pages. When deployed behind CloudFront (CDN stack exists), configure security headers via CloudFront Functions or response headers policy. | W1 CONFIRMED |
| W-02 | MEDIUM | `pages/about.html:8`, `pages/pricing.html:8` | **Missing meta description** on About and Pricing pages. Only `index.html` has it. | `<title>Sobre | DeskAI</title>` (no meta description) | Add `<meta name="description" content="...">` to all pages for SEO. |
| W-03 | MEDIUM | All HTML pages | **No Open Graph (OG) tags.** No `og:title`, `og:description`, `og:image`, `og:url`. Social sharing will show generic previews. | N/A | Add OG meta tags to all pages, especially index.html. | W3 CONFIRMED |
| W-04 | MEDIUM | `pages/about.html`, `pages/pricing.html` | **Missing header/navigation.** Only `index.html` has the site header with nav. About and Pricing pages have no way to navigate to other pages except the "Voltar" link at bottom. | Only `<a href="./index.html">Voltar para a pagina inicial</a>` | Include the same header/nav component on all pages for consistent navigation. |
| W-05 | MEDIUM | `pages/pricing.html:12-25` | **Pricing plan names partially match backend.** Site shows "Teste Gratis", "Plus", "Pro". Backend PlanType enum has `free_trial`, `plus`, `pro`. Names align conceptually but no pricing amounts are shown. | `<h2>Teste Gratis</h2>` / `<h2>Plus</h2>` / `<h2>Pro</h2>` | Add specific features, limits, and prices per plan. Align display names with backend PlanType values. | W5 PARTIAL MATCH |
| W-06 | LOW | `pages/index.html:21-22` | **Dead links.** "Entrar" and "Solicitar acesso" both link to `#`. | `<a class="cta" href="#">Entrar</a>` / `<a class="btn" href="#">Solicitar acesso</a>` | Wire to the actual app URL or a signup/login page. | W6 CONFIRMED |
| W-07 | LOW | `assets/js/main.js:1-9` | **Menu toggle JS has no fallback.** If JS fails, mobile menu is permanently hidden. No `<noscript>` alternative. | `toggle.addEventListener('click', () => { nav.classList.toggle('is-open'); })` | Acceptable for MVP. Consider progressive enhancement or noscript fallback. |
| W-08 | LOW | `assets/css/main.css:29-31` | **Sticky header has no z-index.** On scroll, content could overlap the header. | `.site-header { position: sticky; top: 0; }` | Add `z-index: 100` to `.site-header`. |
| W-09 | INFO | Global | **Content correctly in pt-BR.** All pages use `<html lang="pt-BR">`, all text is in Portuguese. No external JS/CSS dependencies loaded (no SRI needed). No images used (`.gitkeep` in images dir). | N/A | No action needed. |
| W-10 | INFO | `pages/index.html:55` | **JS loaded at end of body** (correct placement). CSS uses only custom properties (no framework). Total CSS: 137 lines. Lightweight. | `<script src="../assets/js/main.js"></script>` | No action needed. |

---

## Phase 16: Test Coverage

### Complete Coverage Matrix

**Legend**: Y = test exists, N = no test, P = partial (tested indirectly), STUB = source is placeholder/stub

#### Domain Layer (40 source files)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| ai_pipeline | `domain/ai_pipeline/entities.py` | N | - | 0 | **UNTESTED** - AI entities (PipelineResult, ClinicalObservation, DraftDocument) |
| ai_pipeline | `domain/ai_pipeline/exceptions.py` | N | - | 0 | **UNTESTED** |
| ai_pipeline | `domain/ai_pipeline/services.py` | N | - | 0 | **UNTESTED** - Core AI business logic |
| ai_pipeline | `domain/ai_pipeline/value_objects.py` | N | - | 0 | **UNTESTED** |
| audit | `domain/audit/entities.py` | Y | `test_audit_domain.py` | 5 | Entity creation, AuditAction enum |
| audit | `domain/audit/exceptions.py` | P | (via test_audit_domain.py) | - | Indirect |
| audit | `domain/audit/services.py` | N | - | 0 | **UNTESTED** |
| audit | `domain/audit/value_objects.py` | P | (via test_audit_domain.py) | - | Indirect |
| auth | `domain/auth/entities.py` | Y | `test_auth_entities.py` | 2 | Dataclass creation only |
| auth | `domain/auth/exceptions.py` | Y | `test_auth_exceptions.py` | 2 | Exception hierarchy |
| auth | `domain/auth/services.py` | N | - | 0 | **UNTESTED** |
| auth | `domain/auth/value_objects.py` | Y | `test_auth_value_objects.py` | 8 | PlanType, Tokens, AuthContext, Entitlement |
| config | `domain/config/entities.py` | N | - | 0 | **UNTESTED** |
| config | `domain/config/exceptions.py` | N | - | 0 | **UNTESTED** |
| config | `domain/config/services.py` | N | - | 0 | **UNTESTED** |
| config | `domain/config/value_objects.py` | N | - | 0 | **UNTESTED** |
| consultation | `domain/consultation/entities.py` | Y | `test_consultation_domain.py` | 5 | Status enum, entity creation/mutation |
| consultation | `domain/consultation/events.py` | P | `test_consultation_lifecycle.py` | 25 | Lifecycle state machine |
| consultation | `domain/consultation/exceptions.py` | P | (via handlers) | - | Indirect |
| consultation | `domain/consultation/rules.py` | Y | `test_consultation_rules.py` | 13 | validate_creation, can_finalize -- GOOD |
| consultation | `domain/consultation/services.py` | N | - | 0 | **UNTESTED** |
| consultation | `domain/consultation/value_objects.py` | P | `test_consultation_status.py` | 1 | Only status count |
| export | `domain/export/entities.py` | N | - | 0 | **UNTESTED** |
| export | `domain/export/exceptions.py` | N | - | 0 | **UNTESTED** |
| export | `domain/export/services.py` | N | - | 0 | **UNTESTED** |
| export | `domain/export/value_objects.py` | N | - | 0 | **UNTESTED** |
| patient | `domain/patient/entities.py` | Y | `test_patient_domain.py` | 4 | Entity creation |
| patient | `domain/patient/exceptions.py` | P | (via use cases) | - | Indirect |
| patient | `domain/patient/services.py` | N | - | 0 | **UNTESTED** |
| patient | `domain/patient/value_objects.py` | N | - | 0 | **UNTESTED** |
| review | `domain/review/entities.py` | N | - | 0 | **UNTESTED** - Physician review entities |
| review | `domain/review/exceptions.py` | N | - | 0 | **UNTESTED** |
| review | `domain/review/services.py` | N | - | 0 | **UNTESTED** |
| review | `domain/review/value_objects.py` | N | - | 0 | **UNTESTED** |
| session | `domain/session/entities.py` | Y | `test_session_domain.py` | 34 | Session lifecycle, guard logic -- GOOD |
| session | `domain/session/exceptions.py` | P | (via test_session_domain) | - | Indirect |
| session | `domain/session/services.py` | N | - | 0 | **UNTESTED** |
| session | `domain/session/value_objects.py` | P | (via test_session_domain) | - | Indirect |
| transcription | `domain/transcription/entities.py` | Y | `domain/transcription/test_entities.py` | 4 | Entity creation, defaults, mutation |
| transcription | `domain/transcription/exceptions.py` | Y | `domain/transcription/test_exceptions.py` | 11 | Exception hierarchy, messages |
| transcription | `domain/transcription/services.py` | Y | `domain/transcription/test_services.py` | 19 | TranscriptionService business logic -- GOOD |
| transcription | `domain/transcription/value_objects.py` | Y | `domain/transcription/test_value_objects.py` | 11 | Enums, SpeakerSegment, config VOs |

#### Ports Layer (15 source files)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| ports | `ports/artifact_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/audit_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/auth_provider.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/config_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/connection_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/consultation_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/doctor_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/event_publisher.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/export_generator.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/llm_provider.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/patient_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/session_repository.py` | Y | `test_session_ports.py` | 12 | Only session port tested |
| ports | `ports/storage_provider.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/transcript_repository.py` | N | - | 0 | Protocol/interface only |
| ports | `ports/transcription_provider.py` | N | - | 0 | Protocol/interface only |

**Note:** Ports are Protocol (interface) definitions. Testing them directly is low-value; the important thing is that adapter implementations are tested against the port contract. Only `session_repository` has explicit port-level tests.

#### Application Layer (Use Cases) (25 source files, excluding placeholders)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| ai_pipeline | `application/ai_pipeline/run_pipeline.py` | N | - | 0 | **UNTESTED** - Core pipeline orchestration |
| ai_pipeline | `application/ai_pipeline/store_artifacts.py` | N | - | 0 | **UNTESTED** |
| auth | `application/auth/authenticate.py` | Y | `test_authenticate_use_case.py` | 2 | Success + error propagation |
| auth | `application/auth/check_entitlements.py` | Y | `test_check_entitlements_use_case.py` | 3 | Entitlement checks |
| auth | `application/auth/forgot_password.py` | Y | `test_forgot_password_use_case.py` | 4 | Forgot + confirm flows |
| auth | `application/auth/get_current_user.py` | Y | `test_get_current_user_use_case.py` | 2 | Success + not found |
| auth | `application/auth/sign_out.py` | Y | `test_sign_out_use_case.py` | 2 | Success + error |
| config | `application/config/get_ui_config.py` | Y | `test_get_ui_config_use_case.py` | 7 | Config retrieval, fallbacks |
| consultation | `application/consultation/create_consultation.py` | Y | `test_create_consultation_use_case.py` | 6 | Creation, audit, validation -- GOOD |
| consultation | `application/consultation/get_consultation.py` | Y | `test_get_consultation_use_case.py` | 2 | Found + not found |
| consultation | `application/consultation/list_consultations.py` | Y | `test_list_consultations_use_case.py` | 2 | List results |
| export | `application/export/generate_export.py` | N | - | 0 | **UNTESTED** |
| patient | `application/patient/create_patient.py` | Y | `test_create_patient_use_case.py` | 5 | Create, validate, audit |
| patient | `application/patient/list_patients.py` | Y | `test_list_patients_use_case.py` | 2 | List results |
| review | `application/review/finalize_consultation.py` | N | - | 0 | **UNTESTED** - Critical business action |
| review | `application/review/open_review.py` | N | - | 0 | **UNTESTED** |
| review | `application/review/update_review.py` | N | - | 0 | **UNTESTED** |
| session | `application/session/end_session.py` | Y | `test_end_session_use_case.py` | 8 | End session, guards, cleanup |
| session | `application/session/start_session.py` | Y | `test_start_session_use_case.py` | 6 | Start, duplicate guards |
| transcription | `application/transcription/finalize_transcript.py` | Y | `test_finalize_transcript_use_case.py` | 8 | Finalization logic |
| transcription | `application/transcription/process_audio_chunk.py` | Y | `test_process_audio_chunk_use_case.py` | 8 | Chunk processing |
| transcription | `application/transcription/process_transcript.py` | N | - | 0 | **UNTESTED** |
| transcription | `application/transcription/store_transcript.py` | N | - | 0 | **UNTESTED** |

#### Adapters Layer (23 source files, excluding placeholders)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| auth | `adapters/auth/cognito_provider.py` | Y | `test_cognito_provider.py` | 18 | Auth, refresh, sign-out, errors -- GOOD |
| events | `adapters/events/eventbridge_publisher.py` | N | - | 0 | **UNTESTED** |
| export | `adapters/export/pdf_generator.py` | N | - | 0 | **UNTESTED** |
| llm | `adapters/llm/claude_provider.py` | N | - | 0 | **UNTESTED** - AI provider |
| persistence | `adapters/persistence/dynamodb_audit_repository.py` | Y | `test_dynamodb_audit_repo.py` | 5 | Save, query |
| persistence | `adapters/persistence/dynamodb_client.py` | N | - | 0 | **UNTESTED** |
| persistence | `adapters/persistence/dynamodb_config_repository.py` | N | - | 0 | **UNTESTED** |
| persistence | `adapters/persistence/dynamodb_connection_repository.py` | Y | `test_dynamodb_connection_repo.py` | 4 | Save, find, delete |
| persistence | `adapters/persistence/dynamodb_consultation_repository.py` | Y | `test_dynamodb_consultation_repo.py` | 10 | CRUD operations |
| persistence | `adapters/persistence/dynamodb_doctor_repository.py` | Y | `test_dynamodb_doctor_repository.py` | 7 | CRUD operations |
| persistence | `adapters/persistence/dynamodb_patient_repository.py` | Y | `test_dynamodb_patient_repo.py` | 6 | CRUD operations |
| persistence | `adapters/persistence/dynamodb_session_repository.py` | Y | `test_dynamodb_session_repo.py` | 8 | Session CRUD |
| secrets | `adapters/secrets/secrets_manager.py` | N | - | 0 | **UNTESTED** |
| storage | `adapters/storage/s3_artifact_keys.py` | Y | `test_s3_artifact_keys.py` | 10 | Key generation patterns -- GOOD |
| storage | `adapters/storage/s3_artifact_repository.py` | Y | `test_s3_artifact_repository.py` | 6 | Store, retrieve |
| storage | `adapters/storage/s3_client.py` | Y | `test_s3_client.py` | 11 | Put, get, presigned URLs |
| storage | `adapters/storage/s3_storage_provider.py` | N | - | 0 | **UNTESTED** |
| storage | `adapters/storage/s3_transcript_repository.py` | Y | `test_s3_transcript_repository.py` | 7 | Transcript store/retrieve |
| transcription | `adapters/transcription/elevenlabs_config.py` | Y | `test_elevenlabs_config.py` | 8 | Config loading, defaults |
| transcription | `adapters/transcription/elevenlabs_provider.py` | Y | `test_elevenlabs_provider.py` | 32 | Provider lifecycle, streaming -- EXCELLENT |

#### Handlers Layer (21 source files, excluding placeholders)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| http | `handlers/http/auth_handler.py` | Y | `test_auth_handler.py` | 10 | Login, logout, forgot password |
| http | `handlers/http/consultation_handler.py` | Y | `test_consultation_handler.py` | 7 | Create, get, list |
| http | `handlers/http/export_handler.py` | N | - | 0 | **UNTESTED** |
| http | `handlers/http/finalize_handler.py` | N | - | 0 | **UNTESTED** |
| http | `handlers/http/me_handler.py` | Y | `test_me_handler.py` | 3 | Get current user |
| http | `handlers/http/middleware.py` | Y | `test_middleware.py` | 12 | Auth extraction, error handling, JSON -- GOOD |
| http | `handlers/http/patient_handler.py` | Y | `test_patient_handler.py` | 3 | Create, list patients |
| http | `handlers/http/review_handler.py` | N | - | 0 | **UNTESTED** |
| http | `handlers/http/session_handler.py` | Y | `test_session_handler.py` | 9 | Start, end, get session |
| http | `handlers/http/ui_config_handler.py` | Y | `test_ui_config_handler.py` | 6 | Config endpoint |
| step_functions | `handlers/step_functions/finalize_processing_handler.py` | N | - | 0 | **UNTESTED** |
| step_functions | `handlers/step_functions/process_transcript_handler.py` | N | - | 0 | **UNTESTED** |
| step_functions | `handlers/step_functions/run_ai_pipeline_handler.py` | N | - | 0 | **UNTESTED** |
| websocket | `handlers/websocket/api_gateway_management.py` | N | - | 0 | **UNTESTED** |
| websocket | `handlers/websocket/audio_chunk_handler.py` | Y | `test_ws_audio_chunk_handler.py` | 3 | Route handling |
| websocket | `handlers/websocket/connect_handler.py` | Y | `test_ws_connect_handler.py` | 3 | Connection handling |
| websocket | `handlers/websocket/disconnect_handler.py` | Y | `test_ws_disconnect_handler.py` | 3 | Disconnection handling |
| websocket | `handlers/websocket/ping_handler.py` | Y | `test_ws_ping_handler.py` | 1 | Ping response |
| websocket | `handlers/websocket/router.py` | Y | `test_ws_router.py` | 7 | Route dispatching |
| websocket | `handlers/websocket/session_init_handler.py` | Y | `test_ws_session_init_handler.py` | 3 | Session init |
| websocket | `handlers/websocket/session_stop_handler.py` | Y | `test_ws_session_stop_handler.py` | 2 | Session stop |

#### BFF Layer (10 source files)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| bff | `bff/action_availability.py` | Y | `test_action_availability.py` | 14 | Action availability rules -- GOOD |
| bff | `bff/feature_flags/evaluator.py` | Y | `test_feature_flag_evaluator.py`, `test_evaluator.py` | 11 | Flag evaluation |
| bff | `bff/feature_flags/flags.py` | Y | `test_flags.py` | 12 | Flag definitions |
| bff | `bff/response.py` | Y | `test_bff_response.py` | 6 | Response building |
| bff | `bff/ui_config/assembler.py` | Y | `test_ui_config_assembler.py` | 10 | Config assembly |
| bff | `bff/ui_config/labels.py` | Y | `test_ui_config_labels.py` | 8 | Label registry |
| bff | `bff/ui_config/screen_config.py` | Y | `test_ui_config_screen_config.py` | 11 | Screen configs |
| bff | `bff/views/consultation_view.py` | Y | `test_consultation_view.py` | 8 | View serialization |
| bff | `bff/views/export_view.py` | N | - | 0 | **UNTESTED** |
| bff | `bff/views/review_view.py` | N | - | 0 | **UNTESTED** |
| bff | `bff/views/session_view.py` | Y | `test_session_view.py` | 4 | View serialization |
| bff | `bff/views/user_view.py` | Y | `test_user_view.py` | 4 | User view |

#### Shared + Container (7 source files)

| Module | Source File | Has Test? | Test File(s) | Test Count | Assessment |
|--------|-----------|-----------|-------------|------------|------------|
| shared | `shared/config.py` | Y | `test_shared.py`, integration | 21 | Settings, env vars -- GOOD |
| shared | `shared/errors.py` | Y | `test_shared.py` | 4 | Error hierarchy |
| shared | `shared/identifiers.py` | Y | `test_shared.py` | 3 | UUID generation |
| shared | `shared/logging.py` | Y | `test_shared.py` | 2 | Logger setup |
| shared | `shared/time.py` | Y | `test_shared.py` | 3 | UTC time |
| shared | `shared/types.py` | N | - | 0 | Type aliases (low-value) |
| container | `container.py` | Y | `test_container.py`, `test_container_transcription.py` | 10 | DI wiring |

#### Infrastructure Tests (2 test files)

| Test File | Test Count | Assessment |
|-----------|------------|------------|
| `infra/tests/test_config.py` | 4 | Env config, CORS origins, budget limits |
| `infra/tests/test_stacks.py` | 17 | CDK synthesis, all 9 stacks validated -- GOOD |

---

### Test Quality Analysis

#### Strong Tests (exemplary quality)
- **`test_elevenlabs_provider.py`** (32 tests): Thorough lifecycle testing, streaming mock, error paths, cleanup. Best-tested module.
- **`test_session_domain.py`** (34 tests): Session state machine with guard conditions, edge cases.
- **`test_consultation_lifecycle.py`** (25 tests): Status transitions exhaustively tested.
- **`test_consultation_rules.py`** (13 tests): Every status tested for `can_finalize`, validates all rule inputs.
- **`test_create_consultation_use_case.py`** (6 tests): Tests creation, validation, audit event, repo save. Good mock setup.
- **`test_cognito_provider.py`** (18 tests): Auth, refresh, sign-out, multiple error types.
- **`test_middleware.py`** (12 tests): Auth extraction, domain error mapping, JSON parsing.
- **`infra/tests/test_stacks.py`** (17 tests): CDK synthesis validates resource counts, properties, security settings.

#### Shallow Tests (low assertion quality)
- **`test_consultation_domain.py`** (5 tests): Only tests dataclass creation and status enum values. No business logic.
- **`test_auth_entities.py`** (2 tests): Only tests `DoctorProfile` construction.
- **`test_auth_exceptions.py`** (2 tests): Only tests exception hierarchy.
- **`test_consultation_status.py`** (1 test): Only `len(ConsultationStatus) == 7`. Redundant with `test_consultation_domain.py`.
- **`test_patient_domain.py`** (4 tests): Only entity creation, no validation logic.
- **`test_get_consultation_use_case.py`** (2 tests): Only success + not-found, no authorization checks.
- **`test_list_consultations_use_case.py`** (2 tests): Only tests list returns results. No filtering, pagination.

#### Mocking Quality
- Mocking is consistent: `unittest.mock.MagicMock` throughout, `@patch` for module-level dependencies.
- `conftest.py` provides good shared fixtures: `make_sample_doctor_profile()`, `make_sample_consultation()`, `make_sample_patient()`, `make_sample_audit_event()`, `make_apigw_event()`.
- All fixtures use factory functions with keyword defaults (good pattern).
- Mock AWS clients (`make_mock_cognito_client`, `make_mock_dynamodb_table`) in conftest are reused.

#### conftest.py Analysis
The conftest at `backend/tests/conftest.py` (219 lines) is **well-structured**:
- 3 AWS client mock factories: Cognito, DynamoDB table, DynamoDB resource
- 5 domain fixture factories: DoctorProfile, Tokens, AuthContext, Consultation, Patient, AuditEvent
- 1 API Gateway event builder with JWT authorizer simulation
- All factory functions accept `**overrides` for flexible test data
- Used across 15+ test files

**Not a pytest conftest** -- note these are plain factory functions, not pytest fixtures (no `@pytest.fixture`). Tests use `unittest.TestCase`, not pytest. The factories are imported explicitly (`from tests.conftest import make_sample_...`).

---

### Summary

| Category | Total Source Files | With Tests | Without Tests | Coverage % |
|----------|-------------------|------------|---------------|------------|
| Domain | 40 | 17 (direct) + 6 (indirect) | 17 | 42.5% (direct) / 57.5% (with indirect) |
| Ports | 15 | 1 | 14 | 6.7% (ports are interfaces, low-value to test) |
| Application (Use Cases) | 25 | 16 | 9 | 64.0% |
| Adapters | 23 | 15 | 8 | 65.2% |
| Handlers | 21 | 14 | 7 | 66.7% |
| BFF | 12 | 10 | 2 | 83.3% |
| Shared + Container | 7 | 6 | 1 | 85.7% |
| **TOTAL (excl. ports)** | **128** | **78** | **50** | **60.9%** |
| **TOTAL (incl. ports)** | **143** | **79** | **64** | **55.2%** |
| Placeholder files | 14 | - | - | N/A |
| Frontend (app/) | 14 TS files | 0 | 14 | **0%** |
| Infra (CDK) | ~12 stacks | 2 test files | - | ~100% stacks synthesized |

**Total backend test functions**: 569 (unit) + 1 (integration) = **570 tests**
**Total infra test functions**: 21

### Critical Untested Modules (Business Risk)

1. **Entire AI pipeline domain + application** (`ai_pipeline/`) -- 6 files, 0 tests. This is the core AI feature: clinical observation extraction, draft document generation, evidence linking.
2. **Entire review domain + application** (`review/`) -- 7 files, 0 tests. Physician review is the safety-critical compliance feature. `finalize_consultation` changes medical record state permanently.
3. **Entire export domain + application** (`export/`) -- 5 files, 0 tests. PDF generation of medical documents.
4. **Entire config domain** (`config/entities.py`, `config/services.py`, `config/value_objects.py`) -- 3 files, 0 tests (only the use case is tested via `test_get_ui_config_use_case.py`).
5. **All Step Functions handlers** -- 3 files, 0 tests. These handle async processing, AI pipeline invocation, and transcript finalization.
6. **Claude LLM adapter** (`claude_provider.py`) -- 0 tests for AI provider integration.
7. **EventBridge publisher** -- 0 tests for event publishing.
8. **Frontend** -- 0 tests for 14 TypeScript files.
9. **Domain services** in auth, audit, consultation, patient -- 0 tests. Services files contain business logic that entities and use cases rely on.

### TDD Violations

1. **Implementation without tests**: 50 production source files have no corresponding test file. At 55-61% coverage (depending on how ports are counted), the pre-investigation estimate of ~28% was too pessimistic, but the gaps are concentrated in the highest-risk areas.
2. **Shallow entity tests**: Several test files (auth entities, patient domain, consultation domain) only verify dataclass construction and enum values, not business behavior. This inflates the "tested" count without meaningful coverage.
3. **Missing integration tests**: Only 1 integration test (`test_settings_loading.py` -- 1 test function). No end-to-end handler tests, no DynamoDB integration tests, no Step Functions integration tests.
4. **No handler→use_case→repository chain tests**: Individual layers are tested in isolation but never wired together.
5. **Dead test comment**: `test_consultation_domain.py:70` has `# Stub: rules.py and value_objects.py are empty stubs. Tests will be expanded in Task 006...` but `rules.py` already has content and separate tests exist. Stale comment.

---

## Pre-Investigation Verification

| Ref | Claim | Verdict |
|-----|-------|---------|
| F1 | ZERO test files in frontend | **CONFIRMED** -- no test files, no test runner, no test config |
| F2 | No auth at all in frontend | **CONFIRMED** -- no Authorization header, no token storage, no login flow |
| W1 | No security headers on website | **CONFIRMED** -- no CSP, no X-Frame-Options, no X-Content-Type-Options |
| W3 | No OG tags | **CONFIRMED** -- no og:* meta tags on any page |
| W5 | Pricing matches plan types | **PARTIALLY CONFIRMED** -- names conceptually align (Teste Gratis/free_trial, Plus/plus, Pro/pro) but no prices or feature limits shown |
| W6 | Dead links | **CONFIRMED** -- "Entrar" and "Solicitar acesso" both href="#" |
| A.17 | ~28% test coverage (11 of ~40 modules) | **REFUTED** -- actual coverage is 55-61% (79 of 143 files have tests). The pre-investigation count likely only counted distinct test file basenames without mapping comprehensively. However, if measuring by modules with COMPLETE coverage (all files tested), the number drops significantly as many modules are partially tested. The spirit of the concern is valid: critical modules (AI, review, export) have 0% coverage. |
