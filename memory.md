# Marajet / Algolyra — Project Continuity Memory (`memory.md`)

**Purpose of this file:** This is the single authoritative memory and state file for the Marajet / Algolyra codebase. Any new conversation or AI session MUST read this file first to resume building seamlessly without guessing or re-asking questions.

---

## 1. Project Overview & Business Core

* **Product Name:** Marajet (also referenced as Algolyra in core specs).
* **Domain:** Operating layer for freight cargo claims recovery.
* **Primary Customer:** Uninsured and self-insured freight brokers and third-party logistics (3PL) providers.
* **Business Model:** 15–20% contingency fee on recovered dollars ($0 fee on $0 recovered).
* **Primary Objective:** Raise cargo claim acceptance rates from the industry baseline of **30%–50%** up to **90%–95%** by building an undeniable, evidence-grounded claim package.

---

## 2. Core Non-Negotiable Rules & Constraints (`rules.md`)

Every line of code and architectural decision MUST follow these non-negotiable rules:

1. **No Autonomous Negotiation:** AI drafts claims and follow-ups; a human sends them, always.
2. **No Autonomous Action Above Threshold:** Claims at or above the customer policy threshold ($5,000 default) require explicit human approval and acknowledgment before submission.
3. **No Legal Conclusions:** AI states factual indicators only ("packaging documentation missing"), never legal conclusions ("carrier is liable under Carmack").
4. **Strict Evidence Grounding:** Every claim fact must trace to a source document. If a fact isn't present, the value is `null / UNKNOWN`. Never guess.
5. **Server-Side Submission Guard:** The state transition to `SUBMITTED` can ONLY be triggered by a human-initiated request. Enforced in `services/claim_service.py` (returns `HTTP 403 Forbidden` if unapproved).
6. **Rich AI Telemetry:** Every AI call logs model, model version, prompt version, input references, output, confidence, and human edits to `audit_events`.
7. **Deterministic Arithmetic:** Deadlines, fees, and amounts are calculated in plain Python using calendar-month arithmetic (`dateutil.relativedelta(months=9)`), NEVER LLM math or fixed 270-day approximations.
8. **NMFC Item 300105 Citation Precision:** Cited as governing minimum filing requirements (valid written claim filing elements), not a narrative draft template.
9. **Storage Security:** **NO local `/uploads` folder**. All binaries are stored in MinIO (S3-compatible) and accessed via short-lived signed URLs.
10. **Phase 0 Scope Discipline:** Live extraction, classification, and completeness processing is **100% restricted to Cargo Damage claims**. Non-damage claims in seed data are static display-only UI rows.

---

## 3. Tech Stack & Architecture (`architecture.md`)

* **Repository Structure:**
  - `apps/web`: Vite + React 18 + TypeScript + TailwindCSS + `@tanstack/react-query` + `react-pdf`.
  - `apps/api`: Python 3.11 + FastAPI + SQLAlchemy ORM + Alembic + Pydantic v2.
  - `packages/shared`: Shared TypeScript and Pydantic domain models.
* **Database:** PostgreSQL 16 with `pgvector` extension enabled from initial migration (`001_initial_schema.py`).
* **Object Storage:** MinIO S3-compatible container (`algolyra-documents` bucket) accessed via `boto3` client.
* **Local Dev Orchestration:** `docker-compose.yml` (`postgres`, `minio`, `api`, `web`).
* **AI Provider Layer:** Abstracted `DocumentParser` base class (`apps/api/parsers/base.py`):
  - `LocalPdfParser` (`local_parser.py`): Default Phase 0 parser for text-layer PDFs (zero external API keys needed).
  - `LlmVisionParser` (`llm_vision_parser.py`): Swappable VLM parser for photos/scans when API key is configured.

---

## 4. Work Completed So Far

The repository setup and architectural phase is **100% complete and verified**:

1. ✅ **`implementation_plan.md`**: Created in full word-for-word unsummarized format based on v4 specification.
2. ✅ **`startup_target_overview.md`**: Created combining YC startup targets, business model framing, and 90–95% acceptance blueprint.
3. ✅ **`architecture.md`**: Saved with full monorepo layout, tech stack, data flows, storage architecture, and provider abstractions.
4. ✅ **`rules.md`**: Saved with coding standards, library allowlist, explicit failure states (`409 Conflict`, `invalid_extraction`), security, and TDD testing rules.
5. ✅ **`phases.md`**: Saved with master build roadmap spanning Phase 0 to Phase 7, featuring complete technical depth for Phase 0 tasks 0.1 through 0.10 and acceptance checklists.
6. ✅ **Applied 4 Precision Corrections**:
   - Calendar-month `relativedelta(months=9)` Carmack deadline arithmetic.
   - NMFC Item 300105 minimum filing requirements precision.
   - Secondary demo carriers flagged with `source_reference = "DEMO DATA — UNVERIFIED"`.
   - Seed claims for non-damage types marked as static display-only UI rows.

