# Algolyra — phases.md (Detailed Master Build Roadmap)

**Purpose of this file:** The WHEN and in WHAT ORDER. This is the authoritative roadmap Antigravity follows task-by-task while building. Work strictly in order — do not start a later sub-phase before the current one's acceptance criteria are met. 

Phase 0 is specified in complete technical depth (including data models, API endpoints, deterministic engines, and UI components) because it is the active build target. Later phases are detailed in full sequence so the growth path to the 90–95% recovery platform is completely transparent.

---

# PHASE 0 — Walking Skeleton (Current Build Target)

**Scope Discipline:** One carrier (ABC Trucking), one claim type (Cargo Damage), one document workflow (BOL + POD + Commercial Invoice + Photos), one hardcoded user (`Sarah Jenkins, Claims Manager`, `org: Apex Freight Brokers`).

---

### 0.1 — Environment & Infrastructure Setup

● **Monorepo scaffolding:** Structure per `architecture.md` Section 3:
  - `apps/web`: Vite + React + TypeScript + TailwindCSS
  - `apps/api`: Python 3.11 + FastAPI + SQLAlchemy + Alembic + Pydantic
  - `packages/shared`: Shared TypeScript/Pydantic types
● **`docker-compose.yml`:**
  - `postgres`: PostgreSQL 16 with `pgvector` extension enabled out-of-the-box.
  - `minio`: S3-compatible local object storage (Bucket: `algolyra-documents`).
  - `api`: FastAPI application container with hot-reloading.
  - `web`: Vite development server container.
● **Alembic Migrations:** Initialized under `apps/api/db/migrations`. The initial migration (`001_initial_schema.py`) is created *after* 0.2's models are defined.
● **Environment Gating:** `.env.example` documents every variable (`DB_URI`, `MINIO_ENDPOINT`, `MINIO_BUCKET`, `ENV=local`).
  - **Critical Rule:** Auto-migration and auto-seeding on boot are gated strictly behind `if os.getenv("ENV") == "local": ...`. Staging/production environments will run migrations as an explicit deployment step.

**Acceptance Criteria:**
- [ ] `docker compose up` brings up all four services with zero errors.
- [ ] API and Web hot-reload cleanly on file change.
- [ ] A round-trip "hello world" endpoint succeeds from web → api → back.

---

### 0.2 — Core Data Models & Database Schema

Create SQLAlchemy models (`apps/api/app/models/`) and Alembic migration (`001_initial_schema.py`) matching `implementation_plan.md` Section 10:

