# Medical AI Scribe

An AI-powered consultation assistant that acts as a **smart medical scribe** for physicians.

## What It Does

The service listens to doctor-patient consultations, transcribes the audio with speaker labels, generates a structured summary of everything discussed, and stores it for the doctor to review and approve.

```
Doctor talks to patient
        |
Audio captured (phone or browser)
        |
Transcription with speaker diarization
        |
AI generates structured summary
        |
Doctor reviews, edits, approves
        |
Stored in database for patient history
```

## What It Is NOT

This is **not** an AI doctor. It does not:
- Diagnose conditions
- Interpret symptoms
- Suggest ICD-10 codes
- Make any clinical decisions

The AI **observes and organizes**. It does not **interpret or diagnose**. Every summary requires physician review and approval before being saved.

## Target Market

Brazilian physicians and clinics — built for Portuguese-first medical vocabulary and documentation standards.

### Key Numbers

| Metric | Value |
|--------|-------|
| Active physicians in Brazil | ~500,000 |
| EHR penetration | ~8% of institutions |
| Documentation time per consultation | ~7 minutes (AI reduces to ~2 min) |
| Physicians using telemedicine | 68% |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Mobile | React Native (Expo) |
| Web | Next.js |
| Backend | Python (FastAPI) |
| Database | PostgreSQL + JSONB |
| Storage | AWS S3 |
| ASR | Deepgram (Nova-2 Medical) |
| LLM | Claude API (Anthropic) |
| Auth | Auth0 or Clerk |
| Queue | Celery + Redis |
| Hosting (MVP) | Railway / Supabase |
| Hosting (Prod) | AWS sa-east-1 (São Paulo) |

## Project Status

- [x] Product concept and market validation
- [x] Technical blueprint complete
- [ ] Phase 0: AI pipeline proof of concept
- [ ] Phase 1: Backend API
- [ ] Phase 2: Web app
- [ ] Phase 3: Mobile app
- [ ] Phase 4: Pilot with real doctors
- [ ] Phase 5: LGPD compliance & scale

## Documentation

- **[blueprint-medical-ai.md](./blueprint-medical-ai.md)** — Full technical blueprint covering architecture, data model, AI pipeline, infrastructure, costs, revenue model, competitive landscape, risks, and roadmap.

## Economics

| Item | Per Consultation |
|------|------------------|
| Deepgram (~15 min) | $0.09 |
| Claude (summary) | $0.02 |
| Infrastructure | $0.01 |
| **Total** | **$0.12** |

Target pricing: R$199-349/month per doctor (50-70% cheaper than human scribes).

## Design Principles

1. **Report, never interpret** — summarize what was said, never what it means
2. **Doctor always in control** — every summary requires human approval
3. **Zero learning curve** — one button to start, one to stop
4. **Works on any device** — phone, tablet, computer
5. **Portuguese-first** — Brazilian medical vocabulary

## License

Private — all rights reserved.
