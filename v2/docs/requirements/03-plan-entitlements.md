# Plan Entitlements and Authorization Matrix

## Purpose

This document defines the explicit permissions, limits, and feature access for each MVP plan type (`free_trial`, `plus`, `pro`).

This resolves Open Issue OI-002 from the task manager: "Plan entitlement differences between `free_trial`, `plus`, and `pro` are not fully defined."

---

## 1. Design Principles

- **MVP-first**: All three plans share the same core features in the MVP. Differentiation is minimal and focused on usage limits, not feature availability.
- **Backend-enforced**: Plan checks happen in the BFF and backend layers, never in the frontend.
- **Feature-flag-driven**: Plan entitlements are expressed as feature flags so that changes do not require code deploys.
- **Reversible**: The entitlement matrix can be adjusted via configuration without backend code changes.

---

## 2. MVP Plan Entitlement Matrix

| Capability | `free_trial` | `plus` | `pro` | Enforcement Point |
|-----------|-------------|--------|-------|------------------|
| Create consultation | Yes | Yes | Yes | Backend |
| Real-time audio streaming | Yes | Yes | Yes | Backend |
| Transcription (pt-BR) | Yes | Yes | Yes | Backend |
| AI-generated medical history | Yes | Yes | Yes | Backend |
| AI-generated summary | Yes | Yes | Yes | Backend |
| AI-generated insights | Yes | Yes | Yes | Backend |
| Physician review and edit | Yes | Yes | Yes | Backend |
| Finalization | Yes | Yes | Yes | Backend |
| Export to PDF | Yes | Yes | Yes | Backend |
| Monthly consultation limit | 10 | 50 | Unlimited | Backend |
| Audio retention (days) | 7 | 30 | 90 | Backend + S3 lifecycle |
| Max consultation duration (minutes) | 30 | 60 | 120 | Backend (session timer) |
| Priority support | No | No | Yes | Operational (not enforced in code) |
| Trial duration (days) | 14 | N/A | N/A | Backend |

### Notes

- **Monthly consultation limit**: The backend counts consultations created in the current calendar month. When the limit is reached, `POST /v1/consultations` returns HTTP 403 with error code `plan_limit_exceeded`.
- **Audio retention**: S3 lifecycle rules delete audio objects after the plan-specific retention period. The finalized note and artifacts are retained independently.
- **Max consultation duration**: The backend auto-ends sessions that exceed the plan limit. A warning is sent to the frontend 5 minutes before the limit via WebSocket.
- **Trial duration**: After 14 days, `free_trial` users cannot create new consultations. Existing consultations remain accessible for review and export. The BFF returns `trial_expired: true` in the user profile response.

---

## 3. Plan Lifecycle Rules

### Free Trial

| Rule | Behavior |
|------|----------|
| Activation | Automatically assigned on signup |
| Duration | 14 calendar days from account creation |
| Expiry behavior | Cannot create new consultations; existing data remains accessible |
| Upgrade path | User can upgrade to `plus` or `pro` (billing integration is post-MVP) |
| Downgrade | N/A (trial is the starting state) |

### Plus

| Rule | Behavior |
|------|----------|
| Activation | Manual assignment or upgrade from `free_trial` |
| Duration | Ongoing (subscription-based, billing post-MVP) |
| Limit enforcement | Monthly consultation count tracked and enforced |
| Downgrade | To `free_trial` limits if subscription lapses (post-MVP) |

### Pro

| Rule | Behavior |
|------|----------|
| Activation | Manual assignment or upgrade |
| Duration | Ongoing (subscription-based, billing post-MVP) |
| Limit enforcement | No consultation count limit; duration limit per session applies |
| Downgrade | To `plus` or `free_trial` limits if subscription lapses (post-MVP) |

---

## 4. Authorization Model

### Role Hierarchy (MVP)

The MVP has a simple role model:

| Role | Description | Scope |
|------|-------------|-------|
| `physician` | Primary user; owns and manages consultations | Own consultations within own clinic |
| `clinic_admin` | Administrative access to clinic configuration | Clinic-level settings (post-MVP for most features) |

### Ownership Rules

| Entity | Owner | Access Rule |
|--------|-------|------------|
| Consultation | Creating physician | Only the creating physician can review, edit, finalize, and export |
| Patient record | Clinic | All physicians in the clinic can see patients, but only consultation owner accesses consultation data |
| Clinic configuration | Clinic admin | Retention policies, clinic metadata |
| Audio artifacts | Consultation owner (physician) | Subject to clinic retention policy |
| Finalized notes | Consultation owner (physician) | Immutable after finalization; accessible to owner |

### Multi-Physician Access (Post-MVP Decision)

- **MVP**: One physician per consultation. No delegation, no shared access.
- **Post-MVP**: May introduce delegate access, supervisor review, or clinic-wide consultation visibility. These are explicitly deferred.

---

## 5. Feature Flag Configuration

Plan entitlements are backed by feature flags evaluated in the BFF layer.

| Flag Name | Type | Default | Description |
|-----------|------|---------|-------------|
| `consultation.create.enabled` | boolean | `true` | Master switch for consultation creation |
| `consultation.monthly_limit` | integer | Plan-dependent | Max consultations per calendar month |
| `consultation.max_duration_minutes` | integer | Plan-dependent | Max real-time session duration |
| `audio.retention_days` | integer | Plan-dependent | Days before audio auto-deletion |
| `export.pdf.enabled` | boolean | `true` | Whether PDF export is available |
| `trial.duration_days` | integer | `14` | Free trial duration |
| `trial.expired` | boolean | Computed | Whether the trial has expired |

### BFF Response Example

```json
{
  "user": {
    "doctor_id": "uuid",
    "name": "Dr. Example",
    "plan_type": "plus",
    "clinic_id": "uuid"
  },
  "entitlements": {
    "can_create_consultation": true,
    "consultations_remaining": 42,
    "max_duration_minutes": 60,
    "export_enabled": true,
    "trial_expired": false
  }
}
```

The frontend renders based on `entitlements` — it never computes these values itself.

---

## 6. Error Responses for Plan Violations

| Scenario | HTTP Status | Error Code | User-Facing Message (pt-BR) |
|----------|------------|------------|----------------------------|
| Monthly limit reached | 403 | `plan_limit_exceeded` | "Voce atingiu o limite de consultas do seu plano este mes." |
| Trial expired | 403 | `trial_expired` | "Seu periodo de teste expirou. Atualize seu plano para continuar." |
| Session duration exceeded | 200 (WebSocket close) | `session_duration_exceeded` | "A sessao atingiu o tempo maximo do seu plano." |
| Feature not available on plan | 403 | `feature_not_available` | "Este recurso nao esta disponivel no seu plano atual." |

---

## 7. Open Decisions (Deferred to Post-MVP)

| Decision | Current Status | Impact |
|----------|---------------|--------|
| Billing integration (Stripe or similar) | Deferred | Plan upgrades/downgrades are manual in MVP |
| Proration and mid-cycle upgrades | Deferred | Not relevant until billing exists |
| Clinic-level plan vs doctor-level plan | Doctor-level for MVP | May change when multi-physician clinics are common |
| Consultation rollover (unused quota) | No rollover in MVP | Simplest implementation |
| Grace period after trial expiry | None in MVP | Trial ends hard on day 14 |