1. `organizations`: `id`, `name`, `type` (`broker|3pl|shipper|other`), `status`, `timezone`, `currency`, `created_at`, `updated_at`
2. `users`: `id`, `organization_id`, `name`, `email`, `role`, `status`, `created_at`, `last_login_at`
3. `customer_policies`: `id`, `organization_id`, `high_value_threshold`, `approval_policy_version`, `contingency_rate`, `communication_policy`, `follow_up_policy`, `timezone`, `effective_at`
4. `carriers`: `id`, `canonical_name`, `aliases`, `mc_number`, `contact_channels`, `active`
5. `carrier_rule_sets`: `id`, `carrier_id`, `version`, `effective_from`, `effective_to`, `rule_status`, `source_reference`, `verified_at`, `verified_by`
6. `carrier_claim_rules`: `id`, `carrier_rule_set_id`, `claim_type`, `filing_window_type`, `filing_window_value`, `filing_window_unit`, `required_document_type`, `submission_channel`, `special_rule_json`
7. `shipments`: `id`, `organization_id`, `external_reference`, `bol_number`, `carrier_id`, `shipper_name`, `consignee_name`, `origin`, `destination`, `pickup_at`, `delivery_at`, `declared_value`, `currency`, `commodity`, `quantity`, `weight`, `created_at`
8. `claims`: `id`, `organization_id`, `shipment_id`, `claim_type`, `status`, `lifecycle_version`, `claimed_amount`, `currency`, `approved_claim_amount`, `deadline_at`, `concealed_deadline_at`, `human_threshold_triggered`, `elevated_approval_acknowledged`, `is_approved_by_human`, `approved_by_user_id`, `reimbursement_mode`, `owner_user_id`, `created_at`, `submitted_at`, `closed_at`
9. `documents`: `id`, `organization_id`, `claim_id`, `shipment_id`, `document_type`, `filename`, `mime_type`, `object_key`, `sha256`, `page_count`, `extraction_status`, `parser_version`, `uploaded_by`, `created_at`
10. `document_evidence`: `id`, `document_id`, `page_number`, `bbox_json`, `source_text`, `field_name`, `normalized_value_json`, `extraction_method`, `model_version`, `confidence`
11. `claim_facts`: `id`, `claim_id`, `field_name`, `value_json`, `source_document_id`, `source_location`, `confidence`, `verification_status`, `original_value_json`, `edited_by_user_id`, `edited_at`, `edit_reason`, `created_at`
12. `claim_requirements`: `id`, `claim_id`, `requirement_type`, `description`, `source_rule_id`, `status` (`met|missing|unknown|waived`), `evidence_document_id`
13. `claim_submissions`: `id`, `claim_id`, `submission_channel`, `submitted_at`, `external_reference`, `payload_hash`, `status`, `submitted_by`
14. `communications`: `id`, `claim_id`, `channel`, `direction`, `sender`, `recipient`, `subject`, `body`, `draft_status`, `approved_by`, `sent_at`, `source_document_id`
15. `tasks`: `id`, `claim_id`, `type`, `owner_user_id`, `due_at`, `status`, `priority`, `created_by`, `completed_at`
16. `recovery_events`: `id`, `claim_id`, `amount`, `currency`, `received_at`, `payment_reference`, `payer`, `evidence_document_id`, `status`, `created_by`
17. `fee_events`: `id`, `claim_id`, `recovery_event_id`, `eligible_amount`, `contingency_rate`, `fee_amount`, `currency`, `status`, `invoice_id`, `created_at`
18. `invoices`: `id`, `organization_id`, `invoice_number`, `status`, `issue_date`, `due_date`, `currency`, `subtotal`, `tax`, `total`
19. `audit_events`: `id`, `organization_id`, `actor_type`, `actor_id`, `entity_type`, `entity_id`, `action`, `before_json`, `after_json`, `reason`, `created_at`

**Seed Data Script (`scripts/seed_demo_data.py`):**
- Organization: `Apex Freight Brokers` (`contingency_rate = 0.20`, `high_value_threshold = 5000`).
- User: `Sarah Jenkins` (`usr-1`, role: `Claims Manager`).
- Primary Verified Carrier: `ABC Trucking` (`CarrierRuleSet v2026.1`: Carmack 9-month window, 5-day concealed damage window, `source_reference = "ABC Freight Tariff 100-A Item 450 (Verified)"`).
- Secondary Demo Carriers (Flagged per rules.md): `Swift Line Logistics` and `Midwest Freight Co.` marked explicitly with `source_reference = "DEMO DATA — UNVERIFIED"`.
- Primary Live Claim: `PRO-847293` (Cargo Damage, live processed).
- Secondary Static Display Rows: Shortage and Lost Cargo claims are seeded as static display-only rows for UI dashboard visual testing (NOT processed live through extraction/classification).

**Acceptance Criteria:**
- [ ] `alembic upgrade head` runs cleanly on a fresh PostgreSQL database.
- [ ] `python -m scripts.seed_demo_data` populates org, user, carrier, rule set, and shipment idempotently.
- [ ] Unverified secondary demo carriers are explicitly tagged `source_reference = "DEMO DATA — UNVERIFIED"`.

---

### 0.3 — Document Upload & Idempotency Pipeline

● Endpoint: `POST /api/claims/{claim_id}/documents/upload` (multipart/form-data accepts BOL, POD, Commercial Invoice, Damage Photo).
● **Streaming & Checksumming:** Stream file payload to MinIO bucket `algolyra-documents` while computing SHA-256 in memory.
● **Strict Storage Rule:** **NO local filesystem storage** (`apps/api/uploads/` is forbidden). All binaries are stored in MinIO and retrieved via short-lived signed URLs.
● **Idempotency Check:** If SHA-256 matches an existing document for the same claim, return `409 Conflict` (`{"error_code": "duplicate_document", "message": "Duplicate document fingerprint detected"}`).

