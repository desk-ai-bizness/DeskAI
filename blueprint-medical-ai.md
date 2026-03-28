# Blueprint: AI-Powered Medical Consultation Scribe

> **Version:** 1.0
> **Date:** 2026-03-25
> **Author:** Daniel Toni
> **Status:** Planning / Pre-MVP

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision](#2-product-vision)
3. [Market Analysis — Brazil](#3-market-analysis--brazil)
4. [Competitive Landscape](#4-competitive-landscape)
5. [Product Form Factors](#5-product-form-factors)
6. [System Architecture](#6-system-architecture)
7. [Tech Stack](#7-tech-stack)
8. [AI Pipeline — Detailed](#8-ai-pipeline--detailed)
9. [Data Model](#9-data-model)
10. [JSON Summary Schema](#10-json-summary-schema)
11. [Infrastructure](#11-infrastructure)
12. [Build Phases & Timeline](#12-build-phases--timeline)
13. [Cost Analysis](#13-cost-analysis)
14. [Revenue Model](#14-revenue-model)
15. [Risks & Mitigations](#15-risks--mitigations)
16. [Future Roadmap](#16-future-roadmap)

---

## 1. Executive Summary

A generative AI-powered service that acts as a **smart medical scribe** — it listens to doctor-patient consultations, transcribes the audio with speaker labels, generates a structured summary of everything discussed, and stores it in a database for the doctor to review and approve.

**What it is:** A documentation tool that observes and organizes.
**What it is NOT:** An AI doctor. It does not diagnose, interpret symptoms, suggest ICD-10 codes, or make any clinical decisions.

This distinction is critical — it eliminates FDA/ANVISA medical device classification risk and removes clinical liability from the product.

### Core Pipeline

```
Doctor talks to patient
        |
Audio is captured (phone or browser)
        |
Transcription with speaker diarization (who said what)
        |
AI generates structured summary (what was discussed, not what it means)
        |
Doctor reviews, edits, and approves
        |
Stored in database, accessible for future patient history
```

---

## 2. Product Vision

### Problem

- Brazilian physicians spend ~50% of consultation time on documentation
- Over 25 hours/week are lost to filling out medical records
- Only 8% of Brazilian healthcare institutions have EHR systems — many still use paper
- 88% of clinics report staff resistance to new technology
- The divide between patient attention and screen/paperwork reduces care quality

### Solution

A zero-friction tool: phone on the desk (or browser tab open), one tap to start, one tap to stop. The AI does the rest. The doctor reviews and approves the summary later — on phone, tablet, or computer.

### Design Principles

1. **Report, never interpret** — the AI summarizes what was said, never what it means
2. **Doctor always in control** — every summary requires human review and approval before it's saved
3. **Zero learning curve** — if a doctor can press a button, they can use this product
4. **Works on any device** — phone, tablet, computer, any browser
5. **Portuguese-first** — built for Brazilian medical vocabulary and documentation standards

---

## 3. Market Analysis — Brazil

### Key Statistics

| Metric | Value | Source |
|--------|-------|--------|
| Active physicians in Brazil | ~500,000 | CFM |
| EHR penetration rate | ~8% of healthcare institutions | Black Book Research |
| Institutions offering telemedicine | 68% | Panorama das Clinicas 2025 |
| ROI on AI in healthcare | 22% | KPMG 2025 |
| Administrative cost savings from AI | 15-25% | Brazilian hospital reports |
| EHR market size (Brazil, 2025) | ~$670M - $1.5B | Multiple estimates |
| EHR market projected (2030) | $1.1B - $2.76B | CAGR 5-17.5% |

### How Doctors Work Today

- **Devices:** Computer, tablet, and smartphone used interchangeably. Cloud-based EHR systems can be accessed from any device with internet
- **EHR systems (when present):** MV Sistemas (68% market), Philips Tasy (63%), Totvs (57%), Oracle Cerner (49%)
- **Documentation:** Mix of typed notes, dictation, handwritten records. AI voice-to-record is the fastest-growing adoption category
- **Telemedicine:** Growing rapidly (68% adoption), creates natural opportunity for audio capture from video calls
- **Pain point:** Documentation takes 7+ minutes per consultation; AI tools reduce this to ~2 minutes (71% reduction reported by Sofya/Oracle)

### Opportunity

Brazil concentrates two-thirds of Latin America's healthtechs. The market is large, growing, and underserved — especially in small clinics and solo practitioners who can't afford enterprise solutions like MV or Philips Tasy.

---

## 4. Competitive Landscape

### Brazilian Competitors

| Company | Stage | Traction | Differentiator |
|---------|-------|----------|----------------|
| **Voa Health** | Seed ($3M from Prosus) | 20K+ doctors, 600+ paying, 80K monthly consultations, R$2.5M ARR | Market leader, 100% Portuguese, founded by physicians |
| **DoctorAssistant.ai** | Early | Growing | ReSOAP methodology, integrates with GoClin/Amplimed/iMedicina |
| **Dr. Scriba** | Active | Unknown | Real-time transcription, template customization, hospital integration |
| **Sofya** | Growth (Oracle-backed) | 500K monthly consultations target | 71% documentation time reduction, enterprise focus |
| **MV med.ai** | Enterprise | Largest EHR in Brazil | Part of existing MV ecosystem, medication suggestions |
| **Doctorflow** | Active | Unknown | Custom anamnesis templates, end-to-end encryption |
| **Vita365** | Active | Unknown | Trained on anonymized Brazilian hospital data |
| **Integrativ.ai** | Active | Unknown | PubMed integration, protocol recommendations |
| **evalmind Care** | Active | Unknown | Real-time insights, exam recommendations |
| **CTC Tech** | Enterprise | Top 150 IT company | GPT-4 powered, enterprise hospital focus |

### Global Competitors (Not Yet in Brazil or English-Only)

| Company | Pricing | Notes |
|---------|---------|-------|
| Nuance DAX (Microsoft) | $1,000+/month/doctor | Enterprise only, English-focused |
| Abridge | Enterprise pricing | US hospital focus |
| DeepScribe | ~$400/month/doctor | Specialty-focused |
| Freed | $99-199/month/doctor | Fast-growing, US market |
| Nabla | Enterprise | European market |

### Competitive Positioning Options

| Strategy | How |
|----------|-----|
| **Price** | Undercut Voa's premium pricing with a simpler, cheaper product for solo practitioners |
| **Specialty niche** | Build specifically for one specialty (dermatology, psychiatry, pediatrics) — generic tools serve everyone, no one perfectly |
| **EHR integration** | Deep integration with a specific EHR that others don't support well |
| **Small clinic focus** | Most competitors target medium/large clinics. 1-3 doctor offices are underserved |
| **API-first** | Sell the engine, not the app — let clinics embed the API into their existing workflow |
| **Geographic expansion** | Portuguese-speaking markets: Portugal has virtually no competition |
| **Generalist-to-specialist** | Start general, then specialize in domains (legal, therapy, finance) beyond healthcare |

---

## 5. Product Form Factors

### Audio Capture Methods

```
+--------------+--------------+--------------+------------+
|  Mobile App  |  Web App     |  Desktop     |  Tele-     |
|              |  (Browser)   |  Agent       |  medicine  |
+--------------+--------------+--------------+------------+
| Phone on     | Browser tab  | Background   | Captures   |
| desk records | open during  | app captures | audio from |
| ambient      | consultation | system audio | video call |
| audio        |              |              |            |
+--------------+--------------+--------------+------------+
| MVP: YES     | MVP: YES     | Phase 2+     | Phase 2+   |
| (easiest     | (most        | (needs OS    | (needs API |
|  adoption)   |  powerful)   |  permissions)|  integr.)  |
+--------------+--------------+--------------+------------+
```

### MVP: Mobile App + Web App

**Mobile App (React Native):**
- Phone sits on doctor's desk
- One-tap start/stop recording
- Push notification when summary is ready
- Review and approve on phone
- **This is the killer feature** — lowest friction, no extra hardware

**Web App (Next.js):**
- Works on any device with a browser
- Full dashboard: consultations, patient history, settings
- Review/edit summaries with side-by-side transcript view
- Admin features for clinic management

---

## 6. System Architecture

### High-Level Overview

```
+--------------------------------------------------------------+
|                        CLIENT LAYER                           |
|                                                               |
|   +-------------+    +-------------+    +-------------+      |
|   | Mobile App  |    |  Web App    |    | Future:     |      |
|   | (React      |    | (React /   |    | Desktop,    |      |
|   |  Native)    |    |  Next.js)  |    | Plugins     |      |
|   +------+------+    +------+-----+    +-------------+      |
|          |                  |                                 |
|          +--------+---------+                                 |
|                   | Audio Stream / File Upload                |
+-------------------+-------------------------------------------+
                    |
                    v
+--------------------------------------------------------------+
|                      API GATEWAY                              |
|           (Authentication, Rate Limiting, Routing)            |
|                                                               |
|   +--------------------------------------------------------+ |
|   | Auth: JWT + Refresh Tokens    Rate Limit: per doctor    | |
|   | Routes: /consultations, /patients, /audio, /summaries   | |
|   +--------------------------------------------------------+ |
+-------------------+-------------------------------------------+
                    |
                    v
+--------------------------------------------------------------+
|                    BACKEND SERVICES                            |
|                                                               |
|  +----------------+  +----------------+  +----------------+  |
|  | Consultation   |  |   Audio        |  |  Patient       |  |
|  | Service        |  |   Service      |  |  Service       |  |
|  |                |  |                |  |                |  |
|  | - CRUD consults|  | - Upload audio |  | - Patient CRUD |  |
|  | - Status mgmt  |  | - Chunk large  |  | - History view |  |
|  | - Doctor review|  |   files        |  | - Search       |  |
|  | - Export/share |  | - Trigger ASR  |  |                |  |
|  +-------+--------+  +-------+--------+  +----------------+  |
|          |                    |                                |
+----------+--------------------+--------------------------------+
           |                    |
           |                    v
           |   +--------------------------------------------+
           |   |         AI PIPELINE (async)                 |
           |   |                                             |
           |   |  +----------+    +----------+              |
           |   |  | 1. ASR   |--->| 2. LLM   |              |
           |   |  | Deepgram |    | Claude   |              |
           |   |  |          |    | API      |              |
           |   |  | Audio -->|    |          |              |
           |   |  | Transcript    | Transcript              |
           |   |  | + Speaker|    | --> JSON  |              |
           |   |  | Labels   |    | Summary   |             |
           |   |  +----------+    +----------+              |
           |   |                       |                     |
           |   |                       v                     |
           |   |              +--------------+              |
           |   |              | 3. Post-     |              |
           |   |              | Processing   |              |
           |   |              |              |              |
           |   |              | - Validate   |              |
           |   |              |   JSON       |              |
           |   |              | - Confidence |              |
           |   |              |   scores     |              |
           |   |              | - Link to    |              |
           |   |              |   transcript |              |
           |   |              +--------------+              |
           |   +--------------------------------------------+
           |
           v
+--------------------------------------------------------------+
|                       DATA LAYER                              |
|                                                               |
|  +--------------+  +--------------+  +--------------+        |
|  | PostgreSQL   |  | Object       |  | Redis        |        |
|  |              |  | Storage (S3) |  |              |        |
|  | - Users      |  |              |  | - Sessions   |        |
|  | - Patients   |  | - Audio files|  | - Cache      |        |
|  | - Consults   |  | - Transcripts|  | - Rate limits|        |
|  | - Summaries  |  |              |  | - Job queue  |        |
|  |   (JSONB)    |  |              |  |   status     |        |
|  +--------------+  +--------------+  +--------------+        |
|                                                               |
+--------------------------------------------------------------+
```

### Request Flow (Happy Path)

```
1. Doctor opens app, selects patient, taps "Record"
2. Audio streams / records locally on device
3. Doctor taps "Stop" -> audio file uploaded to S3 (chunked if large)
4. Backend creates consultation record (status: "processing")
5. Background worker picks up job from queue
6. Worker sends audio to Deepgram -> gets speaker-labeled transcript
7. Worker sends transcript to Claude API -> gets structured JSON summary
8. Worker runs post-processing (validation, confidence scores, PII detection)
9. Worker stores results in Postgres (status: "pending_review")
10. Push notification sent to doctor: "Summary ready for review"
11. Doctor opens summary, reviews, edits if needed
12. Doctor taps "Approve" (status: "approved")
13. Summary permanently stored, linked to patient history
```

---

## 7. Tech Stack

### Core Stack

| Layer | Technology | Rationale |
|-------|-----------|----------|
| **Mobile** | React Native (Expo) | Single codebase iOS + Android, fast iteration, huge ecosystem |
| **Web Frontend** | Next.js (React) | SSR for marketing pages, fast dashboard, shares components with mobile |
| **Backend** | Python (FastAPI) | Best AI/ML library ecosystem, async support, fast to build, easy to hire |
| **Database** | PostgreSQL + JSONB | Structured data (users, patients) + flexible JSON (summaries). Single DB |
| **Object Storage** | AWS S3 | Audio files. Cheap, durable, encrypted at rest |
| **Cache / Queue** | Redis | Session management + async job status tracking |
| **Task Queue** | Celery + Redis | Audio processing is async — doctor uploads, gets notified when ready |
| **Auth** | Auth0 or Clerk | Don't build auth. OAuth2 + MFA out of the box |
| **CI/CD** | GitHub Actions | Free for small teams, integrates with everything |
| **Monitoring** | Sentry (errors) + CloudWatch (infra) | Know when things break before doctors tell you |

### AI Services

| Service | Provider | Purpose | Cost |
|---------|----------|---------|------|
| **ASR (Speech-to-Text)** | Deepgram (Nova-2 Medical) | Transcription with speaker diarization, medical Portuguese | ~$0.0059/min |
| **LLM (Summarization)** | Claude API (Anthropic) | Structured summary generation from transcripts | ~$0.01-0.05/consultation |
| **Backup ASR** | AWS Transcribe Medical | Fallback if Deepgram is down | ~$0.024/min |

### Why These Choices

**Deepgram over Whisper:**
- Deepgram Nova-2 Medical is purpose-built for medical vocabulary
- Built-in speaker diarization (Whisper needs a separate pipeline for this)
- Real-time streaming support (future feature)
- Better at Brazilian Portuguese medical terms
- API-based — no GPU infrastructure to manage

**Claude over GPT:**
- Structured output mode produces reliable JSON
- 200K token context window fits any consultation transcript
- Excellent Portuguese language quality
- Strong instruction following (critical for "report only, never diagnose")

**FastAPI over Node.js:**
- Python has the best AI/ML ecosystem (httpx, anthropic SDK, etc.)
- Async by default — handles concurrent audio processing well
- Type hints + Pydantic for request/response validation
- FastAPI auto-generates OpenAPI docs

**PostgreSQL with JSONB over separate document store:**
- One database to manage, not two
- JSONB supports indexing and querying inside JSON documents
- Relational for structured data (users, patients, clinics)
- Flexible for evolving summary schemas
- GIN indexes for full-text search inside summaries

---

## 8. AI Pipeline — Detailed

### Step 1: Audio Capture & Upload

**Audio Specifications:**
- Format: OPUS (10x smaller than WAV) or WAV
- Sample rate: 16kHz minimum (phone mics do 44.1kHz — more than enough)
- Max duration: 60 minutes (covers any consultation)
- Chunked upload: split files >25MB into 5MB chunks
- Upload target: S3 via presigned URL (never through your backend)

**Upload Flow:**
```
Client generates upload request -> Backend returns presigned S3 URL
Client uploads directly to S3 -> S3 triggers event notification
Backend picks up event -> Creates job in queue
```

### Step 2: Transcription (ASR)

```python
import httpx

async def transcribe(audio_url: str) -> dict:
    """Send audio to Deepgram for transcription with speaker diarization."""
    response = await httpx.post(
        "https://api.deepgram.com/v1/listen",
        headers={"Authorization": f"Token {DEEPGRAM_KEY}"},
        json={"url": audio_url},  # S3 presigned URL
        params={
            "model": "nova-2-medical",
            "language": "pt-BR",
            "diarize": True,        # Speaker separation
            "punctuate": True,
            "paragraphs": True,
            "smart_format": True,
            "utterances": True,     # Speaker-labeled segments
        }
    )
    return response.json()
```

**Output Example:**
```json
{
  "utterances": [
    {
      "speaker": 0,
      "start": 0.5,
      "end": 4.2,
      "text": "Bom dia, o que te traz aqui hoje?"
    },
    {
      "speaker": 1,
      "start": 4.5,
      "end": 12.1,
      "text": "Doutor, estou com dor de cabeca ha duas semanas..."
    }
  ]
}
```

### Step 3: Summarization (LLM)

```python
import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a medical consultation scribe for Brazilian physicians.
Your job is to organize what was discussed into a structured summary.

CRITICAL RULES:
- Report ONLY what was explicitly said. Never interpret, diagnose, or infer.
- Use the exact medical terms the doctor used.
- If something is unclear in the transcript, mark it as [inaudivel].
- Speaker 0 is the Doctor, Speaker 1 is the Patient (unless context says otherwise).
- Write in Brazilian Portuguese.
- Output valid JSON matching the provided schema."""

async def summarize(transcript: str, schema: dict) -> dict:
    """Send transcript to Claude for structured summarization."""
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Transcript of consultation:

{transcript}

Generate a structured summary following this exact JSON schema:
{json.dumps(schema, indent=2)}"""
            }
        ],
    )
    return json.loads(response.content[0].text)
```

### Step 4: Post-Processing

```
Raw LLM Output
      |
      v
+-------------------+
| JSON Validation   | -- Does schema match expected structure?
+--------+----------+
         |
         v
+-------------------+
| Source Linking     | -- Each summary point maps to transcript timestamps
+--------+----------+
         |
         v
+-------------------+
| Confidence Score  | -- Flag low-confidence sections (unclear audio, ambiguous)
+--------+----------+
         |
         v
+-------------------+
| PII Detection     | -- Flag/redact CPF, phone numbers in transcript
+--------+----------+
         |
         v
   Store in database
   Status: "pending_review"
   Notify doctor
```

---

## 9. Data Model

### SQL Schema

```sql
-- =============================================
-- CORE ENTITIES
-- =============================================

CREATE TABLE clinics (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    cnpj          TEXT UNIQUE,
    plan          TEXT NOT NULL DEFAULT 'trial',  -- trial, basic, pro
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE doctors (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id     UUID REFERENCES clinics(id),
    name          TEXT NOT NULL,
    crm           TEXT NOT NULL,            -- CRM number (Brazilian medical license)
    crm_state     TEXT NOT NULL,            -- UF (SP, RJ, MG...)
    email         TEXT UNIQUE NOT NULL,
    specialty     TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE patients (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id     UUID REFERENCES clinics(id),
    name          TEXT NOT NULL,
    cpf           TEXT,                     -- Encrypted at rest
    birth_date    DATE,
    phone         TEXT,
    created_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(clinic_id, cpf)
);

-- =============================================
-- CONSULTATION FLOW
-- =============================================

CREATE TABLE consultations (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id             UUID REFERENCES doctors(id) NOT NULL,
    patient_id            UUID REFERENCES patients(id),  -- nullable: can add patient later
    clinic_id             UUID REFERENCES clinics(id) NOT NULL,

    -- Audio
    audio_s3_key          TEXT,
    audio_duration_seconds INTEGER,

    -- Transcript
    transcript            JSONB,             -- Full speaker-labeled transcript

    -- AI Summary
    summary               JSONB,             -- Structured summary (see JSON schema section)

    -- Status workflow
    -- recording -> processing -> pending_review -> approved -> archived
    status                TEXT NOT NULL DEFAULT 'recording',

    -- Metadata
    consultation_date     TIMESTAMPTZ DEFAULT now(),
    approved_at           TIMESTAMPTZ,
    doctor_edits          JSONB,             -- Track what the doctor changed
    created_at            TIMESTAMPTZ DEFAULT now(),
    updated_at            TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX idx_consultations_doctor
    ON consultations(doctor_id, consultation_date DESC);

CREATE INDEX idx_consultations_patient
    ON consultations(patient_id, consultation_date DESC);

CREATE INDEX idx_consultations_status
    ON consultations(status);

CREATE INDEX idx_consultations_summary
    ON consultations USING GIN (summary);    -- Search inside JSON

-- =============================================
-- AUDIT TRAIL (LGPD requirement)
-- =============================================

CREATE TABLE audit_log (
    id            BIGSERIAL PRIMARY KEY,
    actor_id      UUID NOT NULL,            -- doctor or admin
    action        TEXT NOT NULL,             -- view, edit, approve, export, delete
    resource_type TEXT NOT NULL,             -- consultation, patient, transcript
    resource_id   UUID NOT NULL,
    metadata      JSONB,
    ip_address    INET,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_actor
    ON audit_log(actor_id, created_at DESC);

CREATE INDEX idx_audit_resource
    ON audit_log(resource_type, resource_id);
```

### Status Workflow

```
recording --> processing --> pending_review --> approved --> archived
    |              |               |                           |
    |              |               +-- doctor edits/rejects    |
    |              |                   (back to pending_review)|
    |              |                                           |
    |              +-- on failure: "error"                     |
    |                  (retry or manual intervention)          |
    |                                                          |
    +-- doctor cancels recording (deleted)                     |
                                                               |
                                            archived after N days
                                            or by doctor action
```

---

## 10. JSON Summary Schema

This is what lives in `consultations.summary` (JSONB column):

```json
{
  "version": "1.0",
  "language": "pt-BR",
  "reason_for_visit": "Paciente relata dores de cabeca persistentes ha duas semanas",
  "symptoms_reported": [
    {
      "description": "Dor de cabeca que comeca pela manha",
      "duration": "2 semanas",
      "severity": "6/10",
      "transcript_ref": { "start": 4.5, "end": 12.1 }
    },
    {
      "description": "Sem melhora com ibuprofeno",
      "duration": null,
      "severity": null,
      "transcript_ref": { "start": 15.3, "end": 19.7 }
    }
  ],
  "patient_history_mentioned": [
    {
      "description": "Historico familiar de enxaqueca (mae)",
      "transcript_ref": { "start": 45.2, "end": 52.8 }
    }
  ],
  "current_medications": [
    {
      "name": "Ibuprofeno 400mg",
      "usage": "conforme necessidade",
      "patient_reported_effectiveness": "sem melhora"
    }
  ],
  "medications_discussed": [
    {
      "name": "Sumatriptano",
      "context": "Medico sugeriu como alternativa",
      "transcript_ref": { "start": 120.5, "end": 135.2 }
    }
  ],
  "exams_ordered": [
    "Hemograma completo",
    "Ressonancia magnetica (se sem melhora em 2 semanas)"
  ],
  "doctor_instructions": [
    "Manter diario de dor de cabeca",
    "Reduzir tempo de tela antes de dormir",
    "Retornar se sintomas piorarem subitamente"
  ],
  "next_steps": [
    "Retorno agendado em 2 semanas",
    "Encaminhamento para RM se persistir"
  ],
  "flags": [
    {
      "type": "unclear_audio",
      "description": "Trecho inaudivel entre 3:42 e 3:48",
      "transcript_ref": { "start": 222.0, "end": 228.0 }
    }
  ],
  "confidence_score": 0.92
}
```

### Design Notes

- **`transcript_ref`**: Links each summary point back to the exact timestamp in the audio/transcript. Allows the doctor to click on a summary item and hear/read the original.
- **`confidence_score`**: Overall confidence (0.0-1.0). Sections with unclear audio, overlapping speech, or ambiguous content reduce the score.
- **`flags`**: Explicitly marks anything the AI is uncertain about. The doctor knows exactly what to double-check.
- **`version`**: Schema versioning for backward compatibility as the summary format evolves.
- **No clinical interpretation**: No ICD codes, no differential diagnoses, no risk assessments. Just what was said.

---

## 11. Infrastructure

### Production Architecture (AWS sa-east-1 — Sao Paulo)

```
+-------------------------------------------------------------+
|                  AWS sa-east-1 (Sao Paulo)                   |
|                                                              |
|  +--------------+     +---------------------------------+    |
|  | CloudFront   |---->| S3 Bucket (static frontend)     |    |
|  | CDN          |     | + S3 Bucket (audio files,       |    |
|  +--------------+     |   encrypted SSE-S3)             |    |
|                       +---------------------------------+    |
|                                                              |
|  +--------------+     +--------------+                       |
|  | ALB          |---->| ECS Fargate  | (API containers)      |
|  | (HTTPS only) |     | or App       |                       |
|  +--------------+     | Runner       |                       |
|                       +------+-------+                       |
|                              |                               |
|           +------------------+------------------+            |
|           v                  v                  v            |
|  +--------------+  +--------------+  +--------------+        |
|  | RDS Postgres |  | ElastiCache  |  | SQS          |        |
|  | (encrypted)  |  | (Redis)      |  | (job queue)  |        |
|  +--------------+  +--------------+  +--------------+        |
|                                                              |
|  +--------------+                                            |
|  | CloudWatch   | (logs, metrics, alarms)                    |
|  +--------------+                                            |
+--------------------------------------------------------------+

External APIs:
  +-- Deepgram API (ASR) -- audio sent via presigned S3 URL
  +-- Claude API (Anthropic) -- transcript sent for summarization
  +-- Auth0 / Clerk -- authentication
```

### MVP Simplification (Use This First)

You don't need full AWS on day one. Start cheaper, migrate when you have paying customers:

| Production (Later) | MVP Alternative | Monthly Cost |
|--------------------|-----------------|-------------|
| ECS Fargate | **Railway or Render** (deploy from GitHub) | ~$20-50 |
| RDS Postgres | **Supabase** (managed Postgres + auth + storage) | Free -> $25 |
| S3 + CloudFront | **Supabase Storage** or **Cloudflare R2** | ~$5-10 |
| ElastiCache Redis | **Upstash Redis** (serverless) | Free -> $10 |
| SQS | **BullMQ on Railway** or background workers | Included |
| CloudWatch | **Sentry** (free tier) | Free |

**MVP monthly infrastructure cost: $50-100/month**

### Data Residency

All data must stay in Brazil (LGPD). AWS sa-east-1 (Sao Paulo) satisfies this. For the MVP, verify that Supabase/Railway have a Sao Paulo or South American region.

**External API consideration:** Audio is sent to Deepgram (US-based) and transcripts to Anthropic (US-based) for processing. For LGPD compliance:
- Audio/transcripts are processed transiently (not stored by the provider)
- Verify data processing agreements (DPA) with both providers
- Consider this a risk to address before scaling, not before MVP

---

## 12. Build Phases & Timeline

### Phase 0 — Validate the AI (Week 1-2)

**Goal:** Prove the AI output is useful before building anything.

**Steps:**
1. Record 3-5 mock consultations (you + a friend roleplaying doctor/patient)
2. Run audio through Deepgram API (curl or Python script) -> check transcript quality
3. Feed transcript to Claude with a well-crafted prompt -> check summary quality
4. Show outputs to 2-3 physicians -> get honest feedback
5. **Kill/pivot decision:** If physicians say "this is useless without X," you know what to build

**Deliverable:** A Python script (~200 lines) that takes an audio file and outputs a JSON summary.

**Cost:** ~$10 in API calls.

### Phase 1 — Backend API (Week 3-4)

**API Endpoints:**
```
POST   /auth/login
POST   /auth/register

POST   /consultations              <- create new, get upload URL
POST   /consultations/:id/audio    <- upload audio (presigned URL)
GET    /consultations/:id          <- get consultation + summary
PATCH  /consultations/:id          <- doctor edits summary
POST   /consultations/:id/approve  <- doctor approves
GET    /consultations              <- list (with filters)

POST   /patients                   <- create patient
GET    /patients/:id/history       <- all consultations for patient
GET    /patients                   <- search patients
```

**Background Worker:**
```
Listens to job queue
  -> Downloads audio from S3
  -> Calls Deepgram -> gets transcript
  -> Calls Claude -> gets summary
  -> Stores results in Postgres
  -> Notifies doctor (websocket or push notification)
```

**Deliverable:** Working API, deployed on Railway/Render, with async AI pipeline.

### Phase 2 — Web App (Week 5-6)

**Pages:**

| Page | Purpose |
|------|--------|
| **Login** | Email + password, CRM verification |
| **Dashboard** | Today's consultations, pending reviews, recent activity |
| **New Consultation** | Select patient (or create new), tap record, tap stop, auto-uploads |
| **Review Summary** | AI summary side-by-side with transcript. Doctor can edit each field. Approve button |
| **Patient History** | All past consultations for a patient, searchable |
| **Settings** | Profile, notification preferences, clinic management |

**Deliverable:** Functional web app. Not beautiful — functional.

### Phase 3 — Mobile App (Week 7-8)

React Native (Expo). Mirrors the web app, optimized for the primary use case:

```
Phone sits on doctor's desk
  -> Doctor opens app, selects patient
  -> Taps big green "Record" button
  -> Consultation happens normally
  -> Doctor taps "Stop"
  -> "Processing... we'll notify you when ready"
  -> Push notification: "Summary ready for review"
  -> Doctor reviews on phone or computer later
```

**Deliverable:** iOS + Android app with recording and review flow.

### Phase 4 — Polish & Pilot (Week 9-12)

- Onboard 3-5 doctors for free pilot
- Collect feedback aggressively (weekly calls)
- Fix the top 3 complaints
- Add basic analytics (consultations/day, avg processing time, edit rate)
- Harden error handling (what happens when Deepgram is down? when audio is corrupted?)
- Start charging

**Deliverable:** Stable product with real users and revenue.

### Phase 5 — Scale & Compliance (Month 4-6)

- LGPD compliance audit
- Migrate to AWS sa-east-1 if needed
- BAA / DPA with Deepgram, Anthropic
- EHR integration exploration (start with 1 system)
- Marketing site, onboarding flow, self-service signup
- Billing system (Stripe)

---

## 13. Cost Analysis

### Development Phase (Months 1-3)

| Item | Cost |
|------|------|
| Infrastructure (Railway/Supabase/Upstash) | ~$50-100/month |
| Deepgram API (testing — ~50 hours of audio) | ~$18 |
| Claude API (testing — ~500 summaries) | ~$25 |
| Apple Developer Account (for iOS) | $99/year |
| Google Play Developer (for Android) | $25 one-time |
| Domain + DNS | ~$15/year |
| **Total to working MVP** | **~$500** |

### Production Phase (Per-Consultation Economics)

| Item | Per Consultation | Per Doctor/Day (20 patients) | Per Doctor/Month (22 days) |
|------|-----------------|------------------------------|----------------------------|
| Deepgram (~15 min audio) | $0.09 | $1.80 | $39.60 |
| Claude (Sonnet, ~3K tokens) | $0.02 | $0.40 | $8.80 |
| Infrastructure (amortized) | $0.01 | $0.20 | $4.40 |
| **Total cost** | **$0.12** | **$2.40** | **$52.80** |

### Cost at Scale

| Doctors | Consultations/month | Monthly API Cost | Monthly Infra | Total Cost |
|---------|--------------------:|----------------:|--------------:|-----------:|
| 10 | 4,400 | $484 | $100 | $584 |
| 50 | 22,000 | $2,420 | $300 | $2,720 |
| 100 | 44,000 | $4,840 | $500 | $5,340 |
| 500 | 220,000 | $24,200 | $2,000 | $26,200 |

---

## 14. Revenue Model

### Pricing Strategy

Human medical scribes cost clinics **R$25-45/hour**. A doctor sees ~20 patients/day, each consultation ~15-20 min. That's ~6 hours of scribe work per doctor per day.

| Plan | Price (BRL/month/doctor) | Target |
|------|------------------------:|--------|
| **Basic** | R$199 | Solo practitioners |
| **Pro** | R$349 | Small clinics (2-10 doctors) |
| **Enterprise** | Custom | Hospitals, large networks |

All plans: unlimited consultations, web + mobile, patient history, export.
Pro adds: clinic-wide analytics, admin dashboard, priority support.
Enterprise adds: EHR integration, dedicated support, SLA, custom deployment.

### Unit Economics

At R$349/month per doctor:

| Metric | Value |
|--------|------:|
| Revenue per doctor/month | R$349 |
| Cost per doctor/month (API + infra) | ~R$280 (~$52) |
| Gross margin | ~20% at start |
| At 100 doctors | R$34,900/month revenue |
| At 500 doctors | R$174,500/month revenue |

**Note:** Margins improve significantly at scale because infrastructure costs are largely fixed. API costs per consultation decrease as you negotiate volume discounts with Deepgram and Anthropic.

### Revenue Milestones

| Milestone | Doctors | Monthly Revenue (BRL) | Timeline |
|-----------|---------|---------------------:|----------|
| Ramen profitable | 20 | R$6,980 | Month 4-6 |
| Small team (3 people) | 100 | R$34,900 | Month 8-12 |
| Seed-fundable | 500 | R$174,500 | Month 12-18 |

---

## 15. Risks & Mitigations

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| **Poor transcription quality** (background noise, accents, medical jargon) | High — useless output | Medium | Use medical-specific ASR (Deepgram Medical). Preprocessing: noise reduction. Fallback to AWS Transcribe Medical |
| **LLM hallucination** (AI invents details not in transcript) | High — trust destroyed | Medium | Strong system prompt ("report only what was said"). Post-processing validation. Source linking (every claim maps to transcript). Doctor review required |
| **Audio quality in real clinics** (monitors, HVAC, other patients) | Medium | High | Test with real clinic audio early (Phase 0). Recommend phone placement. Consider directional microphone accessory |
| **Deepgram/Anthropic API downtime** | Medium — service unavailable | Low | Queue-based architecture: jobs retry automatically. Store audio first, process later. Consider multi-provider fallback |
| **Scaling async pipeline** | Medium — slow processing | Low (initially) | Celery with auto-scaling workers. Process in parallel. Optimize prompt to reduce token count |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| **Competition** (Voa Health, etc.) | High | Certain | Differentiate on price, niche, or distribution. Move fast. Be closer to your customers |
| **Doctor adoption resistance** | High | High (88% report resistance to new tech) | Dead-simple UX. Free pilot. Prove time savings in the first week |
| **LGPD non-compliance** | High — fines, shutdown | Medium | Build audit trail from day one. Encrypt everything. Get legal review before scaling |
| **Pricing pressure** | Medium — thin margins | Medium | Negotiate volume discounts with API providers. Build proprietary ASR model long-term |
| **Key person risk** (solo founder) | High | If solo | Document everything. Use managed services. Consider a technical co-founder |

### Regulatory Risks (Low for This Product)

| Risk | Assessment |
|------|----------|
| **FDA / ANVISA medical device classification** | **Low** — this is a documentation tool, not clinical decision support. It does not diagnose, suggest treatments, or interpret data |
| **LGPD** | **Must comply** — patient data is sensitive. Encryption, audit trails, consent, data portability all required |
| **CFM (Conselho Federal de Medicina) rules** | **Must verify** — electronic medical records have specific requirements under Lei 13.787/2018. The doctor's review/approval step is critical |
| **Data breach liability** | **Must address** — have an incident response plan. Encryption at rest and in transit. Minimize data retention |

---

## 16. Future Roadmap

### Near-Term (Months 4-8)

- [ ] EHR integration (start with MV Sistemas — 68% market share)
- [ ] Real-time transcription (streaming mode — see transcript as consultation happens)
- [ ] Custom summary templates per specialty
- [ ] Multi-language support (start with Spanish for LATAM expansion)
- [ ] Clinic-wide analytics dashboard

### Medium-Term (Months 8-14)

- [ ] Desktop agent (background app that captures system audio — for telemedicine)
- [ ] Telemedicine platform integration (capture audio from video calls)
- [ ] Offline mode (record audio offline, sync and process when connected)
- [ ] Patient-facing summary (simplified version the patient can take home)
- [ ] API-as-a-service (let other healthtechs embed your pipeline)

### Long-Term (Year 2+)

- [ ] Proprietary ASR model (fine-tuned on Brazilian medical Portuguese — reduce dependency on Deepgram)
- [ ] Specialty-specific AI models (dermatology, psychiatry, pediatrics — each gets domain-optimized summaries)
- [ ] Expand beyond healthcare: legal consultations, therapy sessions, financial advisory
- [ ] Geographic expansion: Portugal, Spanish-speaking LATAM
- [ ] ICD-10 code suggestions (when regulatory path is clear and accuracy is validated)
- [ ] Patient timeline: aggregate all consultations into a chronological health narrative

---

## Appendix A: Key Decision Log

| Decision | Chosen | Rationale |
|----------|--------|----------|
| No ICD-10 codes in MVP | Yes | Eliminates FDA/ANVISA risk, clinical liability, and the hardest technical challenge |
| No clinical interpretation | Yes | "Report, never interpret" — keeps the product as a documentation tool, not a medical device |
| Mobile + Web (not desktop) | Yes | Covers 90%+ of use cases. Desktop agent adds complexity (OS permissions, audio routing) |
| Deepgram over Whisper | Yes | Medical model, built-in diarization, API-based (no GPU infrastructure) |
| Claude over GPT | Yes | Better structured output, longer context, excellent Portuguese |
| PostgreSQL + JSONB over MongoDB | Yes | One database, relational + flexible JSON, better tooling, GIN indexes for search |
| Python/FastAPI over Node.js | Yes | Better AI/ML ecosystem, async native, type safety with Pydantic |
| Start on Railway/Supabase, not AWS | Yes | Faster to ship, cheaper for MVP. Migrate to AWS when compliance demands it |
| Doctor must approve every summary | Yes | Non-negotiable for trust, accuracy, and regulatory compliance |

---

## Appendix B: First Weekend Checklist

```
[ ] Record 3 fake consultations (10-15 min each) with a friend
[ ] Sign up for Deepgram (free tier: $200 credit)
[ ] Sign up for Anthropic API (pay-as-you-go)
[ ] Write pipeline.py:
    [ ] Load audio file
    [ ] Send to Deepgram -> get transcript
    [ ] Format transcript with speaker labels
    [ ] Send to Claude -> get JSON summary
    [ ] Print/save results
[ ] Run pipeline on all 3 recordings
[ ] Review outputs: Are they accurate? Useful? Missing anything?
[ ] Show to a doctor (friend, family, LinkedIn connection)
[ ] Document feedback: what works, what doesn't, what's missing
[ ] Decision: proceed / pivot / abandon
```

---

## Appendix C: Useful Links & References

### APIs & Services
- Deepgram: https://deepgram.com
- Anthropic (Claude): https://anthropic.com
- Supabase: https://supabase.com
- Railway: https://railway.app
- Auth0: https://auth0.com
- Sentry: https://sentry.io

### Brazilian Healthtech Context
- Voa Health: https://voa.health
- DoctorAssistant.ai: https://doctorassistant.ai
- Dr. Scriba: https://drscriba.com
- Sofya/Oracle Case Study: https://blogs.oracle.com/oracle-brasil/
- Lei do Prontuario Eletronico: Lei 13.787/2018
- LGPD: Lei 13.709/2018
- Telemedicina: Lei 14.510/2022, Resolucao CFM 2.314/2022

### Technical References
- FastAPI Docs: https://fastapi.tiangolo.com
- React Native (Expo): https://expo.dev
- Next.js: https://nextjs.org
- Celery (task queue): https://docs.celeryq.dev
- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html
