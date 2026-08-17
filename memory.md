# Marajet / Algolyra — Project Continuity Memory (`memory.md`)

**Purpose of this file:** This is the single authoritative memory and state file for the Marajet / Algolyra codebase. Any new conversation or AI session MUST read this file first to resume building seamlessly without guessing or re-asking questions.

---

## 1. Project Overview & Business Core

* **Product Name:** Marajet (also referenced as Algolyra in core specs & monorepo `@algolyra`).
* **Domain:** Operating layer for freight cargo claims recovery.
* **Primary Customer:** Uninsured and self-insured freight brokers and third-party logistics (3PL) providers.
* **Business Model:** 20% contingency fee on recovered dollars ($0 fee on $0 recovered).
* **Primary Objective:** Raise cargo claim acceptance rates from the industry baseline of **30%–50%** up to **90%–95%** by building an undeniable, evidence-grounded claim package.
* **GitHub Repository:** [`https://github.com/krishnawararkar777-create/freight-broker.git`](https://github.com/krishnawararkar777-create/freight-broker.git) (`main` branch synced).

---

## 2. Core Non-Negotiable Rules & Constraints (`rules.md`)

Every line of code and architectural decision MUST follow these non-negotiable rules:

1. **No Autonomous Action Above Threshold:** Claims at or above the policy threshold ($5,000 default) require explicit human approval (`is_approved_by_human = True`) before submission.
2. **Strict Evidence Grounding:** Every claim fact must trace to a source document with page numbers and bounding box coordinates (`[BOL p.1]`, `[POD p.1]`). Never guess values.
3. **Server-Side Submission Guard:** State transition to `SUBMITTED` is guarded server-side in `services/submission_service.py` and `routers/claims.py` (returns `HTTP 403 Forbidden` if unapproved or blocked).
4. **Deterministic Arithmetic:** Deadlines, fees, and valuations are calculated in plain Python using calendar-month arithmetic (`dateutil.relativedelta(months=9)`), NEVER LLM math or fixed 270-day approximations.
5. **NMFC Item 300105 Citation Precision:** Cited as governing minimum filing requirements (valid written claim filing elements), not a narrative draft template.
6. **Storage Security:** **NO local `/uploads` folder**. All binaries are stored in MinIO/S3 object storage and accessed via short-lived signed URLs.

---

## 3. Tech Stack & Architecture (`architecture.md`)

* **Monorepo Layout:**
  - `apps/web`: Vite 8 + React 19 + TypeScript + TailwindCSS v4 + `@tanstack/react-query` + `react-pdf`.
  - `apps/api`: Python 3.11/3.14 + FastAPI + SQLAlchemy ORM + Alembic + Pydantic v2.
  - `apps/api/vendor/PaddleOCR`: Official Baidu PaddleOCR (PP-OCRv4) deep learning engine repository.
  - `packages/shared`: Shared TypeScript and Pydantic domain models.
* **Database:** PostgreSQL 16 ready & SQLite local dev engine (`algolyra_local.db`).
* **Object Storage:** MinIO S3-compatible bucket (`algolyra-documents`) via `boto3` client.
* **AI Provider Layer:** Abstracted `DocumentParser` base class (`apps/api/parsers/base.py`):
  - `PaddlePdfParser` (`paddle_parser.py`): Primary advanced OCR engine powered by PaddleOCR PP-OCRv4 (supports PDF, PNG, JPG, JPEG).
  - `LocalPdfParser` (`local_parser.py`): Default text-layer PDF parser.
  - `LlmVisionParser` (`llm_vision_parser.py`): Swappable VLM parser for photos/scans when API key is configured.
* **Live Local Dev Ports:**
  - Web UI: `http://localhost:5173/`
  - Backend API: `http://localhost:8000/api/health`

---

## 4. Initial Repository Setup Completed

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

## 5. Phase 0 Scope & Completed Engineering Tasks (`phases.md`)

**Phase 0 Scope Boundary:** 1 Carrier (`ABC Trucking`), 1 Claim Type (`Cargo Damage`), 1 Document Workflow (`BOL` + `POD` + `Invoice` + `Photo`), 1 User (`Sarah Jenkins`, `org: Apex Freight Brokers`).

### Completed Phase 0 Task Checklist (100% DONE & VERIFIED):

- [x] **0.1 Environment & Infrastructure**
  - Scaffolded `docker-compose.yml` (`postgres:16-alpine` + `pgvector`, `minio`, `api`, `web`).
  - Scaffolded `apps/api` FastAPI structure with `.env.example` (`ENV=local`).
  - Scaffolded `apps/web` Vite React TS app.
- [x] **0.2 Core Data Models & Database Schema**
  - Implemented 19 SQLAlchemy models in `apps/api/app/models/domain_models.py`.
  - Created Alembic migration `001_initial_schema.py`.
  - Created `scripts/seed_demo_data.py` (seeds Org `Apex Freight Brokers`, User `Sarah Jenkins`, Carrier `ABC Trucking`, Shipment `PRO-847293`).
- [x] **0.3 Document Upload & Idempotency Pipeline**
  - Endpoint `POST /api/claims/{claim_id}/documents/upload` streaming file to MinIO with SHA-256 computation.
  - Returns `409 Conflict` on duplicate SHA-256 upload to the same claim.
- [x] **0.4 Extraction Schema & Worker**
  - Abstracted `DocumentParser` base interface.
  - Implemented `LocalPdfParser` & `PaddlePdfParser` for text & image OCR extractions.
  - Pydantic validation into `document_evidence` and `claim_facts` tables.
- [x] **0.5 Split-Screen Review Workspace**
  - Frontend Document Canvas viewer with visual bounding-box evidence overlays.
  - Center pane fact table with inline edit controls logging audit diffs to `audit_events`.
  - Bidirectional click-to-highlight sync between facts and bounding boxes.
- [x] **0.6 Classification, Completeness & Deadline Engine**
  - Completeness matrix checking BOL, POD, Invoice, Photos.
  - Deterministic Carmack filing deadline calculation using `dateutil.relativedelta(months=9)` and concealed damage 5-day window.
- [x] **0.7 Valuation Engine**
  - Deterministic Python math: `claimed_amount = round(invoice_total * (damaged_qty / total_qty), 2)`.
  - Math breakdown string formatted via Python string interpolation.
- [x] **0.8 Dynamic Readiness Score**
  - Computed dynamically as a weighted sum of completeness + per-field extraction confidence.
  - Accompanied by itemized `✓ / ✗` decision explanation checklist.
- [x] **0.9 Citation-Grounded Package Generator**
  - Formats demand letter compliant with NMFC Item 300105 minimum filing requirements with sentence-level citations (`[BOL p.1]`, `[POD p.1]`).
- [x] **0.10 Approval Workflow & Server Guard**
  - State machine transitions (`DRAFT` → `UNDER_REVIEW` → `APPROVED` → `SUBMITTED`).
  - `POST /api/claims/{id}/submit` returns `HTTP 403 Forbidden` if unapproved.

---

## 6. Phase 1 — Demo-Ready Platform Completed (100% DONE & VERIFIED)

- [x] **1.1 Claims Operational Dashboard & Filters**
  - Multi-claim queue list view table.
  - Status tabs (`All Claims`, `Needs Review`, `Submitted`, `Recovered`, `Action Required`).
  - Real-time search bar matching PRO#, Claim#, Carrier Name, Shipper, Consignee.
  - Claim type dropdown filter (`All Types`, `Cargo Damage`, `Shortage`, `Concealed Damage`, `Overcharge`).
  - Top-level KPI metrics cards (Total Active Claimed, Total Recovered, Human Guard Queue, Net Recovery Rate).
- [x] **1.2 Visual Deadline Urgency Alerts**
  - Reusable `DeadlineUrgencyBadge` component displaying color-coded Carmack filing countdowns (`🔴 URGENT`, `🟡 WARNING`, `🟢 SAFE`, `❌ EXPIRED`).
- [x] **1.3 Expanded Carrier Rule Engine**
  - Multi-carrier ruleset inspector (`CarrierRulesView.tsx`) supporting 3 demo carriers (`ABC Trucking` verified; `Swift Line Logistics` and `Midwest Freight Co.` tagged `DEMO DATA — UNVERIFIED`).
- [x] **1.4 CI Automated Evaluation Suite**
  - Golden dataset benchmark suite (`apps/api/tests/test_golden_eval_suite.py`) verifying 100% extraction accuracy.

---

## 7. Advanced PaddleOCR & Image OCR Integration Completed (100% DONE & VERIFIED)

- [x] **PaddleOCR Repository Integration**: Official `PaddlePaddle/PaddleOCR` repository cloned into `apps/api/vendor/PaddleOCR`.
- [x] **`PaddlePdfParser` Engine**: Integrated PP-OCRv4 deep learning layout detection and bounding box coordinate mapping.
- [x] **Full Image Format Support (.png, .jpg, .jpeg)**: Uploading images creates `DAMAGE_PHOTO` documents with visual damage evidence cards, EXIF timestamp metadata, and damage photo preview canvas in `HumanReviewWorkspace.tsx`.
- [x] **GitHub Synchronization**: Repository synced to [`https://github.com/krishnawararkar777-create/freight-broker.git`](https://github.com/krishnawararkar777-create/freight-broker.git) on branch `main`.

---

## 8. Verification Results & Test Metrics

- **Pytest Backend Test Suite (`apps/api/tests`)**: **23/23 PASSED (100% Clean)**
  - `test_carmack_engine.py` (3 tests)
  - `test_document_upload.py` (3 tests)
  - `test_extraction_service.py` (3 tests)
  - `test_golden_eval_suite.py` (1 test)
  - `test_health.py` (1 test)
  - `test_models.py` (1 test)
  - `test_package_generator.py` (1 test)
  - `test_paddle_parser.py` (2 tests)
  - `test_readiness_engine.py` (3 tests)
  - `test_seed_demo_data.py` (1 test)
  - `test_submission_guard.py` (2 tests)
  - `test_valuation_engine.py` (2 tests)
- **Frontend Web Production Build (`npm run build:web`)**: **PASSED in 1.49s (0 Errors)**

---

## 9. Phase 2 Architecture & Sub-Phase Master Roadmap

Phase 2 builds the **Pilot-Ready Multi-Tenant Platform** across 5 sub-phases:
- **Sub-phase 2.1 — Multi-Tenancy, Supabase Connection & RBAC Enforcement** (Supabase DB, RLS policies across 19 tables, 5 RBAC roles, `claim-documents` S3 bucket).
- **Sub-phase 2.2 — Follow-Up Automation & Carrier SLA Tracking** (30-day/120-day SLA clocks under 49 CFR § 370.9, overdue alerts, human-approved follow-up drafts).
- **Sub-phase 2.3 — Carrier Response Intelligence & Settlement Extraction** (Inbound acceptance/denial/settlement parsing, `carrier_responses` schema, offer vs claimed amount extraction).
- **Sub-phase 2.4 — Denial, Rebuttal & Legal Appeal Loop** (Carmack 2-year + 1-day lawsuit clock `lawsuit_deadline_at`, pre-packaged rebuttals for concealed damage/salvage/packaging).
- **Sub-phase 2.5 — Event-Based Recovery & Contingency Fee Ledger** (Immutable append-only `recovery_events` ledger, automated 20% contingency fee math, `invoices` generation).

---

## 10. Phase 2 Mandatory Skill Mapping Rules (`.agents/rules/phase2_skill_mapping.md`)

Every sub-phase MUST follow this skill mapping workflow:

* **Sub-phase 2.1 (Multi-Tenancy & RBAC):**
  - `brainstorming`: Analyze direct vs. parent-inherited `organization_id` RLS isolation across 19 tables before code.
  - `writing-plans`: Enumerate all 19 tables and their isolation strategy checklist.
  - `test-driven-development`: Write failing cross-tenant isolation tests (`Broker A cannot read Broker B's data`) before policies exist.
  - `requesting-code-review`: Mandatory security review of RLS policies.
  - `subagent-driven-development`: Parallelize infra/policies/RBAC within 2.1; test against the complete whole.
  - `verification-before-completion`: Run `supashield audit`, `supashield test --as-user`, and `supashield test-storage` to verify 100% RLS policy and S3 storage bucket isolation across all 19 tables.
  - `finishing-a-development-branch`: Close out sub-phase branch cleanly.

* **Sub-phase 2.2 (Follow-Up & SLA Engine):**
  - `brainstorming`: Define exact calendar vs. business day SLA rules for 30-day/120-day windows.
  - `writing-plans`: Map follow-up draft state machine.
  - `test-driven-development`: Heavy TDD for 30-day and 120-day boundaries & timezone edge cases.
  - `systematic-debugging`: Debug SLA date math if off-by-one errors occur.
  - `requesting-code-review`: Review human sign-off gating logic.

* **Sub-phase 2.3 (Carrier Response & Settlement Extraction):**
  - `brainstorming`: Design `carrier_responses` schema and visual extraction confidence indicators.
  - `writing-plans`: Extend `DocumentParser` base interface.
  - `test-driven-development`: Heavy money-critical TDD for offer vs. claimed amount math.
  - `requesting-code-review`: Mandatory code review for dollar-handling code.
  - `verification-before-completion`: Verify extraction against realistic denial/settlement document fixtures.

* **Sub-phase 2.4 (Denial, Rebuttal & Carmack 2-Year Clock):**
  - `brainstorming`: Map rebuttal strategies for concealed damage, salvage duty, and packaging pretexts.
  - `writing-plans`: Plan rebuttal state machine and Carmack lawsuit clock.
  - `test-driven-development`: Strict TDD for the Carmack 2-year + 1-day post-denial lawsuit deadline (`lawsuit_deadline_at`).
  - `systematic-debugging`: Test leap-year and month-boundary edge cases.
  - `requesting-code-review`: Mandatory review.
  - `verification-before-completion`: Hand-calculate statutory lawsuit dates for test fixtures.

* **Sub-phase 2.5 (Recovery & Contingency Fee Ledger):**
  - `brainstorming`: Design append-only immutable financial ledger schema (`recovery_events`, `fee_events`).
  - `writing-plans`: Map discrete auditable steps for recovery → fee calculation → invoicing.
  - `test-driven-development`: Highest rigor TDD for 20% contingency fee ($0 fee on $0 recovered). Test $0 recovery explicitly.
  - `requesting-code-review`: Mandatory code review.
  - `verification-before-completion`: Manually compute fees for multiple fixtures and compare against invoice outputs.

* **Cross-Cutting Meta-Skills Rules:**
  - `using-superpowers`: Meta-skill active across all sub-phases.
  - `dispatching-parallel-agents`: Use within sub-phases only; NEVER across sub-phases.
  - `writing-skills`: Create skills if recurring patterns warrant codification.
  - `finishing-a-development-branch`: Close out branches at the end of each sub-phase.