**Acceptance Criteria:**
- [ ] Uploading the exact same file twice to a claim returns `409 Conflict` on the second attempt.
- [ ] Uploading 4 unique documents (BOL, POD, Invoice, Photo) succeeds and creates 4 records.
- [ ] File access URLs are short-lived signed S3 URLs, never public paths.

---

### 0.4 — Provider-Abstracted Extraction Schema & Worker

● **Provider Abstraction Interface (`apps/api/parsers/base.py`):**
  ```python
  class BaseDocumentParser(ABC):
      @abstractmethod
      async def parse(self, file_bytes: bytes, filename: str, document_type: str) -> ExtractionResult:
          pass
  ```
● `LocalPdfParser` (`local_parser.py`): Phase 0 default implementation. Extracts text layers, typed fields, page numbers, and bounding boxes with zero external API key requirements.
● `LlmVisionParser` (`llm_vision_parser.py`): Swappable multimodal LLM VLM implementation behind the same interface for scanned/handwritten docs and photos.
● **Pydantic Validation Boundary:** Every extraction result is validated into `document_evidence` and `claim_facts` tables.
● **Confidence Cutoff:** Below threshold → field `verification_status = "needs_review"`. Human-verified facts are locked against automated overwrites.

**Acceptance Criteria:**
- [ ] Uploading `Bill_of_Lading_847293.pdf` populates `claim_facts` rows for carrier, shipment reference, pickup date, and declared value with linked `document_evidence`.
- [ ] Unfound fields default to `null / UNKNOWN` with `verification_status = "needs_review"` — never a plausible guess.
- [ ] Swapping `LocalPdfParser` for `LlmVisionParser` in configuration requires zero changes to `extraction_service.py`.

---

### 0.5 — Split-Screen Human Review Workspace (Frontend UI)

● **Left Pane (Document Viewer):** Render PDF/Image canvas with page pagination, zoom controls (+/-), and interactive bounding-box overlays driven by `document_evidence`.
● **Center Pane (Structured Facts):** Display `claim_facts` table with source citations (`[BOL p.1]`), confidence badges, and inline human edit controls that log `original_value`, `final_value`, `actor=human`, and `edit_reason` to `audit_events`.
● **Right Pane (Readiness & Approvals):** Readiness score gauge, checklist explanations, Carmack deadline timer, and approval actions.
● **Bidirectional Sync:** Clicking a fact in the center pane scrolls and highlights its corresponding bounding box on the document (and vice versa).

**Acceptance Criteria:**
- [ ] Split-screen workspace renders all 3 panes cleanly for sample claim `CLM-847293`.
- [ ] Bidirectional click-to-highlight sync works instantaneously in local state without extra API round-trips.
- [ ] Inline fact editing records audit diffs and updates `verification_status = "edited_by_human"`.

---

### 0.6 — Classification, Completeness & Deterministic Deadline Engine

● **Claim Classification:** Classifies claim type as `DAMAGE` (Confidence: 96%) and writes to `claims.claim_type`.
● **Completeness Engine:** Matches uploaded evidence against `carrier_claim_rules.required_document_type` list, populating `claim_requirements` (`MET`, `MISSING`, `UNKNOWN`).
● **Contradiction Detection:** Compares PRO numbers, quantities, and monetary values across BOL, POD, and Invoice. Flag mismatches (`BOL PRO != POD PRO`) in `contradictions` list.
● **Deterministic Calendar Deadline Engine (Correction 1):**
  - **Calendar-Month Arithmetic:** Compute Carmack statutory filing date using exact calendar-month addition via `dateutil.relativedelta(months=9)` (e.g. `delivery_date + relativedelta(months=9)`), NOT a hardcoded 270-day constant.
  - Tariff rule math: `concealed_deadline = delivery_date + timedelta(days=5)` (concealed damage limit).
  - *Strict Rule:* Never calculate deadlines using LLM arithmetic or fixed 270-day approximations.

