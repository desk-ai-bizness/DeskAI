# Phase 1: Documentation Consistency Audit

**Auditor**: Agent T2
**Commit**: 75715f2

---

## Findings

| # | Severity | Document(s) | Issue | Recommendation | Pre-Inv Ref |
|---|----------|-------------|-------|----------------|-------------|
| DOC-01 | MEDIUM | `CLAUDE.md` vs `docs/implementation-prompt.md` vs `.ai-utils/implementation-prompt.md` | **Reading order conflict.** CLAUDE.md (lines 28-33) prescribes: `1. ai-context-rules → 2. business-rules → 3. tech-specs → 4. task file → 5. @task-manager`. `docs/implementation-prompt.md` (lines 7-11) prescribes: `1. business-rules → 2. tech-specs → 3. ai-context-rules → 4. task file → 5. @task-manager`. `.ai-utils/implementation-prompt.md` (lines 7-11) prescribes: `1. ai-context-rules → 2. business-rules → 3. tech-specs → 4. task file → 5. @task-manager`. All three documents claim to be the instruction set for AI agents, but they disagree on which file to read first. | Standardize on one reading order across all three files. The conflict priority order (CLAUDE.md lines 36-40) is consistent across docs, so the reading order is the only divergence. | DOC1 |
| DOC-02 | LOW | `docs/implementation-prompt.md` vs `.ai-utils/implementation-prompt.md` | **Two divergent copies.** These files are nearly identical (63 lines each, same structure) but differ in reading order: `docs/` copy puts business-rules first (line 7); `.ai-utils/` copy puts ai-context-rules first (line 7). The rest of the files are byte-for-byte identical, including the relative path style (`.ai-utils/` uses `./docs/...` prefixes, `docs/` does not). | Delete one copy and make the other canonical. If both must exist, make `.ai-utils/` a symlink or add a note saying which is authoritative. | DOC2 |
| DOC-03 | LOW | `docs/architecture/01-repository-layout.md` | **"Should mirror" claim is false.** Lines 37-38 state: "Its [CLAUDE.md] content should mirror the instructions in `docs/implementation-prompt.md`, including: The mandatory reading order for project documentation." In reality, CLAUDE.md reading order does NOT mirror either implementation-prompt.md copy. | Update the repo layout doc to reflect actual relationship, or align CLAUDE.md's reading order with the authoritative implementation prompt. | DOC3 |
| DOC-04 | LOW | `docs/mvp-technical-specs.md` vs `docs/architecture/03-contract-inventory.md` | **URL parameter naming inconsistency.** Tech specs section 17 (lines 707-713) uses `{consultation_id}` in all URL paths. Contract inventory section 2 (lines 105, 176-177, 206-207, 279, 296) uses `{id}`. The lifecycle doc (02-consultation-lifecycle.md lines 81-88, 107), requirements traceability matrix (01-requirements-traceability-matrix.md), backend architecture doc (02-backend-architecture.md lines 405-409), and data-flow doc (04-data-flow-and-configuration.md line 57) all use `{id}`. The tech specs is the ONLY document using `{consultation_id}`. | Standardize to `{id}` in tech specs section 17 to match all other documents. Or if `{consultation_id}` is preferred for clarity, update all 5+ other documents. | DOC4 |
| DOC-05 | INFO | `docs/requirements/05-decision-log.md` DEC-007 | **Stale note about Section 13 title already resolved.** DEC-007 (line 87) states: "Technical specs section 13 title should be updated to 'AI Processing Layer.'" The title HAS been updated (tech specs line 561: `## 13. AI Processing Layer`). The decision log note implies it is still pending. | Remove or mark the note as "Done" to avoid confusion. | DOC5 |
| DOC-06 | HIGH | `README.md` | **Local filesystem path leakage.** Root README.md (lines 56-59, 78, 92) contains absolute local paths: `(/Users/gabrielsantiago/Documents/DeskAI/docs/ai-context-rules.md)`, `(/Users/gabrielsantiago/Documents/DeskAI/docs/mvp-business-rules.md)`, etc. These expose a developer's local filesystem structure and are broken links for any other user. | Replace with relative paths: `(docs/ai-context-rules.md)`, `(docs/mvp-business-rules.md)`, etc. | DOC6 |
| DOC-07 | N/A | State machine across docs | **State machine IS consistent across all documents** (verified). `mvp-business-rules.md` section 16 defines 7 states with implementation note explaining `recording` and `processing_failed` as refinements. `02-consultation-lifecycle.md` section 1 defines the same 7 states with identical mapping. `03-contract-inventory.md` ConsultationView status field (line 131) lists all 7 states: `started | recording | in_processing | processing_failed | draft_generated | under_physician_review | finalized`. `04-data-flow-and-configuration.md` lifecycle diagram matches. Tech specs section 17 endpoint list matches lifecycle transitions. | No action needed. | DOC7 |
| DOC-08 | LOW | `CLAUDE.md` vs `docs/ai-context-rules.md` | **Conflict priority order subtle mismatch.** CLAUDE.md (lines 36-40) lists 5 tiers: `1. business-rules → 2. tech-specs → 3. ai-context-rules → 4. @task-manager → 5. CLAUDE.md`. ai-context-rules.md section 1 (lines 12-16) lists 3 tiers: `1. business rules → 2. tech specs → 3. this AI context rules file`. The ai-context-rules file omits @task-manager and CLAUDE.md from priority. This is not technically contradictory (it only lists files it knows about), but an agent reading ONLY ai-context-rules.md would not know CLAUDE.md or @task-manager exist in the hierarchy. | No change strictly required, but for completeness ai-context-rules.md could note that CLAUDE.md and @task-manager exist below it in priority. |
| DOC-09 | MEDIUM | `docs/ai-context-rules.md` | **Missing TDD exemption for static assets.** ai-context-rules.md section 6 (lines 58-63) says "Apply TDD across all applicable test types" but does not list TDD exemptions. CLAUDE.md (lines 163-167) and tech specs section 23 (lines 907-912) both explicitly exempt pure config files, static assets, and exploratory prototypes. An agent reading only ai-context-rules.md might apply TDD to CSS files. | Add TDD exemptions to ai-context-rules.md section 6, or add a cross-reference to tech specs section 23. |
| DOC-10 | LOW | `docs/requirements/03-plan-entitlements.md` vs `docs/architecture/03-contract-inventory.md` | **BFF response example omits fields present in full contract.** Plan entitlements doc section 5 (lines 124-139) shows a BFF response example with `entitlements` containing 5 fields. Contract inventory's UserProfileView (lines 50-68) shows `entitlements` with 7 fields (adds `consultations_used_this_month` and `trial_days_remaining`). The plan doc is a simplified example, not a spec, so this is not a contradiction, but could mislead. | Add a note to plan-entitlements.md that the BFF response example is simplified and the full shape is in the contract inventory. |
| DOC-11 | LOW | `docs/requirements/05-decision-log.md` | **DEC-008 references wrong previous OI number.** Line 97: "Resolves: Open Issue OI-006, previously OPEN-005". The OI numbering uses `OI-NNN` format and the OPEN numbering uses `OPEN-NNN` format. `OPEN-005` is not referenced anywhere else in the decision log or task manager. The task manager's OI-006 (line 131) is about patient endpoints, which aligns. | Remove the "previously OPEN-005" reference since OPEN-005 is a dangling identifier. |
| DOC-12 | LOW | `tasks/@task-manager.md` | **Active blockers section stale.** Line 84 says "Begin Task 009" as the next action, but Task 009 is already completed (line 100, status: done). The section header says "List only blockers that currently prevent progress" but it shows an outdated action. | Update active blockers to reflect current state ("Begin Task 010") or leave the table empty since there are no blockers. |
| DOC-13 | INFO | `docs/mvp-business-rules.md` section 16 | **Implementation note reference is precise.** Line 156 states "See `docs/requirements/02-consultation-lifecycle.md` for the complete state machine." This cross-reference is valid and the lifecycle doc section 1 (lines 23-35) explicitly maps the 5 business states to 7 implementation states. | No action needed. Good cross-referencing. |
| DOC-14 | LOW | `README.md` | **Delivery state section is stale.** Lines 88-92 mention Tasks 001-003 status but the project is at Task 009 completed (73% done). The README was last meaningfully updated around Task 003 completion. | Update "Current Delivery State" section or replace with a pointer to @task-manager.md for live status. |
| DOC-15 | INFO | `docs/architecture/03-contract-inventory.md` | **`patients.yaml` contract file referenced but scope is minimal.** Contract inventory section 2 defines patient endpoints (POST/GET /v1/patients) with CreatePatientRequest and PatientView schemas. However, the contracts directory listing (section 1, line 13-18) does not list a `patients.yaml` file. The HTTP directory lists: auth.yaml, consultations.yaml, review.yaml, exports.yaml, ui-config.yaml, errors.yaml. No patients.yaml. | Add `patients.yaml` to the contracts directory listing in 03-contract-inventory.md section 1, or note that patient schemas are embedded in consultations.yaml. |

