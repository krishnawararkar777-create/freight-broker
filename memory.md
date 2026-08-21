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
4. **Deterministic Arithmetic:** Deadlines, fees, and valuations are calculated in plain Python using calendar-month arithmetic (`dateutil.relativedelta(months=9)` and `relativedelta(years=2, days=1)`), NEVER LLM math or fixed day approximations.
5. **NMFC Item 300105 Citation Precision:** Cited as governing minimum filing requirements (valid written claim filing elements), not a narrative draft template.
6. **Storage Security:** **NO local `/uploads` folder**. All binaries are stored in MinIO/S3 object storage and accessed via short-lived signed URLs.

---

## 3. Tech Stack & Architecture (`architecture.md`)

* **Monorepo Layout:**
  - `apps/web`: Vite 8 + React 19 + TypeScript + TailwindCSS v4 + `@tanstack/react-query` + `@supabase/supabase-js`.
  - `apps/api`: Python 3.11/3.14 + FastAPI + SQLAlchemy ORM + Alembic + Pydantic v2 + `psycopg2`.
  - `apps/api/vendor/PaddleOCR`: Official Baidu PaddleOCR (PP-OCRv4) deep learning engine repository.
  - `packages/shared`: Shared TypeScript and Pydantic domain models.
* **Database:** Cloud Supabase PostgreSQL 16 (`db.dvqtlefogprzgtvssuuv.supabase.co`) with Row Level Security (RLS) enabled across all 19 domain tables.
* **Object Storage:** S3-compatible bucket (`claim-documents` / `algolyra-documents`) accessed via `boto3` client.
* **AI Provider Layer:** Abstracted `DocumentParser` base class (`apps/api/parsers/base.py`):
  - `PaddlePdfParser` (`paddle_parser.py`): Primary advanced OCR engine powered by PaddleOCR PP-OCRv4 (supports PDF, PNG, JPG, JPEG).
  - `LocalPdfParser` (`local_parser.py`): Default text-layer PDF parser.
  - `LlmVisionParser` (`llm_vision_parser.py`): Swappable VLM parser for photos/scans when API key is configured.
* **Live Local Dev Servers:**
  - Web UI: `http://localhost:5173/`
  - Backend API: `http://127.0.0.1:8000/api/health`

---

## 4. Phase 0 — Scope & Engineering Completed (100% DONE & VERIFIED)

**Phase 0 Scope:** 1 Carrier (`ABC Trucking`), 1 Claim Type (`Cargo Damage`), 1 Document Workflow (`BOL` + `POD` + `Invoice` + `Photo`), 1 User (`Sarah Jenkins`, `org: Apex Freight Brokers`).

### Phase 0 Tasks Built:
- **0.1 Infrastructure:** Scaffolded FastAPI API & Vite React web app.
- **0.2 Core Domain Schema:** 19 SQLAlchemy models, Alembic migration `001_initial_schema.py`, seed script `scripts/seed_demo_data.py`.
- **0.3 Document Upload:** MinIO/S3 upload stream with SHA-256 deduplication (`409 Conflict`).
- **0.4 Extraction Worker:** `LocalPdfParser` & `PaddlePdfParser` extracting facts into `document_evidence` & `claim_facts`.
- **0.5 Split-Screen Review:** Document Canvas with bounding box overlays & inline fact editing with audit diffs.
- **0.6 Classification & Deadline:** Completeness matrix & 9-month Carmack filing countdown (`dateutil.relativedelta(months=9)`).
- **0.7 Valuation Engine:** Ratio math `claimed_amount = round(invoice_total * (damaged_qty / total_qty), 2)`.
- **0.8 Readiness Score:** Dynamic 0–100% score based on completeness + confidence matrix.
- **0.9 Citation Package Generator:** Demand letter with sentence-level citations (`[BOL p.1]`, `[POD p.1]`).
- **0.10 Approval Server Guard:** `POST /api/claims/{id}/submit` returns `HTTP 403 Forbidden` if unapproved.

---

## 5. Phase 1 — Demo-Ready Operational Platform Completed (100% DONE & VERIFIED)

