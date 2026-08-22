# Sub-Phase 4.1: Production Telemetry & Quality Tracking Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a native, production-grade telemetry and extraction quality tracking engine measuring API latency percentiles (P50, P95, P99), schema validation failures, multi-parser extraction accuracy rates (tracking `LocalPdfParser`, `PaddlePdfParser`, and `LlmVisionParser`), and human edit diff telemetry from audit events.

**Architecture:** Custom FastAPI middleware asynchronously buffers and records request/response metrics into PostgreSQL (`api_telemetry_logs`). A dedicated `TelemetryService` computes latency percentiles, extraction quality scores, and human intervention rates off `api_telemetry_logs`, `document_evidence`, `claim_facts`, and `audit_events`. Thin FastAPI endpoints expose structured metrics without external observability dependencies.

**Tech Stack:** Python 3.14 + FastAPI + SQLAlchemy ORM + Pydantic v2 + PostgreSQL + Pytest.

**Spec:** `startup_target_overview.md` (Observability Engine) & `phases.md` (Sub-phase 4.1).

## Global Constraints

- **Native telemetry only:** No external SaaS dependencies (no Langfuse, Grafana, Datadog).
- **Three-parser support:** Explicitly track and compare `LocalPdfParser`, `PaddlePdfParser`, and `LlmVisionParser`.
- **OpenTelemetry naming conventions:** Use semantic attribute names (`latency_ms`, `http_method`, `status_code`, `endpoint_path`, `organization_id`).
- **Non-blocking middleware:** Middleware metrics insertion must never fail or block the primary HTTP response.
- **Tenant isolation:** All queries and metrics computations support optional or explicit `organization_id` filtering.

---

### Task 1: Telemetry Data Model & Database Verification

**Files:**
- Modify: `apps/api/app/models/telemetry_model.py`
- Modify: `apps/api/app/models/__init__.py`
- Test: `apps/api/tests/test_telemetry_model.py`

**Interfaces:**
- Produces: `APITelemetryLog` SQLAlchemy model with fields `id`, `organization_id`, `endpoint_path`, `http_method`, `status_code`, `latency_ms`, `request_bytes`, `response_bytes`, `created_at`.

- [ ] **Step 1: Write model verification tests**
Write tests in `apps/api/tests/test_telemetry_model.py` verifying model instantiation, column types, default values, and `to_dict()` serialization.

- [ ] **Step 2: Run test to verify initial state**
Run: `pytest apps/api/tests/test_telemetry_model.py -v`

- [ ] **Step 3: Refine `APITelemetryLog` model**
Ensure `telemetry_model.py` exports `APITelemetryLog` with proper indexed columns and UTC timestamps.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/api/tests/test_telemetry_model.py -v`

- [ ] **Step 5: Commit**
`git add apps/api/app/models/telemetry_model.py apps/api/tests/test_telemetry_model.py && git commit -m "feat(4.1): verify telemetry data model and schema"`

---

### Task 2: FastAPI Telemetry Middleware

**Files:**
- Create: `apps/api/app/middleware/telemetry_middleware.py`
- Modify: `apps/api/main.py`
- Test: `apps/api/tests/test_telemetry_middleware.py`

**Interfaces:**
- Consumes: FastAPI `Request`, `call_next`, `get_db` session generator.
- Produces: `TelemetryMiddleware` class recording route latency, status code, request/response byte size, and `organization_id` extracted from headers (`X-Organization-Id`) or auth context.

- [ ] **Step 1: Write middleware tests**
Write tests in `apps/api/tests/test_telemetry_middleware.py` simulating requests to `/api/health` and verify `APITelemetryLog` entries are recorded with accurate latency and status codes.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest apps/api/tests/test_telemetry_middleware.py -v`

- [ ] **Step 3: Implement `TelemetryMiddleware`**
Create `telemetry_middleware.py` with safe error-handling around DB logging (using background logging or isolated session).

- [ ] **Step 4: Register middleware in `main.py`**
Add `app.add_middleware(TelemetryMiddleware)` in `apps/api/main.py`.