---

## Cross-Reference Matrix

| Topic | CLAUDE.md | ai-context-rules | business-rules | tech-specs | contract-inventory | lifecycle | plan-entitlements | failure-matrix | decision-log | impl-prompt (docs/) | impl-prompt (.ai-utils/) |
|-------|-----------|-------------------|----------------|------------|-------------------|-----------|-------------------|----------------|--------------|---------------------|--------------------------|
| Reading order | ai-ctx first | N/A (is 1st) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | biz-rules first | ai-ctx first |
| Priority (conflicts) | biz > tech > ai-ctx > mgr > claude | biz > tech > ai-ctx | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Plan types | free_trial, plus, pro | N/A | free_trial, plus, pro | free_trial, plus, pro | free_trial, plus, pro (UserProfileView) | N/A | free_trial, plus, pro (matrix) | free_trial mentioned | DEC-002 references matrix | N/A | N/A |
| Consultation states (count) | 7 | N/A | 7 (5 biz + 2 impl) | N/A | 7 (ConsultationView.status) | 7 (full definition) | N/A | 7 (implied) | DEC-005 explains additions | N/A | N/A |
| URL param name | N/A | N/A | N/A | `{consultation_id}` | `{id}` | `{id}` | N/A | N/A | N/A | N/A | N/A |
| Transcription provider | N/A | N/A | ElevenLabs (sec 13) | ElevenLabs (ADR-006) | N/A | N/A | N/A | N/A | DEC-001 (ElevenLabs) | N/A | N/A |
| LLM provider | N/A | N/A | N/A | Claude API (ADR-007) | N/A | N/A | N/A | N/A | DEC-007 (Claude) | N/A | N/A |
| Section 13 title | N/A | N/A | N/A | "AI Processing Layer" (CORRECT) | N/A | N/A | N/A | N/A | Says "should be updated" (STALE) | N/A | N/A |
| TDD exemptions | Listed (3 types) | NOT listed | N/A | Listed (4 types) | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Auth method | email+password | N/A | email+password | email+password (Cognito) | email+password (POST /v1/auth/session) | N/A | N/A | Cognito failures listed | N/A | N/A | N/A |
| Environments | dev, prod | N/A | N/A | dev, prod | N/A | N/A | N/A | N/A | ADR-004 | N/A | N/A |
| Local path leaks | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE |
| README local paths | **YES** (6 occurrences) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

