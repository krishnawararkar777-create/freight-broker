# Algolyra — architecture.md

**Purpose of this file:** this is the HOW. `implementation_plan.md` is the product/business/feature spec. `rules.md` is what to do and avoid while writing code. `phases.md` is what to build, in what order. This file is the concrete system design — stack, folder layout, data flow, and the patterns every part of the codebase should follow. Read this before writing infrastructure, backend, or frontend code.

---

## 1. Tech stack (decided, not open for silent substitution)

| Layer | Choice | Why |
| :--- | :--- | :--- |
| **Backend language/framework** | Python + FastAPI | Matches the document-processing/AI ecosystem (Docling, PaddleOCR, Pydantic); see `implementation_plan.md` Section 16 |
| **Validation / typed AI I/O** | Pydantic | Every AI call's output is validated against a schema before it touches the database — this is how the grounding rule (`implementation_plan.md` Section 4) gets enforced in code |
| **ORM / migrations** | SQLAlchemy + Alembic | Every schema change is a migration, never a manual edit (`implementation_plan.md` Section 29) |
| **Database** | PostgreSQL 16 + `pgvector` extension | Relational core + optional similarity search later, no separate vector DB needed early |
| **Object storage** | MinIO (S3-compatible) locally, swappable for real S3/equivalent in production | Signed URLs, no public document access, ever |
| **Frontend** | Vite + React + TypeScript + TailwindCSS | Fast local dev, clean separation from the API (matches the architecture diagram below) |
| **Local dev orchestration** | Docker Compose (`postgres`, `minio`, `api`, `web`) | One command reproducible environment |
| **AI provider layer** | Abstracted `DocumentParser` interface — local/rule-based parser first, LLM-vision provider swappable behind the same interface | Never hardwire the product to one extraction method (`implementation_plan.md` Section 21) |

If a future decision needs to deviate from this table, it gets written back into this file — this table is the source of truth, not a one-time note in chat.

---

## 2. System architecture (high level)

```
Web App (React, split-screen review workspace)
↓ HTTPS
API (FastAPI — auth/routing/authorization)
↓
Claim Service (owns claim state machine, orchestrates everything below)
↓
Document Processing Pipeline
├── Object Storage (MinIO/S3, signed URLs only)
├── DocumentParser (abstracted: local parser now, LLM-vision provider later)
├── Document Classification
└── Structured Extraction (Pydantic-validated, per-field confidence + provenance)
↓
Claim Intelligence Layer
├── Claim Classification
├── Rules Engine (sourced CarrierRuleSet, deterministic)
├── Evidence/Completeness Checker (+ contradiction detection)
├── Deadline Engine (deterministic calendar-month arithmetic — never 270-day fixed constants or LLM math)
└── Readiness Engine (score + decision explanation)
↓
Human Review (split-screen workspace) → Approval (server-side enforced)
↓
Claim Submission (hard blockers enforced here)
↓
Claim Tracking → Recovery → Billing (Phase 2+)
```

Every arrow is a real service boundary in code, not just a diagram convention — the Claim Service never calls a parser directly, it always goes through the Document Processing Pipeline module. This is what keeps the provider abstraction (Section 7 below) real instead of aspirational.

---

## 3. Monorepo / folder structure

```
algolyra/
├── apps/
│   ├── web/                              # Vite + React + TS
│   │   ├── src/
│   │   │   ├── pages/                    # ClaimReview, ClaimList (Phase 1+), etc.
│   │   │   ├── components/
│   │   │   │   ├── document-viewer/      # PDF/image canvas, bbox overlay, zoom/pagination
│   │   │   │   ├── provenance-panel/     # fact list, click-to-highlight sync
│   │   │   │   └── review-controls/      # approve/edit/reject actions
│   │   │   ├── lib/                      # API client, shared fetch/query hooks
│   │   │   └── types/                    # generated/shared types from packages/shared
│   │   └── vite.config.ts
│   │
│   └── api/                              # FastAPI
│       ├── main.py
│       ├── routers/                      # thin — no business logic here (see rules.md)
│       │   ├── claims.py
│       │   ├── documents.py
│       │   └── organizations.py
│       ├── services/                     # business logic lives here
│       │   ├── claim_service.py
│       │   ├── document_service.py
│       │   ├── extraction_service.py
│       │   ├── rules_engine.py
│       │   ├── deadline_engine.py
│       │   └── readiness_engine.py
│       ├── parsers/                      # DocumentParser implementations
│       │   ├── base.py                   # abstract interface
│       │   ├── local_parser.py           # Phase 0 default
│       │   └── llm_vision_parser.py      # swappable second implementation
│       ├── models/                       # SQLAlchemy models
│       ├── schemas/                      # Pydantic schemas (request/response + AI I/O)
│       ├── db/
│       │   ├── session.py
│       │   └── migrations/               # Alembic
│       ├── scripts/
│       │   └── seed_demo_data.py
│       └── tests/
│
├── packages/
│   └── shared/                           # types/constants shared between web and api docs
│
├── docker-compose.yml                    # postgres16+pgvector, minio, api, web
├── .env.example
├── architecture.md                       # this file
├── rules.md
├── phases.md
└── implementation_plan.md
```

