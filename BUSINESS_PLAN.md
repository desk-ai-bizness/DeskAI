# Business Plan — Medical AI Scribe

> **Version:** 1.0  
> **Date:** 2026-03-25  
> **Author:** Daniel Toni  
> **Status:** Planning / Pre-MVP

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem & Opportunity](#2-problem--opportunity)
3. [Market Analysis](#3-market-analysis)
4. [Competitive Landscape](#4-competitive-landscape)
5. [Product Strategy](#5-product-strategy)
6. [Business Model & Pricing](#6-business-model--pricing)
7. [Financial Projections](#7-financial-projections)
8. [Go-to-Market Strategy](#8-go-to-market-strategy)
9. [Legal, Regulatory & Compliance](#9-legal-regulatory--compliance)
10. [Team & Hiring Plan](#10-team--hiring-plan)
11. [Funding & Investment](#11-funding--investment)
12. [Risk Assessment](#12-risk-assessment)
13. [Milestones & Timeline](#13-milestones--timeline)
14. [Future Products & Expansion](#14-future-products--expansion)
15. [Exit Strategy](#15-exit-strategy)

---

## 1. Executive Summary

**Medical AI Scribe** is a SaaS tool that listens to doctor-patient consultations, transcribes the conversation, and generates structured clinical documentation — saving physicians 5+ minutes per consultation and allowing them to focus on the patient instead of typing.

### The Opportunity

- **500,000+ active physicians** in Brazil, growing ~30,000/year
- Only **8% of healthcare institutions** have EHR systems — massive digitization wave incoming
- Documentation consumes **~50% of consultation time** (7+ minutes per visit)
- Human medical scribes cost **R$1,500-3,000/month** — AI scribe costs **R$199-349/month**
- The Brazilian healthtech market grew **37.6% in 2024** and Brazil represents **64.8% of all LatAm healthtech investment**

### The Model

- **Subscription SaaS** — monthly per-doctor pricing
- **MVP cost per consultation:** ~R$0.85 (~$0.15 USD) in API costs
- **Target pricing:** R$199-349/month per doctor (unlimited consultations)
- **Gross margin:** 20% at launch → 50%+ at scale (infrastructure costs are largely fixed)
- **Path to R$3M+ ARR** within 24 months with 1,000 paying doctors

### The Strategy

1. Build MVP (3 months, <R$3,000 investment)
2. Free pilot with 5-10 doctors (1 month)
3. Launch with subscription pricing (Month 5)
4. Reach 100 paying doctors by Month 12
5. Raise pre-seed/seed when product-market fit is proven
6. Scale to 1,000+ doctors by Month 24

---

## 2. Problem & Opportunity

### The Doctor's Pain

Brazilian physicians face a documentation crisis:

| Problem | Data Point |
|---------|------------|
| Time spent on documentation per consultation | ~7 minutes (50% of consultation time) |
| Hours lost to paperwork per week | 25+ hours |
| Impact on patient attention | Doctors look at screens, not patients |
| Burnout contribution | Documentation is the #1 cited cause of physician burnout globally |
| Current solutions | Typing during consultation, dictating after, or hiring a secretary |

### The Market Gap

- **88% of clinical staff** report resistance to complex new technology
- **97% of smaller facilities** lack infrastructure for digital health
- Enterprise EHR solutions (MV Sistemas, Philips Tasy) cost R$50,000-500,000 to implement
- Small clinics (1-5 doctors) and solo practitioners are completely underserved
- No affordable, zero-friction documentation tool exists for Brazilian Portuguese

### Why Now

1. **AI maturity** — LLMs (Claude, GPT) now produce reliable Portuguese medical text
2. **ASR maturity** — Deepgram/Whisper handle Brazilian Portuguese with speaker diarization
3. **Cost collapse** — API costs dropped 10x in 2 years. A consultation costs R$0.85, not R$8.50
4. **Regulatory clarity** — CFM Resolution 2.454/2026 (effective August 2026) formally regulates AI in medicine, creating a clear compliance framework
5. **Market timing** — Voa Health raised $3M but the market is far from saturated (60K registered vs. 500K+ total doctors)
6. **Telemedicine boom** — 68% adoption creates natural audio capture opportunities

---

## 3. Market Analysis

### TAM / SAM / SOM

| Metric | Number | Annual Revenue Potential |
|--------|--------|------------------------|
| **TAM** — All physicians in Brazil | 575,000 | R$1.38B/year (at R$199/mo) |
| **SAM** — Private practice, urban, clinical, tech-ready | 250,000-300,000 | R$597M-717M/year |
| **SOM Year 1** — Realistic capture (0.5-2%) | 1,250-6,000 | R$3.0M-14.3M/year |
| **SOM Year 3** — Growth target (3-5%) | 7,500-15,000 | R$17.9M-35.8M/year |

### Key Market Characteristics

| Factor | Detail |
|--------|--------|
| **Geography** | Heavily concentrated in Southeast: São Paulo (26%), Rio de Janeiro (11%), Minas Gerais (10%) |
| **Practice type** | 78% work in private sector (many dual public/private) |
| **Technology adoption** | 68% use telemedicine. WhatsApp is the primary professional communication tool. |
| **Payment preference** | Pix (93% of adults use it). Credit card for subscriptions. Boleto for clinics. |
| **Decision maker** | Solo practitioners decide themselves. Clinics: office manager or medical director. Hospitals: IT/CTO. |
| **Sales cycle** | Solo: 1-2 weeks. Small clinic: 2-4 weeks. Hospital: 3-12 months. |
| **Churn risk** | Healthcare SaaS monthly churn: ~7.5%. 43% of churn happens in first 90 days. |

### EHR Market Context

| EHR Provider | Market Share | Our Opportunity |
|-------------|-------------|----------------|
| MV Sistemas | 68% | Integration partner (Phase 6) |
| Philips Tasy | 63% | Integration partner (later) |
| TOTVS | 57% | Integration partner (later) |
| Oracle Cerner | 49% | Enterprise only, different segment |
| **No EHR (paper/basic)** | **~92% of institutions** | **Primary target market** |

The 92% without EHR systems is our sweet spot — doctors who need simple, affordable digital documentation.

---

## 4. Competitive Landscape

### Direct Competitors in Brazil

| Competitor | Funding | Pricing | Traction | Our Advantage |
|-----------|---------|---------|----------|---------------|
| **Voa Health** | $3M (Prosus) | ~R$333/month (est.) | 60K+ registered, ~600 paying | Cheaper (R$199). Simpler product. Focus on small clinics/solo. |
| **DoctorAssistant.ai** | Bossa Invest | R$139-199/month | Growing, 30 employees | Similar pricing. We differentiate on UX simplicity and mobile-first. |
| **Sofya** | MV Saúde (strategic) | Per-consultation | 500K consultations target | They target enterprise. We target small/solo. |
| **MV med.ai** | Part of MV | Bundled with EHR | Largest EHR in Brazil | They're locked into MV ecosystem. We're EHR-agnostic. |

### Global Competitors (Not Yet Localized for Brazil)

| Competitor | Pricing | Why They're Not a Threat (Yet) |
|-----------|---------|-------------------------------|
| Nuance DAX (Microsoft) | $1,000+/month | English-only. Enterprise-only. US-focused. |
| Abridge | Enterprise | English-only. US hospital focus. |
| Freed | $99-149/month | English-only. No Portuguese. |
| DeepScribe | ~$750/month | English-only. US specialty focus. |
| Nabla | Enterprise | European focus. No Portuguese. |

### Competitive Moat Strategy

| Moat | How We Build It |
|------|----------------|
| **Price** | R$199/month vs. Voa's ~R$333 and DoctorAssistant's R$199. Match on price, win on simplicity. |
| **UX simplicity** | One button to record. One button to stop. Zero learning curve. |
| **Mobile-first** | Phone on desk is the killer workflow. Most competitors are web-first. |
| **Small clinic focus** | 1-5 doctor offices are underserved. Enterprise competitors don't bother. |
| **Portuguese-first** | Deep Brazilian medical vocabulary. Not a translation of an English product. |
| **Doctor relationships** | Pilot feedback loop builds trust. Referral network among physicians. |

---

## 5. Product Strategy

### MVP (Month 1-4): AI Scribe

The minimum product that delivers value:

1. **Record** — Doctor records consultation audio (phone or browser)
2. **Transcribe** — AI transcribes with speaker labels (doctor vs. patient)
3. **Summarize** — AI generates structured clinical summary (reason for visit, symptoms, medications, instructions, next steps)
4. **Review** — Doctor reviews, edits, and approves
5. **Store** — Approved summary becomes part of patient's digital record

**What the MVP is NOT:**
- No clinical decision support (no diagnoses, no ICD codes)
- No EHR integration
- No real-time transcription
- No specialty-specific templates
- No multi-language support

### V2 (Month 9-14): Enhanced Scribe

- Real-time transcription (see transcript as you speak)
- Custom summary templates per specialty
- EHR integration (start with MV Sistemas)
- Clinic-wide analytics dashboard
- Patient-facing simplified summary

### V3 (Month 15-24): Platform

- API-as-a-service (let other healthtechs embed the pipeline)
- Spanish language support (LatAm expansion)
- Desktop agent for telemedicine audio capture
- Advanced analytics (consultation patterns, time savings metrics)

### Future Products (Year 2+)

| Product | Description | Revenue Model |
|---------|-------------|---------------|
| **AI Clinical Assistant** | Answer medical questions, generate patient guidance documents | Higher-tier subscription |
| **Patient Portal** | Patients access their consultation summaries | Included in Pro plan (retention feature) |
| **EHR Lite** | Simple electronic health record for clinics without one | Separate product, R$99/month |
| **AI Scribe API** | API for other healthtechs to embed transcription + summarization | Usage-based (per consultation) |
| **Legal Scribe** | Same technology adapted for legal consultations | New market, same infrastructure |
| **Therapy Scribe** | Adapted for psychotherapy sessions (with extra privacy controls) | New market |
| **Financial Advisory Scribe** | Adapted for financial advisor meetings | New market |

---

## 6. Business Model & Pricing

### Subscription Model

| Plan | Price (BRL/month) | Target Customer | Features |
|------|------------------:|-----------------|----------|
| **Basic** | R$199 | Solo practitioners | Unlimited consultations. Web + mobile. Patient history. Export to PDF. |
| **Pro** | R$349 | Small clinics (2-10 doctors) | Everything in Basic + clinic dashboard + analytics + priority support + custom templates. |
| **Enterprise** | Custom (R$250-500/doctor) | Hospitals, clinic networks | Everything in Pro + EHR integration + dedicated support + SLA + custom deployment + SSO. |

### Why These Prices

| Benchmark | Price |
|-----------|-------|
| Human secretary (documentation only, partial time) | R$1,500-3,000/month |
| Voa Health (estimated) | ~R$333/month |
| DoctorAssistant.ai | R$139-199/month |
| Freed (US, for reference) | $99-149/month (~R$575-863) |
| Our Basic plan | R$199/month |
| Our Pro plan | R$349/month |

At R$199/month, we are:
- **87-93% cheaper** than a human secretary doing documentation
- **40% cheaper** than Voa Health
- **At parity** with DoctorAssistant.ai on the lowest tier
- **50-70% cheaper** than US competitors (even before currency adjustment)

### Discounts & Promotions

| Offer | Discount | Purpose |
|-------|---------|--------|
| Annual billing | 20% off (R$159/month Basic, R$279/month Pro) | Reduce churn, improve cash flow |
| Referral program | 1 month free for referrer + referred | Viral growth among doctors |
| Medical society partnership | 15-20% off through affiliated societies | Distribution channel |
| First 100 customers | 30% off for life (R$139/month) | Build early traction fast |
| Free trial | 7 days unlimited, no credit card required | Low-friction trial |
| Free tier | 5 consultations/month | Keep doctors in ecosystem even if they don't pay yet |

### Payment Processing

| Method | Fee | Expected % of Revenue |
|--------|-----|----------------------|
| **Pix** (Stripe) | 1.19% | 40% (growing) |
| **Credit card** (Stripe) | 3.99% + R$0.39 | 50% |
| **Boleto** (Stripe) | R$3.45 flat | 10% (clinics/hospitals) |

**Blended payment processing cost:** ~2.5-3.0% of revenue.

**Pix Automatico** (launched June 2025) enables automatic recurring Pix payments — perfect for subscriptions. 93% of Brazilian adults use Pix.

---

## 7. Financial Projections

### Unit Economics

| Metric | Value |
|--------|-------|
| **Average Revenue Per User (ARPU)** | R$249/month (blended Basic + Pro) |
| **Cost per consultation (API)** | ~R$0.85 ($0.15) |
| **Consultations per doctor/month** | ~440 (20/day × 22 days) |
| **API cost per doctor/month** | ~R$374 ($66) |
| **Infrastructure cost per doctor** | ~R$5-15 (amortized) |
| **Total cost per doctor/month** | ~R$379-389 |
| **Gross margin (Basic plan)** | -R$180 to -R$190 (negative at R$199!) |
| **Gross margin (Pro plan)** | -R$30 to -R$40 (still negative!) |

### Critical Insight: Margin Problem

At 20 consultations/day, the API cost per doctor ($66/month) exceeds the revenue from the Basic plan minus infrastructure. This means:

1. **Not all doctors do 20 consultations/day.** Average is 4.5/day in Brazil. At 4.5 consultations/day:
   - API cost: ~R$85/month → **Gross margin: R$114 (57%) on Basic, R$264 (76%) on Pro**
2. **Volume discounts reduce API costs.** Deepgram Growth tier (-20%) at $4K/year. Anthropic Batch API (-50%).
3. **Claude Haiku 4.5 is already the cheapest viable model.** Further savings possible with Haiku 3 ($0.25/M tokens vs $1.00/M).

**Revised unit economics (realistic 4.5 consultations/day average):**

| Metric | Basic (R$199) | Pro (R$349) |
|--------|-------------:|------------:|
| Monthly consultations | 99 | 99 |
| API cost/month | R$84 | R$84 |
| Infrastructure/month | R$10 | R$10 |
| Payment processing (3%) | R$6 | R$10 |
| **COGS** | **R$100** | **R$104** |
| **Gross profit** | **R$99 (50%)** | **R$245 (70%)** |
| **Blended gross margin** | | **~60%** |

### Revenue Projections

#### Conservative Scenario

| Month | New Doctors | Churn (5%) | Active Doctors | MRR (R$) | ARR (R$) |
|------:|----------:|-----------:|---------------:|---------:|---------:|
| 1-3 | 0 | 0 | 0 | 0 | 0 |
| 4 | 10 (pilot) | 0 | 10 | 2,490 | 29,880 |
| 5 | 15 | 1 | 24 | 5,976 | 71,712 |
| 6 | 20 | 1 | 43 | 10,707 | 128,484 |
| 9 | 30 | 5 | 112 | 27,888 | 334,656 |
| 12 | 40 | 10 | 225 | 56,025 | 672,300 |
| 18 | 60 | 22 | 520 | 129,480 | 1,553,760 |
| 24 | 80 | 40 | 1,000 | 249,000 | 2,988,000 |

#### Optimistic Scenario (strong product-market fit + referral engine)

| Month | Active Doctors | MRR (R$) | ARR (R$) |
|------:|---------------:|---------:|---------:|
| 6 | 100 | 24,900 | 298,800 |
| 12 | 500 | 124,500 | 1,494,000 |
| 18 | 1,500 | 373,500 | 4,482,000 |
| 24 | 3,500 | 871,500 | 10,458,000 |

### Cost Projections

| Month | API Costs | Infrastructure | Payroll | Marketing | Total Burn | Net (Conservative) |
|------:|----------:|---------------:|--------:|----------:|-----------:|--------------------:|
| 1-3 | R$200 | R$450 | R$0 (solo) | R$500 | R$1,150/mo | -R$1,150 |
| 4-6 | R$3,600 | R$1,000 | R$0 (solo) | R$2,000 | R$6,600/mo | -R$600 to +R$4,100 |
| 7-12 | R$12,000 | R$3,000 | R$40,000 | R$8,000 | R$63,000/mo | -R$7,000 to +R$5,000 |
| 13-18 | R$35,000 | R$5,000 | R$80,000 | R$15,000 | R$135,000/mo | -R$5,500 to +R$30,000 |
| 19-24 | R$70,000 | R$8,000 | R$120,000 | R$25,000 | R$223,000/mo | +R$26,000 to +R$100,000 |

### Break-Even Analysis

| Scenario | Break-Even Point | Doctors Needed |
|----------|-----------------|---------------|
| Solo founder (no payroll) | Month 5-6 | ~30 doctors |
| Small team (4 people) | Month 14-16 | ~350 doctors |
| Full team (8 people) | Month 18-22 | ~700 doctors |

**Cash needed to reach break-even (solo founder):** ~R$15,000-20,000 ($2,600-3,400)
**Cash needed to reach break-even (small team):** ~R$900,000-1,200,000 ($155,000-206,000)

### Investment Needed

| Phase | Investment | Source |
|-------|-----------|--------|
| Phase 0-2 (MVP, solo) | R$3,000-5,000 | Personal savings |
| Phase 3-4 (mobile + pilot) | R$10,000-20,000 | Personal savings or angel |
| Phase 5-6 (team + scale) | R$600,000-1,500,000 | Pre-seed round |
| Year 2 (aggressive growth) | R$3,000,000-8,000,000 | Seed round |

---

## 8. Go-to-Market Strategy

### Phase 1: Pilot (Month 4-5)

**Target:** 5-10 doctors (personal network)

| Channel | Action | Cost |
|---------|--------|------|
| Personal network | LinkedIn messages, WhatsApp, friends of friends | R$0 |
| Medical contacts | Ask pilot doctors to introduce 2-3 colleagues each | R$0 |

**Goal:** Validate product-market fit. Get testimonials. Identify the 3 biggest complaints.

### Phase 2: Early Adopters (Month 6-9)

**Target:** 50-100 doctors

| Channel | Action | Cost/Month |
|---------|--------|----------:|
| **Referral program** | 1 month free for referrer + referred doctor | Variable |
| **LinkedIn organic** | Post weekly about the product (videos of the workflow) | R$0 |
| **LinkedIn ads** | Target physicians in São Paulo, Rio, BH | R$3,000-5,000 |
| **WhatsApp groups** | Join medical WhatsApp groups, offer free trial | R$0 |
| **Medical conferences** | Attend 1-2 regional medical conferences with a demo | R$2,000-5,000/event |
| **Instagram** | Short videos showing the recording → summary workflow | R$1,000-2,000 (ads) |

**Estimated CAC:** R$500-1,000 per doctor

### Phase 3: Growth (Month 10-18)

**Target:** 200-500 doctors

| Channel | Action | Cost/Month |
|---------|--------|----------:|
| **Medical society partnerships** | Partner with 2-3 societies (SBMFC, specialty associations) for co-branded discounts | R$5,000-10,000 |
| **Inside sales** | Hire 1 sales rep targeting small clinics | R$8,000-12,000 |
| **Content marketing / SEO** | Blog posts: "How to save 2 hours/day on documentation" (Portuguese) | R$3,000-5,000 |
| **Case studies** | Publish results from pilot doctors (time saved, satisfaction) | R$0 |
| **Paid search** | Google Ads targeting "prontuário eletrônico", "escrita médica por IA" | R$3,000-5,000 |

**Estimated CAC:** R$800-1,500 per doctor

### Phase 4: Scale (Month 19-24+)

**Target:** 500-3,000+ doctors

| Channel | Action | Cost/Month |
|---------|--------|----------:|
| **National conferences** | Major presence at CBR, SBMFC national events | R$15,000-30,000/event |
| **Field sales team** | 3-5 reps targeting clinics and small hospitals | R$40,000-60,000 |
| **EHR marketplace** | List as plugin/integration in MV Sistemas marketplace | Revenue share |
| **API partnerships** | White-label the engine for other healthtech companies | Variable |
| **PR / Media** | Features in Saúde Business, Exame, medical journals | R$5,000-10,000 |

### Customer Acquisition Funnel

```
Awareness (LinkedIn, conferences, referrals)
         │
         ▼
   Visit website (500 visitors/month)
         │
         ▼
   Start free trial (20% conversion → 100/month)
         │
         ▼
   Complete 5+ consultations in trial (60% activation)
         │
         ▼
   Convert to paid (25% of activated → 15/month)
         │
         ▼
   Retain 12+ months (LTV: R$2,988)
```

---

## 9. Legal, Regulatory & Compliance

### Business Registration

| Step | Detail | Cost | Timeline |
|------|--------|------|----------|
| **Company type** | Sociedade Limitada (LTDA) — Brazilian LLC equivalent | R$5,000-15,000 | 2-4 months |
| **Tax regime** | Simples Nacional (if revenue < R$4.8M/year) | ~6-15.5% effective rate | Immediate |
| **Manager requirement** | Must have a manager who is a physical person resident in Brazil | N/A | N/A |
| **CNPJ registration** | Federal tax ID | Included in formation cost | 2-4 weeks |
| **Municipal license** | ISS registration in city of operation | R$500-1,000 | 2-4 weeks |
| **Bank account** | Business account (Nubank PJ, Itaú, Bradesco) | R$0-50/month | 1-2 weeks |

### Tax Implications

#### Under Simples Nacional (Revenue < R$4.8M/year)

| Revenue Band (12 months) | Effective Rate (Anexo V) | With Fator R ≥ 28% (Anexo III) |
|---|---:|---:|
| Up to R$180K | 15.5% | 6.0% |
| R$180K - R$360K | 18.0% | 11.2% |
| R$360K - R$720K | 19.5% | 13.5% |
| R$720K - R$1.8M | 20.5% | 16.0% |
| R$1.8M - R$3.6M | 23.0% | 21.0% |
| R$3.6M - R$4.8M | 30.5% | 33.0% |

**Fator R optimization:** If payroll expenses are ≥ 28% of gross revenue, the company qualifies for Anexo III (lower rates, starting at 6%). This is a critical tax planning consideration when hiring — higher payroll can actually reduce overall tax burden.

**2026-2033 Tax Reform Note:** ISS and ICMS will be replaced by IBS; PIS/COFINS by CBS. Combined IBS+CBS rate may approach 28%. Simples Nacional survives but with adaptations. Get an accountant who tracks the reform timeline.

### Regulatory Compliance

#### LGPD (Lei Geral de Proteção de Dados — Lei 13.709/2018)

| Requirement | Our Implementation | Priority |
|-------------|-------------------|----------|
| **Sensitive data classification** | All health data (audio, transcripts, summaries) treated as sensitive personal data | Day 1 |
| **Explicit consent** | Digital consent form before first recording. Verbal confirmation at start of each consultation. | Day 1 |
| **Data Processing Agreement (DPA)** | Signed with Deepgram and Anthropic. Include ANPD-approved Standard Contractual Clauses (mandatory since Aug 2025). | Before launch |
| **Encryption at rest** | PostgreSQL TDE. S3 SSE-S3. CPF/phone encrypted with pgcrypto. | Day 1 |
| **Encryption in transit** | TLS 1.3 everywhere. HSTS. No HTTP. | Day 1 |
| **Audit trail** | Immutable audit_log table. Every data access logged. | Day 1 |
| **Data portability** | Export endpoint (JSON/CSV) for all patient data. | Before launch |
| **Right to deletion** | Soft delete + scheduled hard delete (respecting 20-year medical record retention). | Before launch |
| **DPO appointment** | Small company exemption available. Maintain communication channel for data subjects. | Before launch |
| **Breach notification** | Automated alerts. Process to notify ANPD within 48 hours. | Before launch |
| **Data minimization** | Audio deleted after 90 days. Only transcript + summary retained. | Phase 5 |

**Penalties for non-compliance:** Up to 2% of revenue in Brazil, capped at R$50 million per infraction.

#### CFM (Conselho Federal de Medicina)

| Regulation | Requirement | Our Compliance |
|-----------|-------------|----------------|
| **Resolução CFM 2.454/2026** (AI in Medicine, effective August 2026) | AI must act as support tool only. Physician has final authority. Governance structures required. | Our product is doctor-reviewed by design. Every summary requires physician approval. |
| **Resolução CFM 2.314/2022** (Telemedicine) | Patient consent for telemedicine and data transmission. | Digital consent form. Verbal confirmation per consultation. |
| **Código de Ética Médica, Art. 73** | Physician cannot reveal patient information without consent. | All recordings and summaries are per-patient consented. |
| **Lei 13.787/2018** (Electronic Medical Records) | 20-year retention. Digital signature (ICP-Brasil). Integrity and authenticity. | 20-year data retention. ICP-Brasil compatible signatures (Phase 5). |

#### ANVISA (Agência Nacional de Vigilância Sanitária)

| Question | Answer |
|----------|--------|
| Is our product classified as SaMD (Software as a Medical Device)? | **No** — it is an administrative documentation tool, not clinical decision support. It does not diagnose, suggest treatments, or interpret data. |
| What could trigger SaMD classification? | Adding features like ICD-10 code suggestions, differential diagnosis, or treatment recommendations. |
| Do we need ANVISA registration? | **No** — administrative software is explicitly excluded from medical device classification under RDC 657/2022. |
| What documentation should we maintain? | Internal risk assessment documenting why the product is NOT SaMD. Clear marketing materials stating it is a documentation tool, not a clinical tool. |

#### Patient Consent for Recording

| Requirement | Implementation |
|-------------|---------------|
| **Written/digital consent** | Digital consent form accepted before first use (checkbox + timestamp). Covers: audio recording, AI processing, international data transfer, data retention. |
| **Verbal confirmation** | At start of each consultation, doctor confirms recording is active. |
| **Right to refuse** | Patient can opt out at any time. Consultation proceeds normally without recording. |
| **Consent record** | Stored in `patient_consents` table. Immutable. Linked to patient record. |
| **Withdrawal** | Patient can withdraw consent. All data deleted (respecting retention requirements). |

### Legal Actions Required (Chronological)

| Action | When | Estimated Cost | Provider |
|--------|------|---------------|----------|
| Register LTDA company | Month 1 | R$5,000-15,000 | Accountant + lawyer |
| Simples Nacional opt-in | Month 1 | Included above | Accountant |
| Draft Terms of Service | Before launch | R$3,000-5,000 | Healthcare lawyer |
| Draft Privacy Policy (LGPD-compliant) | Before launch | R$3,000-5,000 | Data protection lawyer |
| Draft Patient Consent Form | Before launch | R$2,000-3,000 | Healthcare lawyer |
| Sign DPA with Deepgram (+ SCCs) | Before launch | R$2,000-4,000 | Data protection lawyer |
| Sign DPA with Anthropic (+ SCCs) | Before launch | R$2,000-4,000 | Data protection lawyer |
| LGPD compliance audit | Month 6 | R$10,000-20,000 | Specialized firm |
| E&O / Cyber insurance | Month 6 | R$5,000-15,000/year | Insurance broker |
| Intellectual property (trademark) | Month 6 | R$2,000-4,000 | IP lawyer |
| CFM 2.454/2026 compliance review | By August 2026 | R$5,000-10,000 | Healthcare regulatory lawyer |
| **Total legal costs (Year 1)** | | **R$39,000-85,000** | |

---

## 10. Team & Hiring Plan

### Phase 1-4: Solo Founder (Months 1-5)

Daniel builds the MVP alone. All engineering, product, and initial sales.

**Cost:** R$0 payroll (personal investment in time).

### Phase 5: First Hires (Month 6-8)

| Role | Responsibility | Salary (CLT gross) | Total Cost (+ 80% burden) |
|------|---------------|-------------------:|-------------------------:|
| **Senior Python Developer** | Backend, AI pipeline, infrastructure | R$18,000-22,000 | R$32,400-39,600 |
| **Mid Frontend/Mobile Developer** | Next.js + React Native | R$10,000-14,000 | R$18,000-25,200 |
| **Monthly payroll** | | | **R$50,400-64,800** |

### Phase 6: Growth Team (Month 12-14)

| Role | Responsibility | Salary (CLT gross) | Total Cost |
|------|---------------|-------------------:|----------:|
| **Product/UX Designer** | Product design, user research, onboarding flows | R$7,000-10,000 | R$12,600-18,000 |
| **Customer Success / Sales** | Onboard doctors, handle support, initial sales | R$5,000-8,000 | R$9,000-14,400 |
| **Monthly payroll (4 people + founder)** | | | **R$72,000-97,200** |

### Phase 7: Scaling Team (Month 18-24)

| Role | Responsibility | Salary (CLT gross) | Total Cost |
|------|---------------|-------------------:|----------:|
| **2nd Backend Developer** | Scale infrastructure, EHR integrations | R$14,000-18,000 | R$25,200-32,400 |
| **Inside Sales Rep** | Outbound sales to clinics | R$6,000-10,000 | R$10,800-18,000 |
| **Marketing / Growth** | Content, SEO, paid acquisition | R$6,000-10,000 | R$10,800-18,000 |
| **Monthly payroll (7-8 people + founder)** | | | **R$118,800-165,600** |

### Total Monthly Burn by Phase

| Phase | Payroll | Infrastructure | Marketing | Legal/Admin | Total Burn |
|-------|--------:|---------------:|----------:|------------:|-----------:|
| Solo (M1-5) | R$0 | R$500 | R$1,000 | R$1,000 | R$2,500 |
| First hires (M6-8) | R$55,000 | R$2,000 | R$5,000 | R$3,000 | R$65,000 |
| Growth team (M12-14) | R$85,000 | R$5,000 | R$10,000 | R$5,000 | R$105,000 |
| Scaling (M18-24) | R$140,000 | R$10,000 | R$20,000 | R$8,000 | R$178,000 |

### Key Hire Profiles

**Senior Python Developer (First Hire, Most Critical):**
- FastAPI + async Python expertise
- Experience with AI/ML pipelines (LLM APIs, prompt engineering)
- PostgreSQL + Redis + Celery
- AWS/cloud infrastructure
- Bonus: healthcare/biotech background
- Where to find: LinkedIn (Brazil has a strong Python community), PythonBrasil conferences, communities

**Customer Success / Sales (Second Most Critical):**
- Experience selling to doctors or healthcare professionals
- Medical vocabulary knowledge
- Empathetic, patient communication style
- WhatsApp-native (this is how doctors communicate)
- Where to find: healthtech companies (Voa Health, iClinic, Doctoralia alumni)

---

## 11. Funding & Investment

### Bootstrapping Phase (Months 1-5)

| Item | Cost |
|------|------|
| API credits (Deepgram + Claude testing) | R$300 |
| Infrastructure (Railway + Supabase + domain) | R$500/month × 5 = R$2,500 |
| Apple Developer + Google Play | R$700 |
| **Total to launch** | **R$3,500** |

This is buildable from personal savings with no external funding.

### Pre-Seed Round (Month 8-12)

Raise when product-market fit is proven (50+ paying doctors, positive unit economics).

| Metric | Target |
|--------|--------|
| **Amount** | R$500,000 - R$1,500,000 (US$85K-260K) |
| **Valuation** | R$5M-15M (based on 10-30x ARR multiple) |
| **Use of funds** | 60% team (first 2 hires), 20% marketing, 10% infrastructure, 10% legal |
| **Runway** | 12-18 months |
| **Investor type** | Angel investors, micro-VCs, accelerators |

**Potential investors:**
- Angel groups: Anjos do Brasil, GVAngels, Cubo Itaú network
- Accelerators: Startup Farm, ACE, InovaBra
- Micro-VCs: Canary, Maya Capital
- Healthcare-focused: Bossa Invest (funded DoctorAssistant.ai)

### Seed Round (Month 18-24)

Raise when scaling aggressively (200+ paying doctors, R$500K+ ARR).

| Metric | Target |
|--------|--------|
| **Amount** | R$3,000,000 - R$8,000,000 (US$500K-1.4M) |
| **Valuation** | R$15M-50M |
| **Use of funds** | 50% team (scale to 8-10 people), 25% marketing/sales, 15% product, 10% infrastructure |
| **Runway** | 18-24 months |
| **Investor type** | Seed-stage VCs |

**Potential investors:**
- Kaszek (avg seed: $5M, very active in Brazil healthtech)
- Prosus Ventures (funded Voa Health — may be a conflict, but could also be strategic)
- QED Investors (funded Carecode, active in Brazil health)
- Canary (very active Brazilian VC)
- Endeavor Catalyst (seed-Series A, strong network)
- Bossa Invest (funded DoctorAssistant.ai — sector expertise)

### Comparable Raises in Brazilian Healthtech (2024-2025)

| Company | Stage | Amount | Investor | Valuation |
|---------|-------|--------|----------|-----------|
| Voa Health | Seed | US$3M | Prosus | >R$100M |
| Carecode | Pre-seed | US$4.3M | a16z + QED | Undisclosed |
| DoctorAssistant.ai | Seed | Undisclosed | Bossa Invest | Undisclosed |
| Marisa.Care | Pre-seed | US$1.5M | Various | Undisclosed |
| Huna | Pre-seed | US$1.5M | Various | Undisclosed |

---

## 12. Risk Assessment

### Business Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | **Competition from Voa Health** ($3M funded, first-mover) | High | Certain | Differentiate on price (R$199 vs ~R$333), UX simplicity, and small clinic focus. Voa targets enterprise. We target solo/small. |
| 2 | **Doctor adoption resistance** (88% report tech resistance) | High | High | Dead-simple UX. Free trial. Prove time savings in first week. WhatsApp onboarding support. |
| 3 | **Thin/negative margins** on high-volume doctors | Medium | Medium | Use Claude Haiku (cheapest). Negotiate volume discounts. Cap consultations per plan tier if needed. |
| 4 | **High churn** (healthcare SaaS: 7.5% monthly) | High | High | 90-day intensive onboarding. Weekly check-ins during first month. Track leading indicators (consultations/week declining = churn risk). |
| 5 | **LGPD non-compliance** (fines up to R$50M) | Critical | Low (if we prepare) | Build compliance from day 1. LGPD audit before scaling. Insurance. |
| 6 | **Data breach** (patient health data exposed) | Critical | Low | Encryption everywhere. Minimal data retention. Incident response plan. Cyber insurance. |
| 7 | **API provider risk** (Deepgram or Anthropic deprecate/reprice) | Medium | Low | Multi-provider fallback. Long-term: proprietary ASR model. |
| 8 | **Key person risk** (solo founder) | High | If solo | Document everything. Managed services (no custom infra). Find co-founder or hire senior dev early. |
| 9 | **ANVISA reclassification** (if we add clinical features) | High | Low (if we stay disciplined) | Never add diagnostic/clinical features without regulatory review. Internal documentation of why we are NOT SaMD. |
| 10 | **Patent/IP litigation** from competitors | Low | Low | Patent search before launch. Freedom-to-operate analysis if fundraising. |

### Financial Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Running out of money before PMF | Fatal | Keep burn minimal (solo founder until PMF). Target < R$20K to reach first revenue. |
| Currency risk (API costs in USD, revenue in BRL) | Medium | If BRL depreciates significantly, margins compress. Hedge by negotiating annual API contracts. |
| Price war with competitors | Medium | Build on value (time saved, doctor satisfaction), not just price. Lock in annual subscribers at discounted rates. |
| Slower-than-expected adoption | High | Have 6-month runway beyond projected break-even. Diversify acquisition channels. Consider pivoting to API-as-a-service if B2C adoption is too slow. |

---

## 13. Milestones & Timeline

### Year 1 (Months 1-12)

| Month | Milestone | Key Metric |
|------:|-----------|------------|
| 1-2 | Phase 0: AI pipeline proof of concept | 5 test consultations, 3 physician reviews |
| 3-4 | Phase 1: Backend API deployed | API live, all endpoints working |
| 5-6 | Phase 2: Web app live | Functional dashboard |
| 7-8 | Phase 3: Mobile app live (iOS + Android) | App Store + Play Store listing |
| 8-9 | Phase 4: Free pilot with 5-10 doctors | NPS > 30, edit rate < 30% |
| 10 | Launch: start charging (R$199/R$349) | First paying customer |
| 11 | 50 paying doctors | R$12,450 MRR |
| 12 | 100 paying doctors, begin fundraising | R$24,900 MRR, ~R$300K ARR |

### Year 2 (Months 13-24)

| Month | Milestone | Key Metric |
|------:|-----------|------------|
| 13-14 | Close pre-seed round | R$500K-1.5M raised |
| 14-15 | First 2 hires (Python dev + frontend dev) | Team of 3 |
| 16 | LGPD compliance audit complete | Compliant |
| 17-18 | 300 paying doctors. Real-time transcription launched. | R$75K MRR |
| 19-20 | EHR integration (MV Sistemas) launched | First enterprise customer |
| 21-22 | 500+ paying doctors. Customer Success hire. | R$125K MRR |
| 23-24 | 1,000 paying doctors. Begin seed fundraising. | R$249K MRR, ~R$3M ARR |

### Year 3 (Months 25-36)

| Quarter | Milestone |
|---------|----------|
| Q1 | Close seed round (R$3-8M). Scale team to 8-10. |
| Q2 | Launch Spanish language (Mexico, Colombia, Argentina). |
| Q3 | Launch API-as-a-service. 2,000+ paying doctors. |
| Q4 | Launch in Portugal. Consider second product (EHR Lite or AI Clinical Assistant). |

---

## 14. Future Products & Expansion

### Product Expansion Roadmap

```
Year 1:  AI Scribe (core product)
            │
Year 2:  ┌──┴──┐
         │     │
    EHR  │   API-as-a-
    Lite │   Service
         │
Year 3:  ┌──┴──────┐
         │         │
    AI Clinical  Patient
    Assistant    Portal
         │
Year 4+: ┌──┴──────────┐
         │             │
    Beyond Medical   International
    (Legal, Therapy) (Portugal, LATAM)
```

### Revenue Diversification

| Revenue Stream | Timeline | Revenue Model | TAM |
|---------------|----------|---------------|-----|
| **AI Scribe subscriptions** | Month 1+ | R$199-349/month per doctor | R$1.38B (Brazil) |
| **Enterprise contracts** | Month 18+ | R$250-500/doctor/month (annual contracts) | R$500M |
| **API-as-a-service** | Month 24+ | R$0.50-2.00 per consultation | R$200M (healthtech developers) |
| **EHR Lite** | Month 30+ | R$99/month per clinic | R$500M (clinics without EHR) |
| **International (LATAM + Portugal)** | Month 24+ | Same pricing adapted to local market | R$3-5B |
| **Beyond healthcare** | Year 3+ | Adapted pricing per vertical | R$10B+ (legal, therapy, finance) |

### Geographic Expansion Priority

| Market | When | Why | Competitive Landscape |
|--------|------|-----|----------------------|
| **Portugal** | Month 24 | Same language. Virtually zero competition. EU market entry. | Almost no AI scribe competitors |
| **Colombia** | Month 30 | Spanish-speaking, growing healthtech. Nubank already operates there. | Limited local competition |
| **Mexico** | Month 30 | Largest Spanish-speaking market. Strong healthtech investment. | Some US competitors entering |
| **Argentina** | Month 36 | Large physician population. Economic volatility = risk. | Limited competition |
| **Chile** | Month 36 | Stable economy. Smaller market. | Limited competition |

---

## 15. Exit Strategy

### Potential Exit Paths

| Path | Timeline | Valuation Range | Likely Acquirers |
|------|----------|----------------|------------------|
| **Acquisition by Brazilian EHR** | Year 3-5 | R$30M-100M | MV Sistemas, TOTVS, Philips Tasy |
| **Acquisition by global AI scribe** | Year 3-5 | R$50M-200M | Nabla, Abridge, Microsoft (Nuance) |
| **Acquisition by LatAm healthtech** | Year 4-6 | R$100M-500M | Docplanner (Doctoralia), Dr. Consulta, Alice |
| **IPO (long-term)** | Year 7-10 | R$500M+ | If revenue exceeds R$50M ARR |
| **Stay private / profitable** | Ongoing | N/A | If margins are strong and growth is organic |

### Valuation Benchmarks

| Metric | Multiplier | At R$3M ARR | At R$10M ARR | At R$30M ARR |
|--------|-----------|------------|-------------|-------------|
| Revenue multiple (SaaS) | 10-20x | R$30M-60M | R$100M-200M | R$300M-600M |
| Revenue multiple (healthtech premium) | 15-30x | R$45M-90M | R$150M-300M | R$450M-900M |

Voa Health's valuation at $3M funding was >R$100M with ~R$5M ARR (20x+ revenue multiple), which confirms healthtech premium valuations in Brazil.

---

## Appendix A: Financial Model Summary

### 24-Month P&L (Conservative Scenario)

| | M1-3 | M4-6 | M7-9 | M10-12 | M13-18 | M19-24 |
|---|---:|---:|---:|---:|---:|---:|
| **Paying Doctors** | 0 | 43 | 112 | 225 | 520 | 1,000 |
| **Revenue** | R$0 | R$31K | R$84K | R$168K | R$777K | R$1,494K |
| **COGS (API + Infra)** | R$2K | R$14K | R$37K | R$70K | R$280K | R$540K |
| **Gross Profit** | -R$2K | R$17K | R$47K | R$98K | R$497K | R$954K |
| **OpEx (team + marketing)** | R$5K | R$20K | R$195K | R$315K | R$840K | R$1,182K |
| **Net Income** | -R$7K | -R$3K | -R$148K | -R$217K | -R$343K | -R$228K |
| **Cumulative Cash** | -R$7K | -R$10K | -R$158K | -R$375K | -R$718K | -R$946K |

**Cash needed through break-even: ~R$1M** (covered by pre-seed round)

### Key Financial KPIs to Track

| KPI | Target (Month 12) | Target (Month 24) |
|-----|------------------:|------------------:|
| MRR | R$25,000+ | R$249,000+ |
| ARR | R$300,000+ | R$3,000,000+ |
| Paying doctors | 100+ | 1,000+ |
| Gross margin | 55%+ | 65%+ |
| Monthly churn | < 5% | < 3% |
| CAC | < R$1,500 | < R$1,000 |
| LTV | > R$2,500 | > R$5,000 |
| LTV:CAC ratio | > 2:1 | > 5:1 |
| NPS | > 40 | > 60 |
| Doctor edit rate | < 25% | < 15% |

---

## Appendix B: Immediate Next Steps (Week 1)

```
[ ] Record 3-5 mock consultations with a friend
[ ] Sign up for Deepgram ($200 free credit)
[ ] Sign up for Anthropic API (pay-as-you-go)
[ ] Build pipeline.py (Phase 0)
[ ] Test with recordings → review output quality
[ ] Show to 2-3 doctors → get honest feedback
[ ] Decision: proceed / pivot / abandon
[ ] If proceed: register LTDA (start the 2-4 month process)
[ ] If proceed: begin FastAPI backend (Phase 1)
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **ANVISA** | Agência Nacional de Vigilância Sanitária — Brazilian FDA equivalent |
| **ARR** | Annual Recurring Revenue |
| **ASR** | Automatic Speech Recognition (speech-to-text) |
| **CAC** | Customer Acquisition Cost |
| **CFM** | Conselho Federal de Medicina — Brazilian Medical Council |
| **CNPJ** | Cadastro Nacional da Pessoa Jurídica — Brazilian business tax ID |
| **CPF** | Cadastro de Pessoas Físicas — Brazilian individual tax ID |
| **CRM** | Conselho Regional de Medicina — Regional Medical Council (also: doctor's license number) |
| **DPA** | Data Processing Agreement |
| **EHR** | Electronic Health Record |
| **LGPD** | Lei Geral de Proteção de Dados — Brazilian GDPR equivalent |
| **LLM** | Large Language Model |
| **LTDA** | Sociedade Limitada — Brazilian LLC equivalent |
| **LTV** | Lifetime Value (of a customer) |
| **MRR** | Monthly Recurring Revenue |
| **NPS** | Net Promoter Score |
| **SaMD** | Software as a Medical Device |
| **SCC** | Standard Contractual Clauses (for international data transfer) |
| **SUS** | Sistema Único de Saúde — Brazilian public healthcare system |