---

## Pre-Investigation Verification

| Pre-Inv # | Status | Notes |
|-----------|--------|-------|
| DOC1 | **CONFIRMED** | CLAUDE.md reading order (ai-context first) conflicts with docs/implementation-prompt.md (business-rules first). See finding DOC-01. Three-way disagreement: CLAUDE.md and .ai-utils/ copy agree (ai-context first), docs/ copy disagrees (business-rules first). |
| DOC2 | **CONFIRMED** | Two divergent copies exist. Files are identical except for reading order (line 7 in each). `docs/` puts business-rules first, `.ai-utils/` puts ai-context-rules first. See finding DOC-02. |
| DOC3 | **CONFIRMED** | `01-repository-layout.md` line 38 states CLAUDE.md "should mirror the instructions in `docs/implementation-prompt.md`" — but reading orders do not match. See finding DOC-03. |
| DOC4 | **CONFIRMED** | Tech specs section 17 uses `{consultation_id}`; contract inventory, lifecycle doc, requirements traceability, backend architecture, and data-flow doc all use `{id}`. Tech specs is the sole outlier. See finding DOC-04. |
| DOC5 | **CONFIRMED** | DEC-007 note says "section 13 title should be updated to AI Processing Layer" — but it was already updated (tech specs line 561: `## 13. AI Processing Layer`). The decision log note is stale. See finding DOC-05. |
| DOC6 | **REFUTED** | Root `README.md` lines 56-59, 78, 92 contain 6 local filesystem paths: `/Users/gabrielsantiago/Documents/DeskAI/...`. Pre-investigation claimed "No local file path leaks (README paths cleaned up)" — this is WRONG. The paths are still present. See finding DOC-06. |
| DOC7 | **CONFIRMED** | State machine is fully consistent across all documents. Business rules define 7 states (5 business + 2 implementation refinements), lifecycle doc defines the same 7 with identical transitions, contract inventory ConsultationView enumerates all 7, and the data-flow diagram matches. See finding DOC-07. |

---

## Summary Statistics

- **Total findings**: 15
- **HIGH severity**: 1 (local path leakage in README)
- **MEDIUM severity**: 2 (reading order conflict, TDD exemption gap)
- **LOW severity**: 8 (various minor inconsistencies)
- **INFO**: 2 (verified-good cross-references)
- **N/A (verified correct)**: 2

## Key Recommendations (Priority Order)

1. **Fix README.md local paths** (HIGH) -- Replace all 6 `/Users/gabrielsantiago/...` paths with relative paths.
2. **Standardize reading order** (MEDIUM) -- Pick one reading order and apply it to CLAUDE.md, docs/implementation-prompt.md, and .ai-utils/implementation-prompt.md.
3. **Eliminate duplicate implementation-prompt.md** (LOW) -- Delete .ai-utils/ copy or make it a symlink.
4. **Standardize URL parameter naming** (LOW) -- Change tech specs `{consultation_id}` to `{id}` to match all other docs.
5. **Mark DEC-007 note as resolved** (INFO) -- Section 13 title is already updated.
6. **Update stale task manager blockers** (LOW) -- Active blockers section references Task 009 which is done.
7. **Add patients.yaml to contract directory listing** (LOW) -- Missing from 03-contract-inventory.md section 1.
