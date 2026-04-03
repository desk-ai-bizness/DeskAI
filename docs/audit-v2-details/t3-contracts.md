# Phase 2: Contract Validation Audit

**Auditor**: Agent T3
**Commit**: 75715f2
**Date**: 2026-04-03

---

## HTTP Contract Findings

| # | Severity | File | Endpoint | Issue | Recommendation | Pre-Inv Ref |
|---|----------|------|----------|-------|----------------|-------------|
| H1 | HIGH | `review.yaml` | `GET /v1/consultations/{id}/review` | Missing `403` response. A doctor should not access another doctor's consultation review. No ownership check documented. | Add `403` with `ErrorResponse` and description "Not authorized to view this consultation's review". | C1 |
| H2 | HIGH | `review.yaml` | `PUT /v1/consultations/{id}/review` | Missing `403` response. No ownership authorization check documented. | Add `403` with `ErrorResponse` and description "Not authorized to update this consultation's review". | C2 |
| H3 | HIGH | `review.yaml` | `POST /v1/consultations/{id}/finalize` | Missing `403` response. No ownership authorization check documented. | Add `403` with `ErrorResponse` and description "Not authorized to finalize this consultation". | C3 |
| H4 | MEDIUM | `review.yaml` | `PUT /v1/consultations/{id}/review` | Missing `409` response. If the consultation is not in `under_physician_review` state, the update should be rejected — same pattern used in `POST /finalize` (which does have 409). | Add `409` with description "Consultation is not in under_physician_review state". | C4 |
| H5 | MEDIUM | `review.yaml` | `UpdateReviewRequest.medical_history` (line 246) | `additionalProperties: true` — accepts any arbitrary JSON key/value as medical history content. This is a medical record field; the contract provides zero shape validation. | Define a schema for the `medical_history` object with known fields, or at minimum use a `description` clarifying why it's freeform and document the expected structure. | C5 |
| H6 | MEDIUM | `review.yaml` | `ReviewView.medical_history.content` (line 155) | `additionalProperties: true` on the response side. Same concern — no shape validation for medical record content being returned to the frontend. | Define or reference the expected `medical_history` content schema. | — |
| H7 | MEDIUM | `review.yaml` | `ReviewView.ui_config.labels` (line 179) | `additionalProperties: true` — but the sibling contract `ui-config.yaml` defines `UILabels` with `additionalProperties: false` and 10 required keys. The review-embedded `ui_config.labels` is inconsistent with the main UI config contract. | Replace with `$ref` to `ui-config.yaml#/components/schemas/UILabels` or replicate the same strict schema. | — |
| H8 | LOW | `auth.yaml` | `POST /v1/auth/forgot-password` | Missing `400` response. If the email field is malformed or missing, there's no documented error response. The `200` always succeeds (anti-enumeration), but a structurally invalid request body should still return 400. | Add `400` with `ErrorResponse` for missing/invalid `email` field. | C6 |
| H9 | LOW | `auth.yaml` | `POST /v1/auth/confirm-forgot-password` | Missing `400` response. Request has 3 required fields (`email`, `confirmation_code`, `new_password`) but no 400 for validation errors. Only 200 and 401 are defined. | Add `400` with `ErrorResponse` for missing/invalid fields (e.g., weak password, missing email). | — |
| H10 | LOW | `auth.yaml` | `POST /v1/auth/session` | Missing explicit `security: []` declaration. This is a public endpoint (login) that does not require authentication, but per OpenAPI 3.1 best practices, public endpoints should explicitly declare `security: []` to distinguish them from endpoints that inherit a global security scheme. | Add `security: []` to make the public nature explicit. | — |
| H11 | LOW | `auth.yaml` | `POST /v1/auth/forgot-password` | Missing explicit `security: []` declaration. Same as H10. | Add `security: []`. | — |
| H12 | LOW | `auth.yaml` | `POST /v1/auth/confirm-forgot-password` | Missing explicit `security: []` declaration. Same as H10. | Add `security: []`. | — |
| H13 | MEDIUM | `consultations.yaml` | `GET /v1/consultations` | Missing `403` response. This is a protected endpoint (`security: bearerAuth`) but only defines 200, 400, 401. If a user authenticates but has no doctor profile (like `GET /v1/me` handles with 403), the contract doesn't cover it. | Add `403` with description "No doctor profile found" or "Not authorized to list consultations". | C7 |
| H14 | INFO | `errors.yaml` | `ErrorResponse.error.code` (line 19) | `code` is typed as bare `type: string` with no `enum` constraint. The contract inventory (03-contract-inventory.md) defines 11 specific error codes (`validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `plan_limit_exceeded`, `trial_expired`, `session_duration_exceeded`, `feature_not_available`, `service_unavailable`, `export_expired`, `internal_error`). The schema doesn't enforce these. | Add `enum` with the documented error codes, or use `examples` to reference them. Without enum, any string is a valid code — frontend error handling can't rely on contract guarantees. | C8 |
| H15 | INFO | `errors.yaml` | `ErrorResponse.error.details` (line 23) | `additionalProperties: true` — completely freeform. Acceptable for a debug/diagnostics bag, but worth noting that clients cannot rely on any structure here. | Document that `details` is intentionally unstructured, or define known detail shapes per error code. | — |
| H16 | MEDIUM | `patients.yaml` | `/v1/patients/{patient_id}` | **Missing endpoint.** No `GET`, `PUT`, or `PATCH` for individual patient by ID. The contract only defines `POST /v1/patients` (create) and `GET /v1/patients` (list with search). A doctor cannot view or update a specific patient's details. | Add `GET /v1/patients/{patient_id}` and `PUT /v1/patients/{patient_id}` (or `PATCH`) endpoints. | C10 |
| H17 | LOW | `patients.yaml` | `GET /v1/patients` | Missing pagination parameters. Unlike `GET /v1/consultations` which has `page`, `page_size`, `from`, `to` query params, the patient list has only a `search` param. For clinics with many patients, this will return unbounded results. | Add `page` and `page_size` query parameters. | — |
| H18 | MEDIUM | ALL HTTP contracts | ALL endpoints | No endpoint defines `500` (internal_error) or `503` (service_unavailable) responses. The contract inventory lists these as standard error codes, but they're absent from every YAML. Frontend has no contract guarantee for server error shapes. | Add `500` and optionally `503` to each endpoint (or at minimum document them as implicit via a global `responses` section). | — |
| H19 | LOW | `ui-config.yaml` | `GET /v1/ui-config` | The `UIConfigView` includes `feature_flags` with only 3 boolean flags (`export_enabled`, `insights_enabled`, `audio_playback_enabled`). The contract inventory (Section 5) lists 8 flags including integer types (`consultation.monthly_limit`, `consultation.max_duration_minutes`, `audio.retention_days`, `trial.duration_days`). These are not served in the UI config response. | Either expand `FeatureFlags` to include the integer flags, or document that integer flags are internal-only (evaluated by BFF, never sent to frontend). | — |
| H20 | LOW | `consultations.yaml` | `ConsultationDetailView.processing.error_details` (line 386) | `additionalProperties: true` — freeform error details. Acceptable for a debug bag but noted for completeness. | Consider defining known error shapes (e.g., `{ error_type, message, stack_trace }`). | — |

---

## WebSocket Contract Findings

| # | Severity | File | Issue | Recommendation |
|---|----------|------|-------|----------------|
| W1 | HIGH | `session.yaml` + `events.yaml` | **No `$connect` auth schema.** The contract inventory states auth happens via query string token on `$connect`, but neither WebSocket YAML defines the `$connect` route, its required `connection_token` parameter, or the error response when authentication fails. | Add a `$connect` message/schema definition specifying `connection_token` as a required query parameter, and document the 401/403 rejection behavior. |
| W2 | MEDIUM | `events.yaml` | **No dedicated error event type.** Errors are folded into `session.status` with `status: "error"`. There is no structured error payload (no error code, no error category). A client receiving `session.status` with `status: "error"` gets only a freeform `message` string. | Add an `error.code` field to the `session.status` data when `status` is `error`, or create a separate `session.error` event type with structured error information. |
| W3 | MEDIUM | `events.yaml` | **No `$disconnect` event schema.** The inventory mentions `$disconnect` (server-detected), but the YAML has no corresponding event or data shape. Clients don't know if a disconnect was intentional or a network failure. | Add a `session.disconnected` event type with `reason` field (e.g., `client_initiated`, `server_timeout`, `network_error`). |
| W4 | LOW | `session.yaml` | **`session.init` does not include `connection_token`.** The HTTP `SessionStartView` returns `connection_token` for WebSocket auth, but `session.init` only requires `consultation_id` and `session_id`. The init message cannot be used to authenticate — auth must happen at `$connect` (which is undocumented, see W1). | Document the auth flow explicitly: token goes in `$connect` query string, not in `session.init`. |
| W5 | LOW | `events.yaml` | The top-level `data` field (line 18) is `type: object` with no constraints. The `allOf` conditional schemas apply further constraints per event type, but JSON Schema validators may or may not enforce the conditional branches correctly — the base `data: object` is always valid. | Consider restructuring using `oneOf` with discriminator on `event` for clearer validation. |

---

## Feature Flag Findings

| # | Severity | File | Issue | Recommendation |
|---|----------|------|-------|----------------|
| F1 | MEDIUM | `flags.yaml` | **Schema only, no flag instances.** The YAML defines the generic shape of a flag (`type`, `default`, `overrides`) but does not enumerate the 8 specific flags listed in the contract inventory (Section 5). There is no machine-readable registry of which flags exist. | Add an `$defs` or `examples` section listing all 8 documented flags with their types, defaults, and plan overrides. This makes the contract self-documenting and enables automated validation. |
| F2 | LOW | `flags.yaml` | **No type coercion between `default` and `overrides`.** The schema allows `default: true` (boolean) with `overrides: { plus: 50 }` (integer) — a type mismatch within the same flag. The `oneOf` on both `default` and `overrides` doesn't enforce that they share the same type. | Add a cross-field validation or use conditional schemas (`if type == "boolean" then default must be boolean`). |
| F3 | INFO | `flags.yaml` vs `ui-config.yaml` | **Flag name mismatch.** The inventory uses dotted names (`consultation.create.enabled`, `export.pdf.enabled`). The HTTP `FeatureFlags` schema uses underscored names (`export_enabled`, `insights_enabled`, `audio_playback_enabled`). These are different naming conventions for the same concepts — `export.pdf.enabled` vs `export_enabled`. | Standardize naming: either all dotted (internal) or all underscored (API-facing), with a documented mapping. |

---

## UI Config Findings

| # | Severity | File | Issue | Recommendation |
|---|----------|------|-------|----------------|
| U1 | MEDIUM | `screen-schemas.yaml` | **`consultation_list` config defined but NOT served.** The schema requires `consultation_list` (line 6: `required: [version, locale, review_screen, consultation_list]`) with `page_size`, `default_sort`, `default_status_filter`. However, the HTTP contract `ui-config.yaml` `UIConfigView` does NOT include a `consultation_list` property. This config is defined in the standalone schema but never delivered to the frontend. | Either add `consultation_list` to `UIConfigView` in `ui-config.yaml`, or remove it from `screen-schemas.yaml` if it's not needed for MVP. |
| U2 | LOW | `labels.yaml` | `additionalProperties: false` — **PASS.** Labels schema is strict with 10 required string keys and no extras allowed. Consistent with `ui-config.yaml`'s `UILabels`. | No action needed. |
| U3 | LOW | `screen-schemas.yaml` | `additionalProperties: false` everywhere — **PASS.** `review_screen`, `sections`, `SectionConfig`, `consultation_list` all properly locked down. | No action needed. |
| U4 | INFO | `ui-config.yaml` | `additionalProperties: false` on all sub-schemas — **PASS.** `UILabels`, `ReviewScreenConfig`, `SectionConfig`, `InsightCategories`, `InsightCategoryConfig`, `StatusLabels`, `FeatureFlags` all locked down. | No action needed. |

---

## Contract Inventory Gap Analysis

### Endpoints in YAML but NOT in Contract Inventory (03-contract-inventory.md)

| Endpoint | In YAML? | In Docs? | Notes |
|----------|----------|----------|-------|
| `POST /v1/auth/forgot-password` | YES (`auth.yaml`) | NO | Entire endpoint missing from inventory. Schema defines `ForgotPasswordRequest` and `GenericMessageResponse`. |
| `POST /v1/auth/confirm-forgot-password` | YES (`auth.yaml`) | NO | Entire endpoint missing from inventory. Schema defines `ConfirmForgotPasswordRequest`. |

### Endpoints in Contract Inventory but NOT in YAML

| Endpoint | In Docs? | In YAML? | Notes |
|----------|----------|----------|-------|
| `GET /v1/patients/{id}` | Implicitly expected (inventory references `PatientView` by ID) | NO | No individual patient retrieval endpoint defined. |
| `PUT/PATCH /v1/patients/{id}` | Not documented | NO | No patient update endpoint. |

### Endpoints Present in Both (Verified Consistent)

| Endpoint | YAML File | Inventory Match? |
|----------|-----------|-----------------|
| `POST /v1/auth/session` | `auth.yaml` | YES |
| `DELETE /v1/auth/session` | `auth.yaml` | YES |
| `GET /v1/me` | `auth.yaml` | YES |
| `POST /v1/patients` | `patients.yaml` | YES |
| `GET /v1/patients` | `patients.yaml` | YES |
| `POST /v1/consultations` | `consultations.yaml` | YES |
| `GET /v1/consultations` | `consultations.yaml` | YES |
| `GET /v1/consultations/{id}` | `consultations.yaml` | YES |
| `POST /v1/consultations/{id}/session/start` | `consultations.yaml` | YES |
| `POST /v1/consultations/{id}/session/end` | `consultations.yaml` | YES |
| `GET /v1/consultations/{id}/review` | `review.yaml` | YES |
| `PUT /v1/consultations/{id}/review` | `review.yaml` | YES |
| `POST /v1/consultations/{id}/finalize` | `review.yaml` | YES |
| `POST /v1/consultations/{id}/export` | `exports.yaml` | YES |
| `GET /v1/ui-config` | `ui-config.yaml` | YES |

### Error Codes: Inventory vs YAML

| Error Code | Documented in Inventory | Appears in any YAML `responses`? |
|------------|------------------------|----------------------------------|
| `validation_error` (400) | YES | Implicit via `400` responses, but code not in enum |
| `unauthorized` (401) | YES | Implicit via `401` responses, but code not in enum |
| `forbidden` (403) | YES | Implicit via `403` responses, but code not in enum |
| `not_found` (404) | YES | Implicit via `404` responses, but code not in enum |
| `conflict` (409) | YES | Implicit via `409` responses, but code not in enum |
| `plan_limit_exceeded` (403) | YES | Mentioned in `consultations.yaml` description text only |
| `trial_expired` (403) | YES | Mentioned in `consultations.yaml` description text only |
| `session_duration_exceeded` (403) | YES | NO — not referenced in any YAML |
| `feature_not_available` (403) | YES | NO — not referenced in any YAML |
| `service_unavailable` (503) | YES | NO — not in any YAML response |
| `export_expired` (410) | YES | NO — not in any YAML response |
| `internal_error` (500) | YES | NO — not in any YAML response |

---

## Pre-Investigation Verification

| Pre-Inv # | Status | Notes |
|-----------|--------|-------|
| C1 | **CONFIRMED** | `review.yaml` `GET /v1/consultations/{id}/review` — responses are 200, 401, 404. No 403 for ownership/authorization. See H1. |
| C2 | **CONFIRMED** | `review.yaml` `PUT /v1/consultations/{id}/review` — responses are 200, 400, 401, 404. No 403 for ownership/authorization. See H2. |
| C3 | **CONFIRMED** | `review.yaml` `POST /v1/consultations/{id}/finalize` — responses are 200, 401, 404, 409. No 403. See H3. |
| C4 | **CONFIRMED** | `review.yaml` `PUT /v1/consultations/{id}/review` — no 409 response. The PUT can be called when consultation is in any state; no contract enforcement of `under_physician_review` prerequisite. See H4. |
| C5 | **CONFIRMED** | `review.yaml` line 246: `UpdateReviewRequest.medical_history` has `type: object` with `additionalProperties: true`. Also confirmed in `ReviewView.medical_history.content` at line 155. See H5, H6. |
| C6 | **CONFIRMED** | `auth.yaml` `POST /v1/auth/forgot-password` — only response is 200. No 400 for invalid/missing email field. See H8. |
| C7 | **CONFIRMED** | `consultations.yaml` `GET /v1/consultations` — responses are 200, 400, 401. No 403. See H13. |
| C8 | **CONFIRMED** | `errors.yaml` line 19: `code: type: string` — bare string, no enum. The 11 error codes from the inventory are not enforced at the schema level. See H14. |
| C9 | **CONFIRMED** | `screen-schemas.yaml` requires `consultation_list` (line 6) with `page_size`, `default_sort`, `default_status_filter`. The HTTP contract `ui-config.yaml` `UIConfigView` does NOT include `consultation_list` — this config is defined but never served. See U1. |
| C10 | **CONFIRMED** | `patients.yaml` defines only `POST /v1/patients` and `GET /v1/patients`. No `GET /v1/patients/{patient_id}`, `PUT /v1/patients/{patient_id}`, or `PATCH /v1/patients/{patient_id}`. See H16. |
| C11 | **CONFIRMED (PASS)** | All endpoints across all HTTP YAML files have `operationId`. All protected endpoints have `security: - bearerAuth: []`. Public auth endpoints lack explicit `security: []` (see H10-H12) but this is a best-practice concern, not a functional failure. |
| C12 | **CONFIRMED (PASS)** | `ui-config.yaml` has `additionalProperties: false` on ALL sub-schemas: `UILabels`, `ReviewScreenConfig`, `SectionConfig`, `InsightCategories`, `InsightCategoryConfig`, `StatusLabels`, `FeatureFlags`. See U4. |

---

## Summary Statistics

| Category | Critical | High | Medium | Low | Info |
|----------|----------|------|--------|-----|------|
| HTTP Contracts | 0 | 3 | 5 | 7 | 2 |
| WebSocket Contracts | 0 | 1 | 2 | 2 | 0 |
| Feature Flags | 0 | 0 | 1 | 1 | 1 |
| UI Config | 0 | 0 | 1 | 0 | 1 |
| **Total** | **0** | **4** | **9** | **10** | **4** |

### Top Priority Fixes

1. **H1-H3 (HIGH)**: Add `403` to all three review.yaml endpoints — this is an authorization gap for medical data.
2. **W1 (HIGH)**: Define `$connect` auth schema for WebSocket — currently zero documented auth for real-time audio stream.
3. **H5-H7 (MEDIUM)**: Tighten `additionalProperties: true` on medical record schemas in review.yaml.
4. **H4 (MEDIUM)**: Add `409` to `PUT /review` for state consistency.
5. **H18 (MEDIUM)**: Add `500`/`503` responses to HTTP contracts — currently no server error shapes documented anywhere.
6. **U1 (MEDIUM)**: Resolve `consultation_list` config gap between screen-schemas.yaml and ui-config.yaml.