---

## 5. Phase 0 Scope & Engineering Task Checklist (`phases.md`)

**Phase 0 Scope Boundary:** 1 Carrier (`ABC Trucking`), 1 Claim Type (`Cargo Damage`), 1 Document Workflow (`BOL` + `POD` + `Invoice` + `Photo`), 1 User (`Sarah Jenkins`, `org: Apex Freight Brokers`).

### Checklist of Tasks to Build:

- [ ] **0.1 Environment & Infrastructure**
  - Scaffold `docker-compose.yml` (`postgres:16-alpine` + `pgvector`, `minio`, `api`, `web`).
  - Scaffold `apps/api` FastAPI app structure with `.env.example` (`ENV=local`).
  - Scaffold `apps/web` Vite React TS app.
- [ ] **0.2 Core Data Models & Database Schema**
  - Implement 19 SQLAlchemy models in `apps/api/app/models/`.
  - Create Alembic migration `001_initial_schema.py`.
  - Create `scripts/seed_demo_data.py` (idempotently seeds Org, User `Sarah Jenkins`, Carrier `ABC Trucking`, and Shipment `PRO-847293`, gated by `if os.getenv("ENV") == "local":`).
- [ ] **0.3 Document Upload & Idempotency Pipeline**
  - Endpoint `POST /api/claims/{claim_id}/documents/upload` streaming file to MinIO with SHA-256 computation.
  - Return `409 Conflict` on duplicate SHA-256 upload to the same claim.
- [ ] **0.4 Extraction Schema & Worker**
  - Abstract `DocumentParser` interface.
  - Implement `LocalPdfParser` for text-layer PDFs (extracts facts + bounding boxes + page numbers).
  - Pydantic validation into `document_evidence` and `claim_facts` tables.
- [ ] **0.5 Split-Screen Review Workspace**
  - Frontend PDF/Image viewer with canvas rendering and interactive bounding-box overlays.
  - Center pane fact table with inline edit controls logging audit diffs to `audit_events`.
  - Bidirectional click-to-highlight sync between facts and bounding boxes.
- [ ] **0.6 Classification, Completeness & Deadline Engine**
  - Completeness matrix checking BOL, POD, Invoice, Photos.
  - Deterministic Carmack filing deadline calculation using `dateutil.relativedelta(months=9)` and concealed damage 5-day window.
  - Contradiction check flagging quantity/PRO mismatches.
- [ ] **0.7 Valuation Engine**
  - Deterministic Python math: `claimed_amount = round(invoice_total * (damaged_qty / total_qty), 2)`.
  - Math breakdown string formatted via Python string interpolation.
- [ ] **0.8 Dynamic Readiness Score**
  - Computed dynamically as a weighted sum of completeness + per-field extraction confidence.
  - Accompanied by itemized `✓ / ✗` decision explanation checklist.
- [ ] **0.9 Citation-Grounded Package Generator**
  - Formats demand letter compliant with NMFC Item 300105 minimum filing requirements with sentence-level citations (`[BOL p.1]`, `[POD p.1]`).
- [ ] **0.10 Approval Workflow & Server Guard**
  - State machine transitions (`DRAFT` → `UNDER_REVIEW` → `APPROVED` → `SUBMITTED`).
  - `POST /api/claims/{id}/submit` returns `HTTP 403 Forbidden` if unapproved or if `$8,000 >= $5,000` without elevated approval acknowledgment.

---

## 6. How to Start Building in a New Chat

When opening a new conversation with AI:
1. **Instruct the AI:** *"Read `memory.md`, `architecture.md`, `rules.md`, and `phases.md` before writing code."*
2. **First Action for AI:** Begin with **Phase 0 Sub-phase 0.1 & 0.2**:
   - Create `docker-compose.yml` for PostgreSQL 16 + `pgvector` + MinIO.
   - Create `apps/api` FastAPI backend structure with 19 SQLAlchemy models and Alembic migration `001_initial_schema.py`.
   - Create `scripts/seed_demo_data.py` gated by `ENV=local`.
