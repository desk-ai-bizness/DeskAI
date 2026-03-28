# CLAUDE.md

Project instructions for Claude Code when working on this repository.

## Project Overview

**Medical AI Scribe** — an AI-powered consultation assistant that acts as a smart medical scribe for Brazilian physicians. It listens to doctor-patient consultations, transcribes audio with speaker diarization, generates structured summaries, and stores them for doctor review and approval.

**Status:** Pre-MVP (Planning / Phase 0)

**Core principle:** Report, never interpret. The AI summarizes what was said, never what it means. Every summary requires physician approval.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Mobile | React Native (Expo) |
| Web | Next.js (React) |
| Backend | Python 3.12+ (FastAPI) |
| Database | PostgreSQL + JSONB |
| Storage | AWS S3 (audio files) |
| ASR | Deepgram (Nova-2 Medical) |
| LLM | Claude API (Anthropic) |
| Auth | Auth0 or Clerk |
| Queue | Celery + Redis |
| Hosting (MVP) | Railway / Supabase |

## Language Rule

- **Code, comments, variable names, commit messages, PR descriptions:** always in English.
- **AI prompts and output templates for the scribe pipeline:** Brazilian Portuguese (pt-BR), since the product serves Brazilian physicians.
- **User-facing strings:** Portuguese (pt-BR).

## Development Guidelines

### Python / FastAPI

- Python 3.12+ with type hints everywhere. Use `Pydantic v2` for all models.
- Async by default — use `async def` for all endpoint handlers and service functions.
- Follow the repository structure:
  ```
  app/
  ├── api/          # Route handlers (thin — delegate to services)
  ├── services/     # Business logic
  ├── models/       # Pydantic models (request/response schemas)
  ├── db/           # SQLAlchemy models and database access
  ├── pipeline/     # AI pipeline (ASR + LLM + post-processing)
  ├── workers/      # Celery background tasks
  ├── core/         # Config, security, dependencies
  └── tests/        # Mirror the app/ structure
  ```
- Use `httpx` (async) for external API calls, never `requests`.
- Error handling: raise `HTTPException` in routes, use custom exception classes in services.
- No bare `except:` — always catch specific exceptions.

### Testing

- **pytest** with `pytest-asyncio` for async tests.
- Test files mirror source structure: `app/services/consultation.py` → `app/tests/services/test_consultation.py`.
- Use `httpx.AsyncClient` with FastAPI's `TestClient` for API tests.
- Mock external services (Deepgram, Claude API) in tests — never call real APIs.
- Every new endpoint or service function needs tests.

### React Native (Expo) / Next.js

- TypeScript everywhere — no `any` types.
- Functional components only, with hooks.
- Use Expo's managed workflow.
- Shared types between web and mobile where possible.

### Database

- PostgreSQL with JSONB for flexible summary storage.
- Use SQLAlchemy 2.0+ with async engine.
- Alembic for migrations — every schema change needs a migration.
- Never use raw SQL strings in application code — use SQLAlchemy ORM/Core.

### Security (Non-Negotiable)

- **Never log or print patient data** (PII, CPF, medical records).
- **Never commit API keys, tokens, or secrets.** Use environment variables.
- **Encrypt sensitive fields at rest** (CPF, phone numbers).
- **All endpoints require authentication** except health checks.
- **Audit trail** for every data access (LGPD requirement).
- **HTTPS only** — no HTTP endpoints in production.

### AI Pipeline Rules

- The system prompt must enforce "report only, never interpret" — no diagnoses, no ICD codes, no clinical decisions.
- Every summary field must link to transcript timestamps (`transcript_ref`).
- JSON output must be validated against the schema before storage.
- Flag unclear/uncertain sections with confidence scores.
- Doctor approval is **required** before any summary is permanently stored.

## Commit Messages

Use conventional commits:
```
feat: add consultation upload endpoint
fix: handle empty transcript from Deepgram
chore: update dependencies
docs: add API documentation
test: add consultation service tests
```

## Build Phases

- **Phase 0:** AI pipeline proof-of-concept (Python script: audio → transcript → summary)
- **Phase 1:** Backend API (FastAPI + PostgreSQL + async workers)
- **Phase 2:** Web app (Next.js dashboard)
- **Phase 3:** Mobile app (React Native / Expo)
- **Phase 4:** Pilot with real physicians
- **Phase 5:** LGPD compliance and scale

See `blueprint-medical-ai.md` for full architecture details, data model, cost analysis, and roadmap.