**Acceptance Criteria:**
- [ ] Claim `CLM-847293` auto-calculates Carmack filing deadline (`Sept 15, 2026` from `Dec 15, 2025` delivery) using exact calendar-month arithmetic (`relativedelta(months=9)`).
- [ ] Removing Commercial Invoice correctly flags requirement `MISSING` and sets status `NEEDS_INFORMATION`.
- [ ] Mismatched quantity test fixture (BOL 100 units vs POD 92 units) triggers a `HIGH` severity contradiction alert.

---

### 0.7 — Claim Amount & Valuation Engine

● **Deterministic Valuation Calculation:**
  ```python
  claimed_amount = round(invoice_total * (damaged_qty / total_qty), 2)
  ```
● **Deterministic Breakdown Formatting:** Formatted via Python string interpolation directly from calculation variables (never generated by LLM narrative):
  `"$20,000.00 total invoice × 40.0% damaged quantity (3 pallets) = $8,000.00"`

**Acceptance Criteria:**
- [ ] Demo claim (Invoice `$20,000`, 40% damage) calculates exactly `$8,000.00`.
- [ ] UI displays the exact mathematical breakdown string alongside the claimed amount.

---

### 0.8 — Dynamic Readiness Score & Decision Explanation

● **Dynamic Score Computation:** Score is computed dynamically from requirement completeness and per-field extraction confidence:
  $$\text{Score} = f(\text{evidence completeness}, \text{extraction confidence}, \text{verification status})$$
● **Decision Explanation Checklist:** Always paired with itemized `✓ / ✗` explanations (e.g., `✓ BOL verified`, `✓ Invoice matched`, `⚠️ POD damage notation extracted at 89% confidence`).

**Acceptance Criteria:**
- [ ] Demo claim with 4/4 documents and high confidence scores at or near 92% readiness score.
- [ ] Removing one document dynamically drops the score and itemizes the missing requirement.

---

### 0.9 — Citation-Grounded Package Generator (Correction 2)

● Generates NMFC Item 300105 compliant claim demand package using verified `claim_facts` only.
● **Wording & Purpose Precision (Correction 2):** The generated claim package is structured to **comply with NMFC Item 300105's minimum filing requirements** (valid written claim filing with required factual elements), not a narrative draft template.
● Every factual sentence carries explicit sentence-level citations (`[BOL p.1]`, `[POD p.1]`).
● *Strict Rule:* No sentence in the draft may state a fact that does not trace to a verified `claim_facts` record.

**Acceptance Criteria:**
- [ ] The generated claim package is explicitly formatted to meet NMFC Item 300105's minimum filing requirements.
- [ ] Every factual sentence includes a visible evidence citation (`[BOL p.1]`).

---

### 0.10 — Approval Workflow & Server-Side Submission Guard

● Implement state machine transitions: `DRAFT` → `UNDER_REVIEW` → `APPROVED` → `SUBMITTED`.
● **Server-Side Permission Guard:**
  - `POST /api/claims/{claim_id}/submit` checks `claim.status == "APPROVED"`.
  - If `claimed_amount >= $5,000`, requires explicit Phase 0 **elevated approval acknowledgment** by the user (`Sarah Jenkins`), logged as `ELEVATED_APPROVAL_ACKNOWLEDGED` in `audit_events`.
  - Returns `HTTP 403 Forbidden` if submission is attempted without prior human approval sign-off.

**Acceptance Criteria:**
- [ ] Calling `POST /api/claims/{id}/submit` on an unapproved claim returns `HTTP 403 Forbidden`.
- [ ] Claim transitions to `SUBMITTED` only after human approval and elevated threshold acknowledgment are recorded.
- [ ] Every transition is logged in `audit_events` with actor, timestamp, and before/after state snapshots.

---

## Phase 0 Exit Checklist ("Definition of Done for Phase 0")

- [ ] All acceptance criteria for Sections 0.1 through 0.10 pass.
- [ ] Sample Cargo Damage claim (`PRO-847293`, 4 documents) runs end-to-end through upload → parsing → fact extraction → readiness scoring → demand drafting → human approval → submission lock release.
- [ ] `docker compose up` + `python -m scripts.seed_demo_data` initializes a clean, working environment with zero manual database editing.