---

## 4. Request lifecycle walkthroughs

### 4.1 Document upload → extraction → claim facts
1. **Browser:** user drags a POD onto the upload zone in the review workspace.
2. `POST /api/claims/{claim_id}/documents/upload` (multipart) → `routers/documents.py`
3. Router calls `document_service.ingest_document()`:
   - a. Stream file to MinIO, compute `sha256` while streaming.
   - b. Check `sha256` against existing documents for this claim → `409 Conflict` if duplicate (see `rules.md`, error handling).
   - c. Insert `documents` row, `processing_state = "uploaded"`.
4. Async job enqueued → `extraction_service.extract()`:
   - a. Load file from MinIO.
   - b. Call `DocumentParser.parse()` (`local_parser.py` for Phase 0).
   - c. Validate output against the Pydantic extraction schema.
   - d. Write `document_evidence` rows (page, bbox, source text, field, confidence).
   - e. Write/update `claim_facts` rows (field_name, value, source_document_id, confidence, verification_status).
   - f. Set `documents.processing_state = "processed"` (or `"needs_review"` if any field is below the confidence threshold — see `phases.md` 0.4).
5. Frontend polls or receives a websocket/event → refreshes the provenance panel.

### 4.2 Claim review → approval → submission
1. **Browser** loads `GET /api/claims/{claim_id}` → returns claim, `claim_facts`, `document_evidence`, `requirements`, readiness score + explanation.
2. Split-screen workspace renders: document viewer (left), facts (center), readiness/approval controls (right).
3. Reviewer clicks a fact → frontend scrolls/highlights the matching bbox overlay on the document (and vice versa) — pure frontend state, no extra API call needed since evidence location is already in the payload.
4. Reviewer edits a fact if needed → `PATCH /api/claims/{claim_id}/facts/{id}` → `claim_service` records original value, new value, `actor=human`, reason.
5. Reviewer clicks Approve → `POST /api/claims/{claim_id}/approve` → `claim_service.approve()` checks the state machine (`rules.md`) → transitions `under_review` → `approved`. This is the ONLY code path that can move a claim toward submission.
6. `POST /api/claims/{claim_id}/submit` → `claim_service.submit()` checks `claim.status == "approved"` server-side before allowing the transition to `"submitted"`. This check exists even in Phase 0 with one hardcoded user — it's a habit you want baked in before multi-user matters.

---

## 5. Database architecture

● One PostgreSQL 16 instance (Docker Compose locally), `pgvector` extension enabled from the first migration even though nothing uses it yet in Phase 0.
● All schema changes go through Alembic — `alembic revision --autogenerate` then a human reviews the generated migration before running it. Never edit the schema by hand, even locally.
● Connection handling: a single SQLAlchemy session per request via FastAPI dependency injection (`db: Session = Depends(get_db)`) — services receive the session, they don't create their own.
● `organization_id` exists on every tenant-scoped table from the first migration, even though Phase 0 has exactly one hardcoded organization. Retrofitting this later is expensive; including it now is free (`implementation_plan.md` Section 10).

---

## 6. Storage architecture

● MinIO locally, real S3-compatible storage in production — same client code, different endpoint config, so this swap costs nothing later.
● Object key convention: `{organization_id}/{claim_id}/{document_id}/{original_filename}`.
● No public buckets, ever. All frontend file access goes through short-lived signed URLs generated per request, never a stored permanent URL.

---

## 7. AI provider abstraction & Precision Rules

```python
# apps/api/parsers/base.py
class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes, document_type: str) -> ExtractionResult:
        """Returns a Pydantic-validated ExtractionResult with per-field
        confidence and provenance. Must never return a field value without
        also returning where it came from."""
```

`local_parser.py` is the Phase 0 default (works with zero API keys, reliable on text-layer PDFs). `llm_vision_parser.py` is a second implementation of the same interface, swapped in via config once an API key is available.