### Phase 1 Tasks Built:
- **1.1 Claims Operational Dashboard:** Status tabs (`All Claims`, `Needs Review`, `Submitted`, `Recovered`, `Action Required`), real-time search, claim type dropdowns, and top KPI cards.
- **1.2 Visual Urgency Badges:** `DeadlineUrgencyBadge` displaying color-coded Carmack filing countdowns (`🔴 URGENT`, `🟡 WARNING`, `🟢 SAFE`, `❌ EXPIRED`).
- **1.3 Multi-Carrier Rule Engine:** Ruleset inspector (`CarrierRulesView.tsx`) supporting `ABC Trucking` (verified), `Swift Line Logistics`, and `Midwest Freight Co.`.
- **1.4 Evaluation Suite:** Benchmark suite (`tests/test_golden_eval_suite.py`) verifying 100% extraction accuracy.
- **1.5 Deep Learning OCR:** Integrated Baidu PaddleOCR (PP-OCRv4) layout detection and EXIF damage photo canvas viewer.

---

## 6. Phase 2 — Pilot-Ready Multi-Tenant Platform Completed (100% DONE & VERIFIED)

Phase 2 built the complete pilot-ready multi-tenant system across 5 fully verified sub-phases:

### Sub-phase 2.1 — Multi-Tenancy, Supabase DB & RBAC Enforcement
* **Supabase Connection:** Connected Cloud Supabase PostgreSQL (`db.dvqtlefogprzgtvssuuv.supabase.co`).
* **Row Level Security (RLS):** Migration `002_multi_tenancy_rls.py` enabling RLS across all 19 domain tables and S3 storage bucket. Tested with `supashield audit` (**100% RLS Enabled**).
* **RBAC Role Matrix:** Implemented 5 RBAC roles: `Admin`, `Claims Manager`, `Claims Operator`, `Senior Approver`, `Finance`.
* **Frontend Supabase Auth & Multi-Tenant Portal:**
  - Built `AuthContext.tsx` with `@supabase/supabase-js` subscription, local demo fallback persistence, and multi-tenant switcher.
  - Created glassmorphism `/login` portal with 1-click test login for **Org A (Apex Freight Brokers)** and **Org B (Swift Line Logistics)**.
  - Hard route protection blocks unauthenticated visitors and redirects to `/login`.
  - Added user email, Org badge, RBAC role badge, and visible **Logout** button to `Navbar.tsx`.
* **RBAC Approval Guard:** Restricted `Claims Operator` (Dave Miller) from approving high-value claims ($5,000+). Renders `🔒 Approval Restricted ($5,000+)`. Allowed for `Claims Manager`, `Senior Approver`, and `Admin`.

### Sub-phase 2.2 — Follow-Up Automation & Carrier SLA Engine
* **Statutory SLA Engine:** `apps/api/app/services/sla_service.py` tracking 30-day acknowledgment & 120-day resolution windows under **49 CFR § 370.9**.
* **Visual SLA Urgency Alerts:** Red urgency badges (`🔴 30-DAY ACKNOWLEDGMENT OVERDUE`) appear under `CARMACK DEADLINE` column when 30 days elapse without carrier acknowledgment.
* **Human-Approved Follow-Up Drafts:** `app/services/followup_service.py` generates follow-ups in `DRAFT` status behind a server-side lock. Requires explicit human sign-off before carrier dispatch.

### Sub-phase 2.3 — Carrier Response Intelligence & Settlement Extraction
* **Schema & Migration:** `carrier_responses` table created via Alembic migration `003_carrier_responses.py`.
* **Inbound Letter Parser:** `apps/api/parsers/carrier_response_parser.py` parses carrier correspondence PDFs/images into decision types (`ACCEPTANCE`, `DENIAL`, `PARTIAL_SETTLEMENT`), claimed amounts, offer amounts, and denial codes.
* **Settlement Discrepancy Calculator:** `app/services/carrier_response_service.py` computes offer vs. claimed amount deltas and disputed balances.