---

# PHASE 1 — Demo-Ready (Single Tenant / Multi-Claim)

**Goal:** Expand Phase 0 into a multi-claim operational application ready for live investor demos and real broker feedback calls.

● **Claims Operational Dashboard:** List view supporting status filters (`Open`, `Under Review`, `Submitted`, `Recovered`, `Closed`).
● **Visual Deadline Urgency Alerts:** Color-coded Carmack deadline countdowns driven by calendar-month arithmetic.
● **Expanded Carrier Rule Engine:** Support 3 carriers (`ABC Trucking` verified; `Swift Line Logistics` and `Midwest Freight Co.` tagged `DEMO DATA — UNVERIFIED`).
● **CI Automated Evaluation Suite:** Integrate DeepEval/Promptfoo golden dataset tests in CI to gate extraction accuracy and prompt changes.

**Exit Criterion:** 3–5 sample claims visible on dashboard, with live Cargo Damage claim running end-to-end through evidence-backed human approval.

---

# PHASE 2 — Pilot-Ready (Multi-Tenancy & Recovery Billing)

**Goal:** Allow real freight brokers to operate claims independently without founder manual overrides.

---

### Sub-Phase 2.1 — Multi-Tenancy, Supabase DB & RBAC Enforcement (Security-Critical)

● **Supabase PostgreSQL & RLS Integration:** Connect Supabase Cloud PostgreSQL with `organization_id` Row Level Security (RLS) policies on all 19 domain tables (direct scoping or parent-join scoping).
● **Supabase S3 Storage Bucket:** Migrate object storage to Supabase S3 `claim-documents` bucket using short-lived signed URLs.
● **5-Tier RBAC Permission Gating:** Implement `Admin`, `Claims Manager`, `Claims Operator`, `Senior Approver` (required for $\ge \$5,000$ claims), and `Finance` roles in JWT middleware.
● **Mandatory Skill Workflow:**
  - `brainstorming`: Work through isolation model for all 19 tables before code.
  - `writing-plans`: Enumerate 19-table RLS checklist.
  - `test-driven-development`: Write failing cross-tenant isolation tests (`Broker A cannot view Broker B's data`).
  - `requesting-code-review`: Mandatory security code review.
  - `subagent-driven-development`: Split infra/policies/RBAC; test on finished whole.
  - `verification-before-completion`: Execute active cross-org query verifying 0 rows returned.
  - `finishing-a-development-branch`: Close out sub-phase branch cleanly.

---

### Sub-Phase 2.2 — Follow-Up Automation & Carrier SLA Tracking

● **Statutory SLA Clock Engine:** Track 30-day receipt acknowledgment and 120-day resolution windows under 49 CFR § 370.9.
● **Overdue Alerts & Human-Approved Drafts:** Generate citation-grounded follow-up emails/letters requiring human sign-off before dispatch.
● **Mandatory Skill Workflow:**
  - `brainstorming`: Define calendar vs. business day SLA calculation rules.
  - `writing-plans`: Map follow-up draft state machine.
  - `test-driven-development`: TDD for 30-day and 120-day boundaries & timezone edge cases.
  - `systematic-debugging`: Debug off-by-one errors in date math if observed.
  - `requesting-code-review`: Code review human-in-the-loop sign-off gating.

---

### Sub-Phase 2.3 — Carrier Response Intelligence & Settlement Extraction

● **Inbound Response Document Intake:** Ingest carrier acceptance letters, denial notices, partial settlement offers, and inspection requests.
● **VLM/OCR Extraction:** Parse offer amount, claimed amount, reason codes, and settlement conditions into `carrier_responses`.
● **Mandatory Skill Workflow:**
  - `brainstorming`: Design `carrier_responses` schema and visual confidence indicators.
  - `writing-plans`: Extend `DocumentParser` base interface.
  - `test-driven-development`: Heavy TDD for offer vs. claimed amount extraction.
  - `requesting-code-review`: Mandatory code review for financial extraction logic.
  - `verification-before-completion`: Verify extraction against realistic carrier document fixtures.

