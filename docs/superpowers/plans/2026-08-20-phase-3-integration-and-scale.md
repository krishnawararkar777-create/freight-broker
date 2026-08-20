# Phase 3 — Integration & Scale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Phase 3 (Integration & Scale) to convert Marajet into an automated integration engine with TMS connectors (Sub-phase 3.1), EDI/X12 parsing (Sub-phase 3.2), and stateful durable workflow orchestration (Sub-phase 3.3).

**Architecture:** Abstracted `TMSAdapter` interface with Mock McLeod LoadMaster implementation, `pyx12` structural parser with custom Pydantic freight transaction mappers for EDI 214/210/204/211, and LangGraph state graph with Supabase Postgres checkpointer for durable multi-month claim lifecycle orchestration.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, Alembic, `pyx12`, LangGraph, Supabase Cloud PostgreSQL, MinIO/S3 object storage, Vite + React + TypeScript frontend.

**Spec:** [`phases.md`](file:///c:/Users/krish/Downloads/FREIGHT%20BROKER/phases.md)

## Global Constraints

- Do not modify or break Phase 0–2 business logic (RLS, RBAC, Carmack 9-month/2-year lawsuit clocks, 30/120-day SLA engines, 20% contingency fee ledger).
- Server-side human approval guard (`is_approved_by_human == True`) MUST be strictly enforced before any claim can transition to `SUBMITTED` state. Webhook-triggered claims are created in `DRAFT` state ONLY.
- Carmack statutory filing dates MUST use exact calendar-month addition via `dateutil.relativedelta(months=9)` — NEVER 270-day approximations or LLM math.
- All monetary calculations must use exact ratio math: `claimed_amount = round(invoice_total * (damaged_qty / total_qty), 2)`.

---

## Sub-Phase 3.1 — TMS Connectors & Automated Ingestion Engine

### Task 1: Core TMSAdapter Abstract Interface & Normalized Pydantic Schemas

**Files:**
- Create: `apps/api/app/integrations/tms/base.py`
- Test: `apps/api/tests/test_tms_adapter_base.py`

**Interfaces:**
- Consumes: Pydantic `BaseModel`
- Produces: `NormalizedShipmentData`, `NormalizedDocumentRef`, `TMSAdapter` abstract base class

- [ ] **Step 1: Write the failing test**

```python
import pytest
from apps/api/app/integrations/tms/base import NormalizedShipmentData, NormalizedDocumentRef

def test_normalized_shipment_data_schema():
    data = NormalizedShipmentData(
        external_reference="ORD-9921",
        bol_number="BOL-88219",
        pro_number="PRO-7712",
        carrier_canonical_name="ABC Trucking",
        shipper_name="Apex Logistics",
        consignee_name="National Retail",
        origin="Chicago, IL",
        destination="Dallas, TX",
        declared_value=15000.00,
        commodity="Electronics",
        quantity=50,
        weight=2400.0,
        raw_status="DELIVERED_DAMAGED"
    )
    assert data.bol_number == "BOL-88219"
    assert data.declared_value == 15000.00
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_tms_adapter_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'apps.api.app.integrations'"

- [ ] **Step 3: Write minimal implementation**

Create `apps/api/app/integrations/tms/base.py` with abstract methods (`verify_webhook_signature`, `parse_webhook_shipment`, `extract_document_references`, `is_claim_trigger_event`, `fetch_document_bytes`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_tms_adapter_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/integrations/tms/base.py apps/api/tests/test_tms_adapter_base.py
git commit -m "feat(tms): add base TMSAdapter interface and normalized schemas"
```

---

### Task 2: McLeod Mock Adapter Implementation (`McLeodMockAdapter`)

**Files:**
- Create: `apps/api/app/integrations/tms/mcleod_mock_adapter.py`
- Test: `apps/api/tests/test_mcleod_mock_adapter.py`

**Interfaces:**
- Consumes: `TMSAdapter` from `apps/api/app/integrations/tms/base.py`
- Produces: `McLeodMockAdapter` class capable of validating McLeod HMAC headers, parsing McLeod JSON payloads, extracting document attachments, and detecting `DELIVERED_DAMAGED` status events.

- [ ] **Step 1: Write the failing test**

```python
from apps/api/app/integrations/tms/mcleod_mock_adapter import McLeodMockAdapter

def test_mcleod_adapter_parses_damage_webhook():
    adapter = McLeodMockAdapter(webhook_secret="test-secret")
    payload = {
        "event_type": "SHIPMENT_STATUS_UPDATE",
        "order_number": "MCL-50491",
        "bol_number": "BOL-50491",
        "pro_number": "PRO-12345",
        "status": "DELIVERED_DAMAGED",
        "carrier_name": "ABC Trucking",
        "shipper": "Midwest Foods",
        "consignee": "Target Stores",
        "origin": "Omaha, NE",
        "destination": "Denver, CO",
        "declared_value": 8500.00,
        "commodity": "Frozen Goods",
        "quantity": 100,
        "weight": 5000.0,
        "documents": [
            {
                "type": "BOL",
                "filename": "bol_50491.pdf",
                "url": "https://mcleod-mock.internal/docs/bol_50491.pdf",
                "mime_type": "application/pdf"
            }
        ]
    }
    shipment = adapter.parse_webhook_shipment(payload)
    is_trigger, reason = adapter.is_claim_trigger_event(payload)
    docs = adapter.extract_document_references(payload)

    assert shipment.external_reference == "MCL-50491"
    assert is_trigger is True
    assert reason == "DELIVERED_DAMAGED"
    assert len(docs) == 1
    assert docs[0].filename == "bol_50491.pdf"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_mcleod_mock_adapter.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write minimal implementation**

Implement `McLeodMockAdapter` in `apps/api/app/integrations/tms/mcleod_mock_adapter.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_mcleod_mock_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/integrations/tms/mcleod_mock_adapter.py apps/api/tests/test_mcleod_mock_adapter.py
git commit -m "feat(tms): implement McLeodMockAdapter for McLeod LoadMaster JSON webhooks"
```

---

### Task 3: TMS Webhook Service & Router Endpoint

**Files:**
- Create: `apps/api/app/services/tms_service.py`
- Create: `apps/api/routers/tms.py`
- Modify: `apps/api/main.py:1-60`
- Test: `apps/api/tests/test_tms_ingestion.py`

**Interfaces:**
- Consumes: `TMSAdapter`, `document_service`, `extraction_service`
- Produces: `POST /api/integrations/tms/{provider}/webhook` endpoint

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_tms_webhook_endpoint():
    payload = {
        "event_type": "SHIPMENT_STATUS_UPDATE",
        "order_number": "MCL-99001",
        "bol_number": "BOL-99001",
        "status": "DELIVERED_DAMAGED",
        "carrier_name": "ABC Trucking",
        "shipper": "Sender Inc",
        "consignee": "Receiver Inc",
        "origin": "Chicago, IL",
        "destination": "Miami, FL",
        "declared_value": 12000.0,
        "commodity": "Auto Parts",
        "quantity": 20,
        "weight": 1500.0,
        "documents": []
    }
    response = client.post("/api/integrations/tms/mcleod/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["claim_created"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_tms_ingestion.py -v`
Expected: FAIL with 404 Not Found

- [ ] **Step 3: Write minimal implementation**

Implement `TMSService` in `apps/api/app/services/tms_service.py` and register router `/api/integrations/tms` in `apps/api/routers/tms.py` & `main.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_tms_ingestion.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/tms_service.py apps/api/routers/tms.py apps/api/main.py apps/api/tests/test_tms_ingestion.py
git commit -m "feat(tms): add universal TMS webhook router and ingestion service"
```

---

## Sub-Phase 3.2 — EDI / X12 Parsing Engine

### Task 4: EDI 214 Carrier Shipment Status Parser

**Files:**
- Create: `apps/api/app/parsers/edi/edi_214_parser.py`
- Test: `apps/api/tests/test_edi_214_parser.py`

**Interfaces:**
- Consumes: `pyx12` library, `carmack_engine`
- Produces: `EDI214ParseResult` model containing delivery timestamp, status exception code, and calculated Carmack 9-month and concealed-damage 5-day deadline dates.

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime
from apps/api/app/parsers/edi/edi_214_parser import parse_edi_214

SAMPLE_EDI_214 = """ISA*00*          *00*          *ZZ*CARRIER        *ZZ*BROKER         *260820*1120*U*00401*000000001*0*P*>~
GS*QM*CARRIER*BROKER*20260820*1120*1*X*004010~
ST*214*0001~
B10*PRO12345*BOL98765*CARRIER~
LX*1~
AT7*AG*NS***20260820*1120*LT~
SE*5*0001~
GE*1*1~
IEA*1*000000001~"""

def test_parse_edi_214_damage_exception():
    result = parse_edi_214(SAMPLE_EDI_214)
    assert result.pro_number == "PRO12345"
    assert result.bol_number == "BOL98765"
    assert result.status_code == "AG"
    assert result.is_damage_exception is True
    assert result.delivery_at.strftime("%Y-%m-%d") == "2026-08-20"
    # Carmack 9 months from Aug 20, 2026 -> May 20, 2027
    assert result.carmack_deadline_at.strftime("%Y-%m-%d") == "2027-05-20"
    # Concealed 5 days from Aug 20, 2026 -> Aug 25, 2026
    assert result.concealed_deadline_at.strftime("%Y-%m-%d") == "2026-08-25"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_edi_214_parser.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write minimal implementation**

Implement `edi_214_parser.py` using `pyx12` / segment matching and `dateutil.relativedelta(months=9)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_edi_214_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/parsers/edi/edi_214_parser.py apps/api/tests/test_edi_214_parser.py
git commit -m "feat(edi): add EDI 214 shipment status parser with Carmack date triggers"
```

---

### Task 5: EDI 210 Freight Details & Invoice Parser

**Files:**
- Create: `apps/api/app/parsers/edi/edi_210_parser.py`
- Test: `apps/api/tests/test_edi_210_parser.py`

**Interfaces:**
- Consumes: `valuation_engine`
- Produces: `EDI210ParseResult` with linehaul charges, fuel, weight, and damage ratio verification logic.

- [ ] **Step 1: Write the failing test**

```python
from apps/api/app/parsers/edi/edi_210_parser import parse_edi_210

SAMPLE_EDI_210 = """ISA*00*          *00*          *ZZ*CARRIER        *ZZ*BROKER         *260820*1120*U*00401*000000002*0*P*>~
GS*IM*CARRIER*BROKER*20260820*1120*2*X*004010~
ST*210*0002~
B3*210123*BOL98765**PP*20260820*2000000**20260820*035~
N1*CN*CONSIGNEE NAME~
L3*4000*G***2000000*****100~
SE*6*0002~
GE*1*2~
IEA*1*000000002~"""

def test_parse_edi_210_invoice():
    result = parse_edi_210(SAMPLE_EDI_210)
    assert result.invoice_number == "210123"
    assert result.invoice_total == 20000.00
    assert result.weight == 4000.0
    assert result.total_pieces == 100
    # Ratio math test: 40 damaged out of 100 pieces on $20,000 invoice = $8,000
    claimed = result.calculate_damaged_amount(damaged_qty=40)
    assert claimed == 8000.00
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_edi_210_parser.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write minimal implementation**

Implement `edi_210_parser.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_edi_210_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/parsers/edi/edi_210_parser.py apps/api/tests/test_edi_210_parser.py
git commit -m "feat(edi): add EDI 210 freight invoice parser with damage ratio valuation"
```

---

### Task 6: EDI 204 / 211 Load Tender Parser & EDIService Integration

**Files:**
- Create: `apps/api/app/parsers/edi/edi_204_211_parser.py`
- Create: `apps/api/app/services/edi_service.py`
- Test: `apps/api/tests/test_edi_service.py`

**Interfaces:**
- Consumes: `edi_214_parser`, `edi_210_parser`, `edi_204_211_parser`
- Produces: `EDIService.ingest_edi_file(file_content: str)`

- [ ] **Step 1: Write the failing test**

```python
from apps/api/app/services/edi_service import EDIService

def test_edi_service_detects_and_parses_214():
    sample_214 = "ST*214*0001~\nB10*PRO111*BOL111*CARRIER~\nAT7*AG*NS***20260820*1120*LT~\nSE*4*0001~"
    result = EDIService.process_edi_payload(sample_214)
    assert result["transaction_set"] == "214"
    assert result["parsed_data"]["status_code"] == "AG"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_edi_service.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write minimal implementation**

Implement `edi_204_211_parser.py` and `edi_service.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_edi_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/parsers/edi/edi_204_211_parser.py apps/api/app/services/edi_service.py apps/api/tests/test_edi_service.py
git commit -m "feat(edi): add EDI 204/211 parser and unified EDIService engine"
```

---

## Sub-Phase 3.3 — Durable Stateful Workflow Orchestration Engine

### Task 7: LangGraph Claim Lifecycle State Graph & Postgres Checkpointer

**Files:**
- Create: `apps/api/app/workflows/claim_workflow_graph.py`
- Create: `apps/api/app/workflows/postgres_checkpointer.py`
- Test: `apps/api/tests/test_durable_workflow.py`

**Interfaces:**
- Consumes: LangGraph framework, `submission_service`, `sla_service`, `carmack_lawsuit_service`
- Produces: `build_claim_workflow_graph()`, `SupabasePostgresCheckpointer`

- [ ] **Step 1: Write the failing test**

```python
from apps/api/app/workflows/claim_workflow_graph import build_claim_workflow_graph, ClaimWorkflowState

def test_claim_workflow_graph_transitions():
    graph = build_claim_workflow_graph()
    initial_state = ClaimWorkflowState(
        claim_id="CLM-TEST-001",
        status="DRAFT",
        is_approved_by_human=False,
        claimed_amount=6000.00
    )
    # Attempting to jump directly to SUBMITTED without approval must fail or halt at interrupt
    next_state = graph.invoke(initial_state)
    assert next_state["status"] in ["DRAFT", "EVIDENCE_COLLECTION", "UNDER_REVIEW"]
    assert next_state["status"] != "SUBMITTED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_durable_workflow.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write minimal implementation**

Implement `claim_workflow_graph.py` and `postgres_checkpointer.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_durable_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/workflows/claim_workflow_graph.py apps/api/app/workflows/postgres_checkpointer.py apps/api/tests/test_durable_workflow.py
git commit -m "feat(workflow): implement LangGraph claim workflow state graph with Postgres checkpointer"
```

---

### Task 8: Event Triggers & Documentation Sync (`architecture.md` & `phases.md`)

**Files:**
- Create: `apps/api/app/workflows/workflow_triggers.py`
- Modify: `architecture.md:1-190`
- Modify: `phases.md:297-304`
- Test: `apps/api/tests/test_workflow_triggers.py`

**Interfaces:**
- Consumes: `sla_service`, `carmack_lawsuit_service`
- Produces: `evaluate_workflow_triggers(claim_id)` (Day 30 SLA alert, Day 90 Carmack filing countdown alert, Day 120 Senior Approver escalation).

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timedelta
from apps/api/app/workflows/workflow_triggers import evaluate_workflow_triggers

def test_workflow_day_30_and_90_triggers():
    submitted_at = datetime.now() - timedelta(days=35)
    delivery_at = datetime.now() - timedelta(days=250) # 8+ months ago -> Day 90 warning
    alerts = evaluate_workflow_triggers(
        submitted_at=submitted_at,
        delivery_at=delivery_at,
        carrier_acknowledged=False
    )
    assert "DAY_30_SLA_OVERDUE" in alerts
    assert "DAY_90_CARMACK_WARNING" in alerts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_workflow_triggers.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write minimal implementation**

Implement `workflow_triggers.py` and update `architecture.md` and `phases.md` to document Phase 3 architecture decisions.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_workflow_triggers.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite & frontend build verification**

Run: `pytest apps/api/tests/` (Verify 100% clean pass)
Run: `cd apps/web && npm run build` (Verify 0 TS errors)

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/workflows/workflow_triggers.py architecture.md phases.md apps/api/tests/test_workflow_triggers.py
git commit -m "feat(workflow): add Day 30/90/120 event triggers and update architecture.md docs"
```
