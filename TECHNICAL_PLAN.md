# Technical Development Plan — Medical AI Scribe

> **Version:** 1.0  
> **Date:** 2026-03-25  
> **Author:** Daniel Toni  
> **Status:** Planning / Pre-MVP

---

## Table of Contents

1. [Overview & Technical Vision](#1-overview--technical-vision)
2. [Technology Decisions & Rationale](#2-technology-decisions--rationale)
3. [Service Costs Reference](#3-service-costs-reference)
4. [Phase 0 — AI Pipeline Proof of Concept (Weeks 1-2)](#4-phase-0--ai-pipeline-proof-of-concept-weeks-1-2)
5. [Phase 1 — Backend API (Weeks 3-6)](#5-phase-1--backend-api-weeks-3-6)
6. [Phase 2 — Web Application (Weeks 7-10)](#6-phase-2--web-application-weeks-7-10)
7. [Phase 3 — Mobile Application (Weeks 11-14)](#7-phase-3--mobile-application-weeks-11-14)
8. [Phase 4 — Pilot & Hardening (Weeks 15-20)](#8-phase-4--pilot--hardening-weeks-15-20)
9. [Phase 5 — LGPD Compliance & Production Migration (Months 6-8)](#9-phase-5--lgpd-compliance--production-migration-months-6-8)
10. [Phase 6 — Scale & Feature Expansion (Months 9-14)](#10-phase-6--scale--feature-expansion-months-9-14)
11. [Infrastructure Architecture](#11-infrastructure-architecture)
12. [AI Pipeline Deep Dive](#12-ai-pipeline-deep-dive)
13. [Database Design & Data Strategy](#13-database-design--data-strategy)
14. [Security & Compliance Architecture](#14-security--compliance-architecture)
15. [Testing Strategy](#15-testing-strategy)
16. [CI/CD & DevOps](#16-cicd--devops)
17. [Monitoring & Observability](#17-monitoring--observability)
18. [Technical Risk Register](#18-technical-risk-register)
19. [Technology Roadmap Beyond V1](#19-technology-roadmap-beyond-v1)

---

## 1. Overview & Technical Vision

### What We Are Building

A cloud-based service that captures doctor-patient consultation audio, transcribes it with speaker diarization, and uses a large language model (LLM) to generate a structured clinical summary — which the doctor reviews, edits, and approves before it becomes part of the patient's medical record.

### Core Technical Principles

1. **Async-first architecture** — Audio processing takes 30-90 seconds. The system must handle this gracefully with background workers, job queues, and push notifications.
2. **API-first design** — The backend is a REST API consumed by web and mobile clients. No server-rendered pages.
3. **Report, never interpret** — The AI summarizes what was said. It never diagnoses, suggests treatments, or interprets symptoms. This is enforced at the prompt level, validated at the post-processing level, and verified in tests.
4. **Doctor-in-the-loop** — Every AI-generated summary requires explicit physician approval before permanent storage.
5. **Data sovereignty** — All persistent patient data stored in Brazil (AWS sa-east-1). Transient processing via US-based APIs (Deepgram, Anthropic) covered by DPAs and Standard Contractual Clauses.
6. **Progressive complexity** — Start with the simplest possible stack (Railway + Supabase), migrate to AWS when compliance or scale demands it.

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                             │
│                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │ Mobile App   │    │  Web App     │    │ Future:      │  │
│   │ React Native │    │  Next.js     │    │ Desktop,     │  │
│   │ (Expo)       │    │  (React)     │    │ EHR Plugins  │  │
│   └──────┬───────┘    └──────┬───────┘    └──────────────┘  │
│          │                   │                               │
│          └─────────┬─────────┘                               │
│                    │ HTTPS (REST + WebSocket)                │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                           │
│                                                              │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│   │ Auth       │  │ Consult    │  │ Patient    │           │
│   │ Service    │  │ Service    │  │ Service    │           │
│   └────────────┘  └─────┬──────┘  └────────────┘           │
│                         │                                    │
│                    ┌────▼─────┐                              │
│                    │ AI       │  ◄── Celery Worker           │
│                    │ Pipeline │                              │
│                    └────┬─────┘                              │
│                         │                                    │
│              ┌──────────┼──────────┐                        │
│              ▼          ▼          ▼                        │
│         Deepgram    Claude API   Post-Processing            │
│         (ASR)       (Summary)    (Validation)               │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│                                                              │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│   │ PostgreSQL │  │ S3 / R2    │  │ Redis      │           │
│   │ (Supabase) │  │ (Audio)    │  │ (Upstash)  │           │
│   └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Decisions & Rationale

### Core Stack

| Layer | Technology | Why This Over Alternatives |
|-------|-----------|---------------------------|
| **Backend** | Python 3.12+ / FastAPI | Best AI/ML library ecosystem (anthropic SDK, httpx, pydantic). Async-native. Type-safe with Pydantic v2. Auto-generated OpenAPI docs. Largest talent pool for AI work. |
| **Web Frontend** | Next.js 14+ (React / TypeScript) | SSR for marketing/SEO pages, SPA for dashboard. Shares component patterns with React Native. Huge ecosystem. |
| **Mobile** | React Native (Expo) | Single codebase for iOS + Android. Expo managed workflow simplifies build/deploy. Audio recording APIs available via expo-av. |
| **Database** | PostgreSQL 16 + JSONB | One database for structured data (users, patients) AND flexible JSON (summaries). GIN indexes for full-text search inside JSONB. Battle-tested, free, excellent tooling. |
| **Object Storage** | AWS S3 (production) / Supabase Storage (MVP) | Audio files are large (5-50MB). S3 is the cheapest durable storage. Presigned URLs for direct client upload (never routes audio through the API server). |
| **Cache / Queue** | Redis (Upstash serverless for MVP, ElastiCache for production) | Session management, rate limiting, and Celery broker. Upstash has a free tier and serverless pricing. |
| **Task Queue** | Celery + Redis | Audio processing is inherently async (30-90 sec). Celery handles retries, dead-letter queues, and concurrency. Mature, well-documented. |
| **Auth** | Auth0 | HIPAA BAA available (Clerk does not offer this). OAuth2 + MFA out of the box. Free tier: 25,000 MAU. Essential paid tier: ~$35/month. |
| **Payments** | Stripe | Supports Pix (1.19% fee), credit cards (3.99% + R$0.39), boleto (R$3.45). Pix Automatico for recurring subscriptions. No monthly fees. |

### AI Services

| Service | Provider | Model | Why |
|---------|----------|-------|-----|
| **Speech-to-Text (ASR)** | Deepgram | Nova-3 Multilingual | Best price/performance for Portuguese. Built-in speaker diarization. $0.0092/min (PAYG). Streaming support for future real-time features. $200 free credit to start. |
| **Summarization (LLM)** | Anthropic | Claude Haiku 4.5 (MVP) → Sonnet 4.6 (production) | Excellent Portuguese quality. Structured JSON output mode. 200K token context window. Haiku: ~$0.01/consultation. Sonnet: ~$0.04/consultation. Strong instruction-following for "report only" constraint. |
| **Backup ASR** | Google Cloud Speech-to-Text | Chirp 3 | Fallback if Deepgram is down. Supports Portuguese. 60 min/month free. ~$0.016/min. |

### Why NOT AWS HealthScribe

AWS HealthScribe was evaluated and rejected:
- **English only** — no Portuguese support, no announcements of Portuguese support planned
- **$0.10/minute** — 10x more expensive than Deepgram ($0.0092/min) for the same task
- **US East region only** — cannot deploy in sa-east-1 (São Paulo)
- **Limited specialties** — only general medicine and orthopedics
- A 15-minute consultation costs $1.50 with HealthScribe vs. ~$0.14-0.18 with Deepgram + Claude

### Why NOT Whisper (OpenAI)

Whisper was evaluated and rejected for production use (suitable for offline/testing):
- No built-in speaker diarization — requires a separate pipeline (pyannote.audio or similar)
- Requires GPU infrastructure to run at acceptable latency (or use OpenAI's hosted API)
- OpenAI's hosted Whisper API: $0.006/min but limited medical vocabulary optimization
- No medical-specific model for Portuguese
- Deepgram is API-based with zero infrastructure to manage

### Hosting Strategy

| Phase | Hosting | Monthly Cost | Why |
|-------|---------|-------------|-----|
| **MVP (Months 1-4)** | Railway (API) + Supabase (DB + Auth + Storage) + Upstash (Redis) | ~$50-100/month | Fastest to ship. Deploy from GitHub in minutes. No DevOps needed. Focus all energy on product, not infra. |
| **Growth (Months 5-8)** | Railway Pro + Supabase Pro + Cloudflare R2 (audio) | ~$100-300/month | Scale horizontally. Better monitoring. R2 has no egress fees. |
| **Production (Month 9+)** | AWS sa-east-1: ECS Fargate + RDS PostgreSQL + S3 + ElastiCache | ~$164-500/month | Full LGPD compliance. Data residency in São Paulo. Auto-scaling. SLA guarantees. |

---

## 3. Service Costs Reference

All prices as of March 2026. Updated periodically.

### AI API Costs Per 15-Minute Consultation

| Step | Service | Cost | Notes |
|------|---------|------|-------|
| Transcription | Deepgram Nova-3 Multilingual | $0.138 | 15 min × $0.0092/min |
| Summarization (MVP) | Claude Haiku 4.5 | ~$0.015 | ~5K input tokens + ~800 output tokens |
| Summarization (Prod) | Claude Sonnet 4.6 | ~$0.04 | Better quality, same token count |
| **Total (MVP)** | | **~$0.15** | |
| **Total (Prod)** | | **~$0.18** | |

### Infrastructure Costs

#### MVP Stack (Months 1-4)

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Railway | Pro plan | $20 (includes $20 credit) |
| Supabase | Pro plan | $25 |
| Upstash Redis | Free → Pay-as-you-go | $0-10 |
| Cloudflare R2 (audio storage) | Pay-as-you-go | ~$5-10 |
| Auth0 | Free tier (25K MAU) | $0 |
| Sentry (error tracking) | Free tier | $0 |
| Domain + DNS | Cloudflare | ~$15/year |
| Apple Developer Account | Annual | $99/year |
| Google Play Developer | One-time | $25 |
| **Total** | | **~$60-75/month** |

#### Production AWS Stack (Month 9+)

| Service | Configuration | Monthly Cost |
|---------|--------------|-------------|
| ECS Fargate | 2 tasks × 0.5 vCPU / 1 GB RAM | ~$52 |
| RDS PostgreSQL | db.t3.small (2 vCPU, 2 GB) + 20 GB gp3 | ~$48 |
| ElastiCache Redis | cache.t3.micro (0.5 GB) | ~$16 |
| S3 | 100 GB standard storage | ~$3 |
| NAT Gateway | 1 AZ | ~$45 |
| CloudWatch | Logs + metrics + alarms | ~$10 |
| ALB (Application Load Balancer) | HTTPS termination | ~$20 |
| Data transfer | ~20 GB/month | ~$2 |
| **Total** | | **~$196/month** |

**Note:** sa-east-1 (São Paulo) carries a ~40-65% premium over US East regions.

### Cost at Scale (API + Infra Combined)

| Paying Doctors | Consultations/Month | API Cost | Infra Cost | Total Cost |
|----------------|--------------------:|--------:|----------:|-----------:|
| 10 | 4,400 | $660 | $75 | $735 |
| 50 | 22,000 | $3,300 | $200 | $3,500 |
| 100 | 44,000 | $6,600 | $300 | $6,900 |
| 500 | 220,000 | $33,000 | $1,500 | $34,500 |
| 1,000 | 440,000 | $66,000 | $3,000 | $69,000 |

Assumptions: 20 consultations/doctor/day × 22 working days = 440/month. $0.15/consultation average.

---

## 4. Phase 0 — AI Pipeline Proof of Concept (Weeks 1-2)

### Goal

Prove the AI output is useful for Brazilian physicians before building any infrastructure. This is the kill/pivot decision point.

### Deliverables

1. A Python script (~300 lines) that takes an audio file → transcript → structured JSON summary
2. Test results from 5+ mock consultations in Brazilian Portuguese
3. Feedback from 2-3 physicians on output quality
4. Kill/pivot/proceed decision documented

### Technical Steps

#### Week 1: Build the Pipeline Script

**Environment setup:**
```
python -m venv .venv
source .venv/bin/activate
pip install httpx anthropic python-dotenv pydantic
```

**File structure:**
```
pipeline/
├── .env                    # DEEPGRAM_API_KEY, ANTHROPIC_API_KEY
├── pipeline.py             # Main script
├── prompts/
│   └── system_prompt.txt   # LLM system prompt (Portuguese)
├── schemas/
│   └── summary_v1.json     # Expected JSON output schema
├── samples/
│   ├── consultation_01.opus # Mock recordings
│   ├── consultation_02.opus
│   └── ...
└── outputs/
    ├── transcript_01.json  # Deepgram raw output
    ├── summary_01.json     # Claude structured output
    └── ...
```

**Step 1 — Record mock consultations:**
- Record 5 consultations (10-15 min each) with a friend roleplaying doctor/patient
- Cover different specialties: general practice, cardiology, dermatology, pediatrics, psychiatry
- Include realistic ambient noise (background music, door sounds, coughing)
- Use phone recording (to simulate real conditions)
- Record in OPUS format (10x smaller than WAV, supported by Deepgram)

**Step 2 — Transcription (Deepgram):**
```python
import httpx
import os

async def transcribe_audio(audio_path: str) -> dict:
    """Send audio file to Deepgram for transcription with speaker diarization."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(audio_path, "rb") as f:
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}",
                    "Content-Type": "audio/opus",
                },
                content=f.read(),
                params={
                    "model": "nova-2",          # Nova-2 general (pt-BR supported)
                    "language": "pt-BR",
                    "diarize": "true",           # Speaker separation
                    "punctuate": "true",
                    "paragraphs": "true",
                    "smart_format": "true",
                    "utterances": "true",        # Speaker-labeled segments
                },
            )
        response.raise_for_status()
        return response.json()
```

**Step 3 — Format transcript for LLM:**
```python
def format_transcript(deepgram_response: dict) -> str:
    """Convert Deepgram utterances into a readable speaker-labeled transcript."""
    lines = []
    for utterance in deepgram_response["results"]["utterances"]:
        speaker = "Médico" if utterance["speaker"] == 0 else "Paciente"
        start = utterance["start"]
        text = utterance["transcript"]
        lines.append(f"[{start:.1f}s] {speaker}: {text}")
    return "\n".join(lines)
```

**Step 4 — Summarization (Claude):**
```python
import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Você é um escriba médico para consultas de médicos brasileiros.
Seu trabalho é organizar o que foi discutido em um resumo estruturado.

REGRAS CRÍTICAS:
- Relate APENAS o que foi explicitamente dito. Nunca interprete, diagnostique ou infira.
- Use os termos médicos exatos que o médico usou.
- Se algo está inaudível na transcrição, marque como [inaudível].
- Speaker 0 é o Médico, Speaker 1 é o Paciente (a menos que o contexto indique o contrário).
- Escreva em português brasileiro.
- Retorne JSON válido seguindo o schema fornecido.
- NÃO sugira diagnósticos, códigos CID, ou decisões clínicas.
- NÃO interprete sintomas — apenas relate o que foi dito."""

async def summarize_transcript(transcript: str, schema: dict) -> dict:
    """Send formatted transcript to Claude for structured summarization."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Transcrição da consulta:\n\n{transcript}\n\nGere um resumo estruturado seguindo este schema JSON exato:\n{json.dumps(schema, indent=2, ensure_ascii=False)}"""
            }
        ],
    )
    return json.loads(response.content[0].text)
```

**Step 5 — Post-processing validation:**
- Validate JSON against Pydantic schema
- Check all `transcript_ref` timestamps exist in the original transcript
- Calculate confidence score based on: number of `[inaudível]` markers, transcript coverage, speaker balance
- Flag any summary field that cannot be traced back to a specific transcript segment

#### Week 2: Test & Validate

1. Run pipeline on all 5 recordings
2. Manual quality assessment:
   - Does the transcript capture medical terms correctly? (e.g., "dipirona", "omeprazol", "hemograma")
   - Are speakers correctly identified?
   - Does the summary accurately reflect what was said?
   - Are there any hallucinations (information not in the transcript)?
   - Is the JSON structure complete and valid?
3. Show outputs to 2-3 physicians (friends, family, LinkedIn connections)
4. Document feedback: what works, what doesn't, what's missing
5. **Decision gate:** proceed / pivot / abandon

### Cost

| Item | Cost |
|------|------|
| Deepgram API (~75 min of audio) | ~$0.69 |
| Claude API (~10 summaries with iterations) | ~$0.50 |
| **Total** | **< $2** |

Deepgram provides $200 in free credits. Anthropic is pay-as-you-go.

### Success Criteria

- [ ] Transcript word error rate < 15% for medical Portuguese
- [ ] Speaker diarization accuracy > 90% (correct speaker label)
- [ ] Summary covers all key sections (reason for visit, symptoms, medications, instructions)
- [ ] Zero hallucinations in 5 test runs
- [ ] At least 2 out of 3 physicians say "I would use this"

---

## 5. Phase 1 — Backend API (Weeks 3-6)

### Goal

Build a production-ready REST API with async AI pipeline, deployed and accessible from the internet.

### Deliverables

1. FastAPI application with all core endpoints
2. Celery background workers for AI pipeline
3. PostgreSQL database with all core tables
4. S3/R2 integration for audio storage
5. Auth0 authentication integration
6. Deployed on Railway with Supabase database
7. OpenAPI documentation auto-generated
8. Test suite with >80% coverage

### Week 3-4: Core API

#### Project Structure

```
app/
├── __init__.py
├── main.py                          # FastAPI app factory
├── core/
│   ├── config.py                    # Settings (Pydantic BaseSettings)
│   ├── security.py                  # Auth0 JWT verification
│   ├── dependencies.py              # Dependency injection
│   └── exceptions.py                # Custom exception classes
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py                # Main router aggregating all sub-routers
│   │   ├── auth.py                  # POST /auth/login, /auth/register
│   │   ├── consultations.py         # CRUD + workflow endpoints
│   │   ├── patients.py              # CRUD + search
│   │   ├── audio.py                 # Upload presigned URL generation
│   │   └── health.py                # GET /health (no auth required)
│   └── deps.py                      # Route-level dependencies
├── services/
│   ├── __init__.py
│   ├── consultation.py              # Business logic for consultations
│   ├── patient.py                   # Business logic for patients
│   ├── audio.py                     # S3 presigned URL generation
│   └── notification.py              # Push notifications / WebSocket
├── pipeline/
│   ├── __init__.py
│   ├── transcription.py             # Deepgram integration
│   ├── summarization.py             # Claude API integration
│   ├── postprocessing.py            # JSON validation, confidence scoring
│   └── prompts/
│       └── system_prompt_v1.txt      # LLM system prompt
├── models/
│   ├── __init__.py
│   ├── consultation.py              # Pydantic request/response schemas
│   ├── patient.py
│   ├── summary.py                   # Summary JSON schema (Pydantic)
│   └── audit.py
├── db/
│   ├── __init__.py
│   ├── engine.py                    # SQLAlchemy async engine
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── repositories/
│   │   ├── consultation.py          # DB access for consultations
│   │   ├── patient.py
│   │   └── audit.py
│   └── migrations/                  # Alembic
│       ├── env.py
│       └── versions/
├── workers/
│   ├── __init__.py
│   ├── celery_app.py                # Celery configuration
│   └── tasks.py                     # process_consultation task
├── tests/
│   ├── conftest.py                  # Fixtures (test DB, mock clients)
│   ├── api/
│   │   ├── test_consultations.py
│   │   ├── test_patients.py
│   │   └── test_audio.py
│   ├── services/
│   │   ├── test_consultation.py
│   │   └── test_patient.py
│   ├── pipeline/
│   │   ├── test_transcription.py
│   │   ├── test_summarization.py
│   │   └── test_postprocessing.py
│   └── workers/
│       └── test_tasks.py
├── pyproject.toml                   # Dependencies (Poetry or pip)
├── Dockerfile
├── docker-compose.yml               # Local dev (Postgres + Redis)
└── alembic.ini
```

#### API Endpoints

```
Authentication:
  POST   /api/v1/auth/register        Register new doctor account
  POST   /api/v1/auth/login            Login (delegates to Auth0)
  POST   /api/v1/auth/refresh          Refresh JWT token

Consultations:
  POST   /api/v1/consultations                  Create new consultation
  GET    /api/v1/consultations                   List (with filters: status, date, patient)
  GET    /api/v1/consultations/:id               Get single consultation + summary
  PATCH  /api/v1/consultations/:id               Doctor edits summary fields
  POST   /api/v1/consultations/:id/approve       Doctor approves summary
  POST   /api/v1/consultations/:id/reject        Doctor rejects (back to pending_review)
  DELETE /api/v1/consultations/:id               Delete consultation (soft delete)
  POST   /api/v1/consultations/:id/upload-url    Get presigned S3 URL for audio upload
  POST   /api/v1/consultations/:id/process       Trigger AI pipeline (called after upload)

Patients:
  POST   /api/v1/patients                        Create patient
  GET    /api/v1/patients                         Search patients (name, CPF)
  GET    /api/v1/patients/:id                     Get patient details
  PATCH  /api/v1/patients/:id                     Update patient
  GET    /api/v1/patients/:id/consultations       Patient's consultation history

Health:
  GET    /api/v1/health                           Healthcheck (no auth)
  GET    /api/v1/health/ready                     Readiness check (DB + Redis)
```

#### Database Schema

See `blueprint-medical-ai.md` Section 9 for the full SQL schema. Key additions for Phase 1:

- All UUIDs generated server-side (`gen_random_uuid()`)
- `cpf` column encrypted at rest using `pgcrypto` extension
- `consultations.summary` is JSONB with GIN index for search
- `audit_log` table captures every data access (LGPD requirement)
- Alembic migrations for all schema changes — no raw DDL in production

#### Audio Upload Flow

```
1. Client: POST /consultations → gets consultation_id
2. Client: POST /consultations/:id/upload-url → gets presigned S3 PUT URL (5 min expiry)
3. Client: PUT audio directly to S3 (multipart for files > 25MB)
4. Client: POST /consultations/:id/process → triggers Celery task
5. Worker: Downloads audio from S3 → Deepgram → Claude → post-processing → store results
6. Worker: Updates consultation status to "pending_review"
7. Worker: Sends push notification to doctor via WebSocket or Firebase Cloud Messaging
```

The audio never passes through the API server. Direct client-to-S3 upload via presigned URLs reduces server load and latency.

### Week 5-6: Celery Workers & Pipeline Integration

#### Celery Task Flow

```python
# workers/tasks.py
from celery import Celery
from app.pipeline.transcription import transcribe_audio
from app.pipeline.summarization import summarize_transcript
from app.pipeline.postprocessing import validate_and_enrich

celery_app = Celery("medical_scribe")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_consultation(self, consultation_id: str):
    """Full AI pipeline: audio → transcript → summary → store."""
    try:
        # 1. Get audio URL from S3
        audio_url = get_presigned_download_url(consultation_id)

        # 2. Transcribe with Deepgram
        transcript = transcribe_audio(audio_url)

        # 3. Format transcript for LLM
        formatted = format_transcript(transcript)

        # 4. Summarize with Claude
        summary = summarize_transcript(formatted)

        # 5. Post-process: validate JSON, link sources, score confidence
        enriched_summary = validate_and_enrich(summary, transcript)

        # 6. Store results
        update_consultation(
            consultation_id,
            transcript=transcript,
            summary=enriched_summary,
            status="pending_review"
        )

        # 7. Notify doctor
        send_notification(consultation_id, "summary_ready")

    except DeepgramError as e:
        # Retry with exponential backoff
        raise self.retry(exc=e)
    except AnthropicError as e:
        # Retry with exponential backoff
        raise self.retry(exc=e)
    except Exception as e:
        # Mark as error, don't retry
        update_consultation(consultation_id, status="error", error=str(e))
        raise
```

#### Error Handling & Retry Strategy

| Error Type | Strategy | Max Retries | Backoff |
|------------|----------|------------:|--------:|
| Deepgram API timeout | Retry | 3 | 30s, 60s, 120s |
| Deepgram rate limit | Retry | 5 | Respect `Retry-After` header |
| Claude API timeout | Retry | 3 | 30s, 60s, 120s |
| Claude rate limit | Retry | 5 | Respect `Retry-After` header |
| Invalid JSON from Claude | Retry with modified prompt | 2 | Immediate |
| Audio file corrupted | Fail permanently | 0 | N/A |
| Database error | Retry | 3 | 10s, 30s, 60s |
| Unknown error | Fail permanently, alert | 0 | N/A |

### Deployment (Week 6)

**Railway deployment:**
```yaml
# railway.toml
[build]
  builder = "dockerfile"

[deploy]
  startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  healthcheckPath = "/api/v1/health"
  healthcheckTimeout = 10
  restartPolicyType = "on_failure"
  restartPolicyMaxRetries = 5
```

**Services on Railway:**
1. **API** — FastAPI (uvicorn)
2. **Worker** — Celery worker (`celery -A app.workers.celery_app worker`)
3. **Redis** — Railway Redis addon (or Upstash external)

**Supabase:**
1. PostgreSQL database (Pro tier, $25/month)
2. Connection via connection string (SSL required)

---

## 6. Phase 2 — Web Application (Weeks 7-10)

### Goal

Build a functional web dashboard where doctors can record consultations, review AI summaries, manage patients, and approve documentation.

### Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14+ (App Router) |
| Language | TypeScript (strict mode) |
| UI Library | Tailwind CSS + shadcn/ui |
| State Management | React Query (TanStack Query) for server state |
| Forms | React Hook Form + Zod validation |
| Audio Recording | MediaRecorder API (Web) |
| Real-time | WebSocket (consultation status updates) |
| Auth | Auth0 Next.js SDK (@auth0/nextjs-auth0) |
| Testing | Vitest + React Testing Library + Playwright (E2E) |

### Pages & Features

#### Week 7-8: Core Pages

| Page | Route | Features |
|------|-------|----------|
| **Login** | `/login` | Auth0 Universal Login. CRM number verification on first login. |
| **Dashboard** | `/dashboard` | Today's consultations. Pending reviews count (badge). Recent activity feed. Quick-start recording button. |
| **New Consultation** | `/consultations/new` | Select patient (search or create new). Big record button. Audio waveform visualization while recording. Upload progress indicator. |
| **Review Summary** | `/consultations/[id]` | Left panel: AI-generated structured summary (editable fields). Right panel: transcript with timestamps (click to play audio). Approve / Reject buttons. Edit tracking (what the doctor changed). |
| **Patient List** | `/patients` | Search by name or CPF. List with last consultation date. Click to view history. |
| **Patient Detail** | `/patients/[id]` | Patient info. Timeline of all consultations. Each consultation expandable to see summary. |
| **Settings** | `/settings` | Profile (name, CRM, specialty). Notification preferences. Clinic management. |

#### Week 9-10: Polish & Real-time Features

| Feature | Description |
|---------|-------------|
| **WebSocket notifications** | Real-time status updates: "processing" → "summary ready". Toast notifications. |
| **Audio playback** | Click any summary item → plays the corresponding audio segment (using `transcript_ref` timestamps). |
| **Summary editing** | Inline editing of each summary field. Track what the doctor changed (stored as `doctor_edits` JSONB). |
| **Export** | Export approved summary as PDF (for printing or sharing). |
| **Responsive design** | Works on tablet and phone browsers (not just desktop). |
| **Dark mode** | Toggle between light and dark themes. |

### Audio Recording Implementation

```typescript
// hooks/useAudioRecorder.ts
import { useState, useRef } from 'react';

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100,
      },
    });

    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
    });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      setAudioBlob(blob);
      chunksRef.current = [];
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start(1000); // Capture in 1-second chunks
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current?.stream.getTracks().forEach(t => t.stop());
    setIsRecording(false);
  };

  return { isRecording, audioBlob, startRecording, stopRecording };
}
```

---

## 7. Phase 3 — Mobile Application (Weeks 11-14)

### Goal

Build a React Native (Expo) app for iOS and Android. The mobile app is the **killer feature** — phone sits on the doctor's desk, one tap to record, one tap to stop.

### Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | React Native + Expo SDK 52+ |
| Language | TypeScript (strict mode) |
| Navigation | Expo Router (file-based routing) |
| Audio | expo-av (recording + playback) |
| UI | NativeWind (Tailwind for React Native) + custom components |
| State | React Query (TanStack Query) |
| Auth | Auth0 React Native SDK |
| Push Notifications | Expo Notifications + Firebase Cloud Messaging |
| Testing | Jest + React Native Testing Library + Detox (E2E) |

### Screens

| Screen | Description |
|--------|-------------|
| **Login** | Auth0 login with biometric option (Face ID / fingerprint) |
| **Home** | Today's consultations list. Big floating "Record" button. Pending reviews badge. |
| **Record** | Full-screen recording view. Patient selector at top. Giant red pulsing record button. Timer. Waveform visualization. |
| **Processing** | Loading state with progress indicator. "We'll notify you when the summary is ready." |
| **Review** | Scrollable summary with editable fields. Transcript accordion. Approve/Reject buttons. |
| **Patient Search** | Search by name. Quick-create patient inline. |
| **Notifications** | List of all notifications (summaries ready, errors, etc.) |

### Audio Recording (Expo)

```typescript
// hooks/useExpoAudioRecorder.ts
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

export function useExpoAudioRecorder() {
  const [recording, setRecording] = useState<Audio.Recording | null>(null);

  const startRecording = async () => {
    await Audio.requestPermissionsAsync();
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    const { recording } = await Audio.Recording.createAsync(
      Audio.RecordingOptionsPresets.HIGH_QUALITY // 44.1kHz, AAC
    );
    setRecording(recording);
  };

  const stopRecording = async () => {
    if (!recording) return null;
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    setRecording(null);
    return uri; // Local file path
  };

  return { recording, startRecording, stopRecording };
}
```

### Upload Strategy (Large Files)

Consultation audio can be 5-50MB. Upload strategy:

1. **Compression:** OPUS encoding reduces file size ~10x vs WAV
2. **Background upload:** Use `expo-file-system` background upload (continues if app is backgrounded)
3. **Chunked upload:** For files > 25MB, split into 5MB multipart chunks to S3
4. **Resume on failure:** Track uploaded chunks, resume from last successful chunk
5. **Offline queue:** If no internet, queue the upload and process when connected

### Push Notifications

```
Consultation processed → Backend sends FCM notification → Phone buzzes
  → Doctor taps notification → Opens review screen directly
```

Using Expo Notifications + Firebase Cloud Messaging (free tier: unlimited notifications).

---

## 8. Phase 4 — Pilot & Hardening (Weeks 15-20)

### Goal

Onboard 5-10 doctors for free pilot. Collect feedback. Fix critical issues. Start charging.

### Week 15-16: Pilot Onboarding

1. **Recruit 5-10 pilot doctors** — friends, family, LinkedIn, medical school contacts
2. **Onboarding flow:** 15-minute video call setup + first recording together
3. **Feedback channel:** Dedicated WhatsApp group (doctors use WhatsApp heavily in Brazil)
4. **Usage tracking:** Amplitude or PostHog for product analytics (free tiers)

### Week 17-18: Fix Top Issues

Based on pilot feedback, expect to fix:
- Transcript quality issues (background noise, accents, medical jargon)
- Summary structure adjustments (missing fields, wrong categorization)
- UX friction (too many taps, confusing flow, slow upload)
- Audio quality recommendations (phone placement guide)

### Week 19-20: Billing & Launch Prep

1. **Stripe integration** — subscription billing with Pix (1.19% fee) and credit card (3.99% + R$0.39)
2. **Pricing page** — R$199/month (Basic) and R$349/month (Pro)
3. **Onboarding flow** — self-service signup, 7-day free trial (no credit card required)
4. **Landing page** — marketing site with testimonials from pilot doctors
5. **Error handling hardening:**
   - What happens when Deepgram is down? → Queue job, retry in 5 min, notify doctor of delay
   - What happens when audio is corrupted? → Detect early, notify doctor to re-record
   - What happens when Claude returns invalid JSON? → Retry with stricter prompt, fallback to simpler template
6. **Rate limiting** — per-doctor limits to prevent abuse (100 consultations/day max)

### Success Criteria for Pilot

- [ ] 5+ doctors completing 10+ consultations each
- [ ] Average processing time < 2 minutes
- [ ] Doctor edit rate < 30% (70%+ of summaries are usable without edits)
- [ ] NPS > 30
- [ ] At least 2 doctors willing to pay
- [ ] Zero data loss incidents

---

## 9. Phase 5 — LGPD Compliance & Production Migration (Months 6-8)

### Goal

Achieve full LGPD compliance and migrate to AWS sa-east-1 for data sovereignty.

### LGPD Technical Requirements

| Requirement | Implementation |
|-------------|---------------|
| **Encryption at rest** | PostgreSQL: TDE (Transparent Data Encryption) on RDS. S3: SSE-S3 (AES-256). CPF column: application-level encryption with `pgcrypto`. |
| **Encryption in transit** | TLS 1.3 everywhere. No HTTP endpoints. Certificate pinning on mobile. |
| **Audit trail** | `audit_log` table captures every data access (who, what, when, from where). Immutable — no DELETE or UPDATE on audit_log. |
| **Consent management** | `patient_consents` table tracking consent per patient per purpose. Digital signature (ICP-Brasil compatible) or checkbox with timestamp. |
| **Data portability** | API endpoint to export all patient data as JSON/CSV on demand. |
| **Right to deletion** | Soft delete + scheduled hard delete after retention period (20 years for medical records per Lei 13.787/2018). |
| **DPO contact** | Public DPO contact on website. Can be outsourced for small companies. |
| **Breach notification** | Automated alerting (Sentry + PagerDuty). Process to notify ANPD within 48 hours. |
| **Standard Contractual Clauses** | Signed SCCs with Deepgram and Anthropic for international data transfers (mandatory since August 2025). |
| **Data minimization** | Audio files deleted after 90 days (configurable per clinic). Only transcript + summary retained long-term. |

### AWS Migration Plan

1. **Infrastructure as Code** — Terraform for all AWS resources
2. **VPC setup** — Private subnets for RDS + ElastiCache. Public subnets for ALB + ECS tasks.
3. **Database migration** — `pg_dump` from Supabase → `pg_restore` to RDS during maintenance window
4. **DNS cutover** — Zero-downtime migration using weighted routing in Route 53
5. **CI/CD migration** — GitHub Actions deploys to ECR → ECS (blue/green deployment)

---

## 10. Phase 6 — Scale & Feature Expansion (Months 9-14)

### Features Roadmap

| Feature | Effort | Impact | Priority |
|---------|--------|--------|----------|
| **Real-time transcription** | High (streaming Deepgram + live UI) | High — see transcript as you speak | P1 |
| **Custom summary templates** | Medium (per-specialty prompt tuning) | High — dermatology vs. psychiatry need different formats | P1 |
| **EHR integration (MV Sistemas)** | High (API integration + data mapping) | Very High — 68% market share in Brazil | P1 |
| **Multi-language** | Low (add `es` to Deepgram + Claude prompts) | Medium — opens Spanish-speaking LATAM | P2 |
| **Clinic-wide analytics** | Medium (aggregate dashboards) | Medium — sells Pro/Enterprise plans | P2 |
| **Patient-facing summary** | Low (simplified view of approved summary) | Medium — differentiator | P3 |
| **Offline recording** | Medium (local storage + sync queue) | Medium — rural areas | P3 |
| **API-as-a-service** | High (multi-tenant, rate limiting, billing) | High — new revenue stream | P3 |
| **Desktop agent (system audio capture)** | High (OS-level audio routing) | Medium — telemedicine use case | P4 |

### Performance Targets at Scale

| Metric | Target |
|--------|--------|
| API response time (P95) | < 200ms |
| Audio upload throughput | 100 concurrent uploads |
| AI pipeline processing time | < 90 seconds (15-min audio) |
| Database query time (P95) | < 50ms |
| Uptime SLA | 99.9% |
| Concurrent active WebSocket connections | 1,000 |

---

## 11. Infrastructure Architecture

### MVP Architecture (Months 1-4)

```
┌─────────────────────────────────────────────┐
│               Cloudflare                     │
│         (DNS + CDN + DDoS protection)        │
└──────────────────┬──────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌──────────────┐   ┌──────────────┐
│  Vercel      │   │  Railway     │
│  (Next.js)   │   │  (FastAPI    │
│              │   │  + Celery)   │
│  Web app     │   │  API +       │
│  + Marketing │   │  Workers     │
└──────────────┘   └──────┬───────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ Supabase │  │ Upstash  │  │ R2 / S3  │
     │ Postgres │  │ Redis    │  │ (Audio)  │
     └──────────┘  └──────────┘  └──────────┘
```

### Production Architecture (Month 9+)

See `blueprint-medical-ai.md` Section 11 for the full AWS sa-east-1 architecture diagram.

---

## 12. AI Pipeline Deep Dive

### Pipeline Architecture

```
┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌─────────────┐
│  Audio   │───▶│ Transcription │───▶│ Summary   │───▶│ Post-       │
│  (S3)    │    │ (Deepgram)   │    │ (Claude)  │    │ Processing  │
│          │    │              │    │           │    │             │
│ OPUS/    │    │ Nova-3       │    │ Haiku 4.5 │    │ - Validate  │
│ WebM     │    │ Multilingual │    │ (MVP)     │    │ - Score     │
│ 16kHz+   │    │ pt-BR        │    │ Sonnet 4.6│    │ - Link refs │
│          │    │ + Diarize    │    │ (Prod)    │    │ - PII detect│
└──────────┘    └──────────────┘    └───────────┘    └─────────────┘
```

### Prompt Engineering Strategy

The system prompt is the most critical piece of the product. It must:

1. **Enforce the "report only" constraint** — multiple redundant instructions to never interpret
2. **Handle edge cases** — unclear audio, overlapping speakers, non-medical small talk
3. **Output valid JSON** — use Claude's structured output mode for guaranteed schema compliance
4. **Be specialty-aware** — different prompts for different medical specialties (Phase 6)
5. **Include examples** — few-shot prompting with gold-standard summaries

Prompts are version-controlled in `app/pipeline/prompts/` and A/B tested with a prompt version field in the summary JSON.

### Fallback Strategy

| Primary | Fallback | Trigger |
|---------|----------|--------|
| Deepgram Nova-3 | Google Cloud Chirp 3 | Deepgram API 5xx for > 5 min |
| Claude Haiku 4.5 | Claude Haiku 3.5 (cheaper/older) | Anthropic API 5xx for > 5 min |
| Claude Haiku 4.5 | Claude Sonnet 4.6 | Haiku returns invalid JSON after 2 retries |

---

## 13. Database Design & Data Strategy

### PostgreSQL Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";      -- For gen_random_uuid() and encryption
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- For trigram similarity search (patient names)
CREATE EXTENSION IF NOT EXISTS "unaccent";      -- For accent-insensitive search (Portuguese)
```

### Indexing Strategy

| Table | Index | Type | Purpose |
|-------|-------|------|--------|
| `consultations` | `(doctor_id, consultation_date DESC)` | B-tree | Dashboard: today's consultations |
| `consultations` | `(patient_id, consultation_date DESC)` | B-tree | Patient history timeline |
| `consultations` | `(status)` | B-tree | Filter by status |
| `consultations` | `(summary)` | GIN | Full-text search inside JSON summaries |
| `patients` | `(clinic_id, name)` | B-tree | Patient search |
| `patients` | `(name gin_trgm_ops)` | GIN (trigram) | Fuzzy name search |
| `audit_log` | `(actor_id, created_at DESC)` | B-tree | User activity feed |
| `audit_log` | `(resource_type, resource_id)` | B-tree | Resource access history |

### Data Retention Policy

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Audio files (S3) | 90 days after approval | Space optimization. Transcript is the permanent record. |
| Transcripts (JSONB) | 20 years | Lei 13.787/2018 requires 20-year medical record retention |
| Summaries (JSONB) | 20 years | Part of the medical record |
| Audit logs | 5 years | LGPD compliance |
| Deleted patient data | Soft delete → hard delete after 30 days | Right to deletion (LGPD) |

---

## 14. Security & Compliance Architecture

### Authentication & Authorization

| Layer | Implementation |
|-------|---------------|
| **Identity Provider** | Auth0 (HIPAA BAA available) |
| **Token type** | JWT (RS256) with refresh tokens |
| **MFA** | Required for all doctor accounts (TOTP or SMS) |
| **RBAC** | Roles: `doctor`, `clinic_admin`, `super_admin` |
| **Row-level security** | Doctors can only access their own patients and consultations |
| **API key** | For future API-as-a-service (Phase 6) |

### Data Protection

| Threat | Protection |
|--------|------------|
| Data in transit | TLS 1.3 everywhere. HSTS headers. Certificate pinning on mobile. |
| Data at rest | RDS encryption (AES-256). S3 SSE-S3. CPF/phone encrypted with `pgcrypto`. |
| SQL injection | SQLAlchemy ORM (parameterized queries). No raw SQL. |
| XSS | React auto-escapes. CSP headers. |
| CSRF | SameSite cookies. CSRF tokens for state-changing requests. |
| PII in logs | NEVER log patient data. Structured logging with PII scrubbing middleware. |
| API abuse | Rate limiting per doctor (100 consultations/day). Per-IP rate limiting on auth endpoints. |
| Secrets management | Environment variables only. AWS Secrets Manager in production. |

### Patient Consent Flow

```
1. Doctor selects patient → system checks if consent exists
2. If no consent → display consent form on screen
3. Patient reads consent (or doctor reads aloud)
4. Consent covers: audio recording, AI processing, international data transfer
5. Patient signs digitally (checkbox + timestamp) or verbally (doctor confirms)
6. Consent record stored in `patient_consents` table (immutable)
7. Recording begins only after consent is recorded
```

---

## 15. Testing Strategy

### Test Pyramid

```
           ┌──────┐
           │  E2E │  ← Playwright (web) + Detox (mobile)
          ┌┴──────┴┐
          │ Integr. │  ← httpx.AsyncClient + test DB
         ┌┴────────┴┐
         │   Unit    │  ← pytest + mocked dependencies
        ┌┴──────────┴┐
        │   Static    │  ← mypy + ruff + eslint
        └────────────┘
```

### Backend Testing

| Test Type | Tools | Coverage Target |
|-----------|-------|----------------|
| Unit tests | pytest + pytest-asyncio | >80% |
| Integration tests | httpx.AsyncClient + test Postgres | All API endpoints |
| Pipeline tests | Mocked Deepgram/Claude responses | All pipeline paths |
| E2E tests | Playwright | Core happy paths |
| Load tests | Locust | 100 concurrent consultations |

### AI Pipeline Testing

- **Golden test suite:** 20+ consultation recordings with manually verified gold-standard summaries
- **Regression tests:** Run pipeline on golden suite after every prompt change
- **Hallucination detection:** Automated check that every summary fact maps to a transcript segment
- **Schema validation:** Pydantic model validates every Claude output before storage
- **Prompt versioning:** Every summary stores the prompt version used. Compare accuracy across versions.

---

## 16. CI/CD & DevOps

### GitHub Actions Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy app/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml

  deploy:
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: railway up  # or: aws ecs update-service
```

### Deployment Strategy

| Phase | Strategy |
|-------|----------|
| MVP | Railway auto-deploy on push to `main` |
| Production | Blue/green deployment on ECS Fargate. Health check before traffic cutover. |
| Database migrations | Alembic runs as a pre-deploy step. Backward-compatible only. |
| Rollback | Railway: revert to previous deployment. AWS: switch traffic back to blue. |

---

## 17. Monitoring & Observability

### Stack

| Tool | Purpose | Cost |
|------|---------|------|
| **Sentry** | Error tracking + performance monitoring | Free tier (5K events/month) |
| **PostHog** | Product analytics (user behavior, feature usage) | Free tier (1M events/month) |
| **CloudWatch** (production) | Infrastructure metrics, logs, alarms | ~$10/month |
| **UptimeRobot** | Uptime monitoring + status page | Free tier (50 monitors) |

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| API response time (P95) | < 200ms | > 500ms |
| AI pipeline processing time | < 90s | > 180s |
| Error rate | < 1% | > 5% |
| Deepgram API latency | < 30s | > 60s |
| Claude API latency | < 15s | > 30s |
| Queue depth (pending jobs) | < 10 | > 50 |
| Database connections | < 20 | > 40 |
| Audio upload success rate | > 99% | < 95% |
| Doctor summary approval rate | > 70% | < 50% |

---

## 18. Technical Risk Register

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | **Portuguese transcription quality** — Deepgram Nova-3 is not medical-optimized for Portuguese (Medical model is English-only) | High | Medium | Test extensively in Phase 0. Build a custom vocabulary list for common medical terms. Consider Google Chirp 3 as alternative. Long-term: fine-tune a custom ASR model. |
| 2 | **LLM hallucination** — Claude generates facts not present in the transcript | Critical | Medium | Multi-layer defense: (1) strict system prompt, (2) post-processing validation that checks every claim against transcript, (3) mandatory doctor review, (4) hallucination detection tests in CI. |
| 3 | **Audio quality in real clinics** — background noise, distant microphone, overlapping speakers | High | High | Phase 0 tests with real clinic conditions. Recommend phone placement (desk, 30cm from patient). Future: offer USB directional microphone accessory. Preprocessing: noise reduction before Deepgram. |
| 4 | **LGPD compliance with US-based APIs** — sending patient audio/text to Deepgram (US) and Anthropic (US) | High | Low | Sign DPAs with both providers. Implement ANPD-approved Standard Contractual Clauses (mandatory since August 2025). Anonymize PII before sending to Claude where possible. Long-term: deploy local ASR model. |
| 5 | **Deepgram/Anthropic API downtime** | Medium | Low | Queue-based architecture: jobs retry automatically. Multi-provider fallback (Google Chirp 3 for ASR, older Claude model for LLM). Store audio first, process later. |
| 6 | **Cost overrun at scale** — API costs grow linearly with consultations | Medium | Medium | Negotiate volume discounts (Deepgram Growth tier at 4K/year). Use Claude Haiku (cheapest) for most consultations. Batch API (50% discount) for non-urgent processing. Long-term: proprietary ASR model. |
| 7 | **Data breach** — patient health data exposed | Critical | Low | Encryption everywhere. Minimal data retention (audio deleted after 90 days). RBAC. Audit logs. Incident response plan. Cyber insurance. |
| 8 | **Single founder / key person risk** | High | If solo | Document everything. Use managed services (no custom infra to maintain). Consider a technical co-founder. |

---

## 19. Technology Roadmap Beyond V1

### Year 1 (Months 9-14)

| Initiative | Technology | Impact |
|-----------|-----------|--------|
| Real-time transcription | Deepgram streaming API + WebSocket to client | See transcript live during consultation |
| EHR integration | REST API integration with MV Sistemas (FHIR R4 if supported) | 68% of Brazilian hospitals use MV |
| Custom specialty templates | Per-specialty prompt library + Pydantic schemas | Better summaries for dermatology, psychiatry, etc. |
| Spanish language support | Deepgram `es` + Claude Spanish prompts | Open LATAM market (Colombia, Mexico, Argentina) |

### Year 2 (Months 15-24)

| Initiative | Technology | Impact |
|-----------|-----------|--------|
| Proprietary ASR model | Fine-tuned Whisper on Brazilian medical Portuguese corpus | Reduce Deepgram dependency. Better medical term accuracy. Lower cost. |
| On-device processing | Whisper.cpp on mobile for offline transcription | Works without internet. Zero data transfer risk. |
| ICD-10 code suggestions | Classification model trained on approved summaries | Only after regulatory clarity (ANVISA SaMD classification risk) |
| API-as-a-service | Multi-tenant API with usage-based billing | New revenue stream: other healthtechs embed your pipeline |
| Desktop agent | Electron app capturing system audio (for telemedicine) | Capture audio from video calls |

### Year 3+ (Months 25+)

| Initiative | Technology | Impact |
|-----------|-----------|--------|
| Patient timeline | Graph database (Neo4j) for cross-consultation relationships | Longitudinal health narrative |
| Expand beyond healthcare | Configurable pipeline for legal, therapy, financial consultations | 10x TAM |
| Portugal expansion | Same product, minor localization (pt-PT vs pt-BR) | Virtually no competition in Portugal |
| Federated learning | Privacy-preserving model improvement across clinics | Better model without sharing patient data |

---

## Appendix A: Development Environment Setup

```bash
# Prerequisites
python --version  # 3.12+
node --version    # 20+
npx expo --version  # 52+

# Backend setup
git clone https://github.com/danielportoni/medical-ai-scribe.git
cd medical-ai-scribe
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in API keys

# Start local services
docker-compose up -d  # PostgreSQL + Redis
alembic upgrade head   # Run migrations
uvicorn app.main:app --reload  # Start API
celery -A app.workers.celery_app worker --loglevel=info  # Start worker

# Web app
cd web/
npm install
npm run dev  # http://localhost:3000

# Mobile app
cd mobile/
npm install
npx expo start  # Scan QR code with Expo Go
```

## Appendix B: Key Third-Party Accounts Needed

| Service | URL | Free Tier |
|---------|-----|----------|
| Deepgram | https://deepgram.com | $200 free credit |
| Anthropic | https://console.anthropic.com | Pay-as-you-go |
| Supabase | https://supabase.com | 2 projects, 500 MB DB |
| Railway | https://railway.com | $5 credit (trial) |
| Auth0 | https://auth0.com | 25,000 MAU |
| Cloudflare | https://cloudflare.com | Free DNS + CDN |
| Sentry | https://sentry.io | 5,000 events/month |
| PostHog | https://posthog.com | 1M events/month |
| Stripe | https://stripe.com/br | No monthly fees |
| Apple Developer | https://developer.apple.com | $99/year |
| Google Play | https://play.google.com/console | $25 one-time |
| Expo | https://expo.dev | Free tier |
| Vercel | https://vercel.com | Free tier (hobby) |
| UptimeRobot | https://uptimerobot.com | 50 monitors free |