**Precision Engineering Mandates:**
1. **Calendar-Month Arithmetic:** Deadline calculations use `dateutil.relativedelta(months=9)` for Carmack statutory limits, never fixed day-count approximations like 270 days.
2. **NMFC Item 300105 Citation Precision:** NMFC Item 300105 is cited accurately as governing minimum filing requirements (valid written claim filing with required factual elements), not a narrative draft template.
3. **Carrier Rule Sourcing:** Unverified secondary carriers (`Swift Line Logistics`, `Midwest Freight Co.`) are explicitly flagged with `source_reference = "DEMO DATA — UNVERIFIED"`.
4. **Seed Claim Scope Discipline:** Claims 2 (`Shortage`) and 4 (`Lost Cargo`) in `seed_demo_data.py` are static display-only rows for UI testing. Live processing is strictly scope-gated to Cargo Damage claims.

---

## 8. Local development environment

`docker-compose.yml` services: `postgres` (16, `pgvector` enabled), `minio`, `api` (FastAPI, hot reload), `web` (Vite dev server). `.env.example` documents every required variable (DB connection string, MinIO credentials, LLM API key placeholder, confidence thresholds per task).

`python -m scripts.seed_demo_data` populates the demo organization (Apex Freight Brokers), user (Sarah Jenkins), and one sample shipment/claim (PRO-847293) on demand.

---

## 9. Deployment path (for later — not needed in Phase 0)

Local → Staging → Production, each with its own environment variables and secrets, database migrations run as an explicit deploy step (never automatic-on-boot in production), backups scheduled on the production database. Do not build this until Phase 2 needs a real pilot-facing environment — see `phases.md`.

---

## 10. Phase 3 Integration & Workflow Architecture

### 10.1 TMS Adapter Architecture (`apps/api/app/integrations/tms/`)
* **Abstract Contract (`base.py`):** Unified `TMSAdapter` base class defining normalized Pydantic schemas (`NormalizedShipmentData`, `NormalizedDocumentRef`).
* **Provider Implementations (`mcleod_mock_adapter.py`):** McLeod LoadMaster adapter implementing HMAC signature verification, status exception classification (`DELIVERED_DAMAGED`, `SHORTAGE_REPORTED`), and document attachment extraction.
* **Universal Router & Service (`routers/tms.py`, `tms_service.py`):** Endpoint `POST /api/integrations/tms/{provider}/webhook` handling webhook verification, shipment/carrier record upserts, auto-fetching documents to S3 bucket `claim-documents`, triggering PaddleOCR fact extraction, and auto-creating claims in **`DRAFT` status ONLY** (`is_approved_by_human = False`).

### 10.2 EDI / X12 Parsing Architecture (`apps/api/app/parsers/edi/`)
* **Structural Segment Tokenizer (`x12_segment_parser.py`):** Pure-Python X12 tokenizer with segment delimiter autodetection (`~`, `\n`, `*`), tag lookups, and sub-element accessors.
* **Specialized Transaction Set Parsers:**
  - **EDI 214 (`edi_214_parser.py`):** Status exception codes (`AG` damaged, `SD` shortage, `CD` exception, `A7` refused). Locks `delivery_at` and computes Carmack 9-month statutory deadline (`dateutil.relativedelta(months=9)`) and Concealed Damage 5-day limit (`timedelta(days=5)`).
  - **EDI 210 (`edi_210_parser.py`):** Linehaul, fuel, weight, piece count, and damage ratio valuation math `claimed_amount = round(invoice_total * (damaged_qty / total_pieces), 2)`.
  - **EDI 204 / 211 (`edi_204_211_parser.py`):** Load tenders and e-BOL reference ingestion into `shipments`.
* **Unified Pipeline (`edi_service.py`):** Auto-detects `ST` headers (214, 210, 204, 211), updates shipment records, and auto-creates `DRAFT` claims on damage exception events.

### 10.3 Stateful Workflow Orchestration (`apps/api/app/workflows/`)
* **LangGraph State Graph (`claim_workflow_graph.py`):** Stateful graph modeling the complete claim lifecycle (`DRAFT` → `EVIDENCE_COLLECTION` → `UNDER_REVIEW` → `APPROVED` → `SUBMITTED` → `ACKNOWLEDGED` → `SETTLED / REBUTTAL_PENDING` → `LAWSUIT_CLOCK`).
* **Server-Side Approval Guard:** `validate_claim_submission_guard` strictly enforces `is_approved_by_human == True` and readiness score $\ge 80.0\%$ before allowing `SUBMITTED` transitions.
* **Supabase Postgres Checkpointer (`postgres_checkpointer.py`):** Checkpointer persisting graph state into `audit_events` table so claims resume seamlessly across worker restarts and multi-month carrier delays.
* **Event Triggers (`workflow_triggers.py`):** Evaluates Day 30 SLA receipt acknowledgment overdue (49 CFR § 370.9), Day 90 Carmack filing countdown warning, and Day 120 resolution escalation.