### Sub-phase 2.4 — Denial, Rebuttal & Carmack 2-Year Lawsuit Clock
* **Carmack Lawsuit Clock Engine:** `app/services/carmack_lawsuit_service.py` calculates exact 2-year + 1-day statutory lawsuit deadline (`49 U.S.C. § 14706(e)(1)`).
* **Database Column:** Alembic migration `004_add_lawsuit_deadline.py` added `lawsuit_deadline_at` as a physical column in Supabase `claims` table.
* **Hand-Calculation Verification:**
  - Denial Date: `August 17, 2026` + 2 Years + 1 Day = **`August 18, 2028`**.
  - Supabase DB (`lawsuit_deadline_at`): **`August 18, 2028`**.
  - Web UI Display: **`August 18, 2028`** (100% exact match across DB, UI, and hand math).
* **Leap-Year Edge Case:** `Feb 29, 2024` -> `March 1, 2026` verified with 0 off-by-one errors.
* **Grounded Rebuttal Generator:** `app/services/rebuttal_service.py` refutes carrier denial pretexts (concealed damage 5-day notice, salvage duty, packaging pretexts) with statutory citations (`49 U.S.C. § 14706`, `[BOL p.1]`, `[Photo p.1]`).

### Sub-phase 2.5 — Event-Based Recovery & Contingency Fee Ledger
* **Append-Only Financial Ledger:** `app/services/recovery_ledger_service.py` records carrier settlement payouts into immutable `recovery_events`.
* **Deterministic 20% Contingency Fee Engine:** `fee_events` calculates Marajet's 20% fee ($0 fee on $0 recovered).
* **Deep Empirical Audit (All 6 Steps Verified):**
  - **Step 1 & 2:** Hand math: `$6,000.00 x 20% = $1,200.00`.
  - **Step 3:** Supabase `fee_events` table stores `fee_amount: 1200.00` (Exact Match).
  - **Step 4:** `$0.00` recovery event creates a `$0.00` fee event row (not skipped, no error).
  - **Step 5:** `recovery_events` ledger rows are append-only/immutable.
  - **Step 6:** Auto-generates billing `invoices` row for `$1,200.00` with status `issued`.

---

## 7. Phase 3 — Integration & Scale Progress

### Sub-phase 3.1 — TMS Connectors & Automated Ingestion Engine (100% DONE & VERIFIED)
* **`TMSAdapter` Contract:** Created abstract base interface (`apps/api/app/integrations/tms/base.py`) with Pydantic v2 schemas (`NormalizedShipmentData`, `NormalizedDocumentRef`).
* **`McLeodMockAdapter`:** Implemented McLeod LoadMaster adapter (`mcleod_mock_adapter.py`) supporting HMAC SHA-256 signature verification, document attachment URL extraction, and status event parsing (`DELIVERED_DAMAGED`, `SHORTAGE_REPORTED`, `CLAIM_PENDING`).
* **`TMSService` & Ingestion Pipeline:** Created `tms_service.py` orchestrating shipment upserts, Carmack 9-calendar month deadline computation (`dateutil.relativedelta(months=9)`), document auto-fetching to Supabase S3 bucket `claim-documents`, and PaddleOCR fact extraction.
* **Server-Side Approval Guard Enforcement:** Webhook-triggered claims strictly enforce `status = "DRAFT"` and `is_approved_by_human = False` — never auto-submitted.
* **Universal Router:** Registered `POST /api/integrations/tms/{provider}/webhook` in `routers/tms.py` & `main.py`.

### Sub-phase 3.2 — EDI / X12 Parsing Engine (100% DONE & VERIFIED)
* **Structural X12 Segment Tokenizer (`x12_segment_parser.py`):** Built pure-Python X12 tokenizer with segment delimiter autodetection (`~`, `\n`, `*`), tag lookups, and sub-element parsing.
* **EDI 214 Carrier Status Parser (`edi_214_parser.py`):** Parses 214 status messages. Extracts status exception codes (`AG` damaged, `SD` shortage, `CD` exception, `A7` refused). Locks `delivery_at` and computes Carmack 9-month statutory deadline (`dateutil.relativedelta(months=9)`) and Concealed Damage 5-day limit (`timedelta(days=5)`).
* **EDI 210 Freight Details & Invoice Parser (`edi_210_parser.py`):** Parses linehaul, fuel, weight, and total piece counts. Implements damage ratio valuation math `claimed_amount = round(invoice_total * (damaged_qty / total_pieces), 2)`.
* **EDI 204 / 211 Load Tender Parser (`edi_204_211_parser.py`):** Extracts load reference numbers, e-BOL details, shipper/consignee entities, NMFC item codes, and declared valuations into `shipments`.
* **`EDIService` Pipeline (`edi_service.py`):** Unified EDI file processor supporting `ST` header auto-detection (214, 210, 204, 211), database shipment upserts, and automated `DRAFT` claim generation (`is_approved_by_human = False`) upon damage exceptions.