- [ ] **Step 5: Run tests to verify they pass**
Run: `pytest apps/api/tests/test_telemetry_middleware.py -v`

- [ ] **Step 6: Commit**
`git add apps/api/app/middleware/telemetry_middleware.py apps/api/main.py apps/api/tests/test_telemetry_middleware.py && git commit -m "feat(4.1): implement native FastAPI telemetry middleware"`

---

### Task 3: Telemetry Calculation Service

**Files:**
- Create: `apps/api/app/services/telemetry_service.py`
- Test: `apps/api/tests/test_telemetry_service.py`

**Interfaces:**
- Produces:
  - `TelemetryService.get_api_metrics(db, org_id=None, time_window_hours=24) -> Dict` (Total requests, Error rate %, Avg latency, P50, P95, P99, heavy endpoint latencies).
  - `TelemetryService.get_extraction_accuracy(db, org_id=None) -> Dict` (Accuracy by document type: BOL, POD, Invoice, Carrier Response; Accuracy by parser: LocalPdfParser, PaddlePdfParser, LlmVisionParser; schema failure rate).
  - `TelemetryService.get_human_edit_diffs(db, org_id=None) -> Dict` (Total edits, human intervention rate %, field edit frequencies, mean absolute numeric corrections, avg review duration).

- [ ] **Step 1: Write failing service calculation tests**
Write tests in `apps/api/tests/test_telemetry_service.py` with known synthetic telemetry records, audit events, and document extractions to test exact percentile math and accuracy formula.

- [ ] **Step 2: Run test to verify failure**
Run: `pytest apps/api/tests/test_telemetry_service.py -v`

- [ ] **Step 3: Implement `TelemetryService`**
Write `telemetry_service.py` with deterministic percentile sorting (`numpy`/pure Python percentile math), document classification accuracy metrics, and `audit_events` aggregation.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/api/tests/test_telemetry_service.py -v`

- [ ] **Step 5: Commit**
`git add apps/api/app/services/telemetry_service.py apps/api/tests/test_telemetry_service.py && git commit -m "feat(4.1): implement TelemetryService with percentile and accuracy math"`

---

### Task 4: Backend Telemetry Router

**Files:**
- Create: `apps/api/routers/telemetry.py`
- Modify: `apps/api/main.py`
- Test: `apps/api/tests/test_telemetry_router.py`

**Interfaces:**
- Produces Endpoints:
  - `GET /api/telemetry/metrics` -> API latency, status distribution, P50/P95/P99.
  - `GET /api/telemetry/accuracy` -> Document type & parser extraction accuracy.
  - `GET /api/telemetry/human-diffs` -> Field edit counts, diff distributions, intervention rate.

- [ ] **Step 1: Write router API tests**
Write tests in `apps/api/tests/test_telemetry_router.py` calling the telemetry endpoints via `TestClient`.

- [ ] **Step 2: Run test to verify failure**
Run: `pytest apps/api/tests/test_telemetry_router.py -v`

- [ ] **Step 3: Implement `routers/telemetry.py`**
Create thin router calling `TelemetryService`.

- [ ] **Step 4: Register router in `main.py`**
Include `telemetry_router` in `apps/api/main.py`.

- [ ] **Step 5: Run tests to verify they pass**
Run: `pytest apps/api/tests/test_telemetry_router.py -v`

- [ ] **Step 6: Commit**
`git add apps/api/routers/telemetry.py apps/api/main.py apps/api/tests/test_telemetry_router.py && git commit -m "feat(4.1): register telemetry router and endpoints"`

---

### Task 5: End-to-End Verification & Benchmark Audit

**Files:**
- Modify: `apps/api/tests/test_telemetry_service.py`
- Test: `apps/api/tests/` (full test suite)

- [ ] **Step 1: Run full pytest suite across all 116+ tests**
Run: `pytest apps/api/tests`
Verify 100% clean passing with 0 warnings or failures.

- [ ] **Step 2: Commit & Update SDD Progress Ledger**
Update `.superpowers/sdd/2026-08-22-subphase-4-1-observability-engine/progress.md` with completed tasks.