---

### Sub-Phase 2.4 — Denial, Rebuttal & Legal Appeal Loop

● **Carmack Statutory Lawsuit Clock (`lawsuit_deadline_at`):** Calculate exact **2-year + 1-day** post-denial lawsuit expiration date from written disallowance.
● **Pre-Packaged Rebuttal Engine:** Generate legally grounded rebuttals for concealed damage 5-day traps, salvage retention duties, and packaging negligence.
● **Mandatory Skill Workflow:**
  - `brainstorming`: Map rebuttal arguments against carrier pretexts.
  - `writing-plans`: Plan rebuttal state machine and Carmack lawsuit clock.
  - `test-driven-development`: Strict TDD for `2 years + 1 day` date arithmetic.
  - `systematic-debugging`: Test leap-year and month-boundary edge cases.
  - `requesting-code-review`: Mandatory review.
  - `verification-before-completion`: Hand-calculate statutory lawsuit dates for fixtures and compare.

---

### Sub-Phase 2.5 — Event-Based Recovery & Contingency Fee Ledger

● **Immutable Financial Ledger (`recovery_events`):** Append-only ledger recording verified carrier recovery check/ACH payments.
● **Contingency Fee Math & Invoicing:** Auto-calculate Marajet's 20% contingency fee ($0 fee on $0 recovered) and issue linked `invoices`.
● **Mandatory Skill Workflow:**
  - `brainstorming`: Design append-only immutable financial ledger schema.
  - `writing-plans`: Map discrete recovery → fee calculation → invoicing pipeline.
  - `test-driven-development`: Highest rigor TDD for 20% contingency fee math ($0 fee on $0 recovered).
  - `requesting-code-review`: Mandatory review.
  - `verification-before-completion`: Manually compute fees for multiple fixtures and compare against invoice outputs.

---

**Exit Criterion:** At least one pilot broker processes claims independently, resulting in a recorded recovery and fee invoice.

---

# PHASE 3 — Integration & Scale

● **TMS Connectors & Ingestion:** Integrate broker TMS APIs (McLeod, CargoWise, MercuryGate) for automated shipment intake.
● **EDI/X12 Parsing:** Ingest ANSI ASC X12 (214 status, 210 invoice) freight data.
● **Durable Workflow Orchestration:** Introduce LangGraph / Pydantic AI durable execution checkpoints for long-running claims spanning 30–120 days.

---

# PHASE 4 — Observability & Intelligence Engine

● **Production Observability:** Detailed API latency, extraction error rate, schema validation failure, and human edit diff telemetry.
● **Rejection Reason Taxonomy Learning:** Classify carrier rejection reasons into structured categories to identify carrier denial tactics.

---

# PHASE 5 — Acceptance-Rate Optimization & Expansion Modules (90–95% Target)

**Goal:** Achieve 90%–95% carrier acceptance rates and unlock high-margin revenue streams (per `implementation_plan.md` Section 29).

● **5.1 Automated Salvage Valuation & Liquidation Module:** Estimate residual damaged cargo value via vision models; connect with liquidation buyers to deduct salvage value before submission.
● **5.2 Real-Time Carrier Insurance & Double-Brokering Verification ("Risk Shield"):** Query FMCSA SAFER (`safer.fmcsa.dot.gov`) and L&I (`li-public.fmcsa.dot.gov`) endpoints at intake to flag ghost/uninsured carriers.
● **5.3 Tiered Contingency & Legal Escalation Partnerships:** Partner with specialized freight law firms for formal demand letters and litigation on denied claims at a **30%–35% contingency rate**.
● **5.4 Proactive Statute & Tariff Guardian:** Ingest Master Service Agreements (MSAs) and multimodal waybills to extract custom contractual limitation clauses (60–180 days) that override statutory clocks.

---

# PHASE 6 — Shipper Product

● Shared core claims engine supporting a dedicated Shipper Workspace, shipper-specific roles, internal approvals, and supply chain claims analytics.

---

# PHASE 7 — Global Cargo Recovery Platform

● Network carrier intelligence, insurance subrogation workflows, partner API platform, and international multimodal recovery.