### Sub-phase 3.3 — Stateful Durable Workflow Orchestration Engine (100% DONE & VERIFIED)
* **LangGraph Claim Lifecycle State Graph (`claim_workflow_graph.py`):** Models the full claim lifecycle (`DRAFT` → `EVIDENCE_COLLECTION` → `UNDER_REVIEW` → `APPROVED` → `SUBMITTED` → `ACKNOWLEDGED` → `SETTLED / REBUTTAL_PENDING` → `LAWSUIT_CLOCK`).
* **Server-Side Approval Guard:** `validate_claim_submission_guard` strictly enforces `is_approved_by_human == True` and readiness score $\ge 80.0\%$ before allowing `SUBMITTED` transitions.
* **Supabase Postgres Checkpointer (`postgres_checkpointer.py`):** Checkpointer persisting graph state into `audit_events` table so claims resume seamlessly across worker restarts and multi-month carrier delays.
* **Workflow Event Triggers (`workflow_triggers.py`):** Evaluates Day 30 SLA receipt acknowledgment overdue (49 CFR § 370.9), Day 90 Carmack filing countdown warning, and Day 120 resolution escalation.

---

## 8. Master Test Suite Metrics (100% CLEAN PASSING)

* **Pytest Backend Test Suite (`apps/api/tests`)**: **115/115 PASSED (100% Clean)**
  - `test_carmack_engine.py` (3 tests)
  - `test_carrier_response_parser.py` (3 tests)
  - `test_cross_tenant_isolation.py` (3 tests)
  - `test_document_upload.py` (3 tests)
  - `test_durable_workflow.py` (6 tests)
  - `test_edi_214_parser.py` (10 tests)
  - `test_edi_210_parser.py` (8 tests)
  - `test_edi_service.py` (14 tests)
  - `test_extraction_service.py` (3 tests)
  - `test_golden_eval_suite.py` (1 test)
  - `test_health.py` (1 test)
  - `test_mcleod_mock_adapter.py` (9 tests)
  - `test_models.py` (1 test)
  - `test_package_generator.py` (1 test)
  - `test_paddle_parser.py` (2 tests)
  - `test_phase2_5_deep_audit.py` (4 tests)
  - `test_readiness_engine.py` (3 tests)
  - `test_rebuttal_engine.py` (4 tests)
  - `test_recovery_fee_ledger.py` (4 tests)
  - `test_seed_demo_data.py` (1 test)
  - `test_sla_engine.py` (3 tests)
  - `test_submission_guard.py` (2 tests)
  - `test_tms_adapter_base.py` (8 tests)
  - `test_tms_ingestion.py` (12 tests)
  - `test_valuation_engine.py` (2 tests)
  - `test_workflow_triggers.py` (4 tests)
* **Frontend Production Build (`npm run build`)**: **PASSED in 497ms (0 TypeScript Errors)**
* **Git Repository State:** `main` branch synced with all Phase 3 commits (`c08faad`).

---

## 9. Current Status & Next Steps

* **Phase 0 Status:** 100% COMPLETE & VERIFIED
* **Phase 1 Status:** 100% COMPLETE & VERIFIED
* **Phase 2 Status:** 100% COMPLETE & VERIFIED (Sub-phases 2.1, 2.2, 2.3, 2.4, 2.5)
* **Phase 3 Status:** 100% COMPLETE & VERIFIED (Sub-phases 3.1, 3.2, 3.3)
* **Ready For:** Phase 4 — Observability & Intelligence Engine / Phase 5 — Acceptance-Rate Optimization (90–95% Target).



