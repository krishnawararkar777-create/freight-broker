# Phase 0.2 Core Data Models & Database Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 19 SQLAlchemy ORM models, create Alembic migration `001_initial_schema.py` enabling `pgvector` and creating all tables, and create an idempotent seed script `scripts/seed_demo_data.py` (gated by `ENV=local`).

**Architecture:** SQLAlchemy models under `apps/api/app/models/`, Alembic migration script under `apps/api/db/migrations/versions/001_initial_schema.py`, and seed script under `apps/api/scripts/seed_demo_data.py`.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0 ORM, Alembic, PostgreSQL 16 (`pgvector`), Pytest.

**Spec:** `phases.md` Section 0.2, `architecture.md` Section 5, `rules.md` Section 2.

## Global Constraints

- **Python Version:** 3.11
- **Database:** PostgreSQL 16 with `pgvector` extension enabled in `001_initial_schema.py`.
- **Environment Gating:** Auto-seeding gated behind `if os.getenv("ENV") == "local":`.
- **Idempotency:** Running `seed_demo_data.py` multiple times must NOT duplicate rows.
- **Unverified Carriers:** Secondary carriers (`Swift Line Logistics`, `Midwest Freight Co.`) MUST have `source_reference = "DEMO DATA — UNVERIFIED"`.

---

### Task 1: TDD — Write Idempotency and Model Test Suite (RED)

**Files:**
- Create: `apps/api/tests/test_seed_demo_data.py`
- Create: `apps/api/tests/test_models.py`

- [ ] **Step 1: Write failing idempotency test for seed_demo_data**

```python
# apps/api/tests/test_seed_demo_data.py
import pytest
from sqlalchemy.orm import Session
from db.session import SessionLocal

def test_seed_demo_data_idempotency():
    """Running seed_demo_data twice must not duplicate rows."""
    from scripts.seed_demo_data import seed_data
    
    db: Session = SessionLocal()
    try:
        # Run 1
        counts_run_1 = seed_data(db)
        assert counts_run_1["organizations"] == 1
        assert counts_run_1["users"] == 1
        assert counts_run_1["carriers"] >= 1

        # Run 2
        counts_run_2 = seed_data(db)
        assert counts_run_2["organizations"] == 0, "Second seed run created duplicate org"
        assert counts_run_2["users"] == 0, "Second seed run created duplicate user"
    finally:
        db.close()
```

- [ ] **Step 2: Run test to verify RED state**
  Run `pytest apps/api/tests/test_seed_demo_data.py` and confirm it fails with `ModuleNotFoundError: No module named 'scripts.seed_demo_data'`.

---

### Task 2: Implement 19 SQLAlchemy Models (GREEN)

**Files:**
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/models/__init__.py`
- Create: `apps/api/app/models/organization.py`
- Create: `apps/api/app/models/user.py`
- Create: `apps/api/app/models/customer_policy.py`
- Create: `apps/api/app/models/carrier.py`
- Create: `apps/api/app/models/carrier_rule_set.py`
- Create: `apps/api/app/models/carrier_claim_rule.py`
- Create: `apps/api/app/models/shipment.py`
- Create: `apps/api/app/models/claim.py`
- Create: `apps/api/app/models/document.py`
- Create: `apps/api/app/models/document_evidence.py`
- Create: `apps/api/app/models/claim_fact.py`
- Create: `apps/api/app/models/claim_requirement.py`
- Create: `apps/api/app/models/claim_submission.py`
- Create: `apps/api/app/models/communication.py`
- Create: `apps/api/app/models/task.py`
- Create: `apps/api/app/models/recovery_event.py`
- Create: `apps/api/app/models/fee_event.py`
- Create: `apps/api/app/models/invoice.py`
- Create: `apps/api/app/models/audit_event.py`

- [ ] **Step 1: Define all 19 models inheriting from `Base` (`db.session.Base`)**
  Ensure foreign key relationships, indexes, and field constraints match `phases.md` Section 0.2.

---

### Task 3: Create Alembic Migration `001_initial_schema.py` & Database Migration Execution

**Files:**
- Create: `apps/api/db/migrations/versions/001_initial_schema.py`

- [ ] **Step 1: Write 001_initial_schema.py Alembic migration**
  Include `op.execute("CREATE EXTENSION IF NOT EXISTS vector;")` and create all 19 tables with indexes.

- [ ] **Step 2: Run Alembic migration against local Postgres database**
  Execute `alembic upgrade head`.

---

### Task 4: Implement Idempotent Seed Script `scripts/seed_demo_data.py` (GREEN)

**Files:**
- Create: `apps/api/scripts/seed_demo_data.py`

- [ ] **Step 1: Implement `seed_data(db)` function**
  Idempotently seed:
  - Org: `Apex Freight Brokers` (`high_value_threshold = 5000`, `contingency_rate = 0.20`).
  - User: `Sarah Jenkins` (`usr-1`, `Claims Manager`).
  - Primary Carrier: `ABC Trucking` (`CarrierRuleSet v2026.1`: Carmack 9-month window, 5-day concealed damage window, `source_reference = "ABC Freight Tariff 100-A Item 450 (Verified)"`).
  - Secondary Unverified Carriers: `Swift Line Logistics` & `Midwest Freight Co.` tagged with `source_reference = "DEMO DATA — UNVERIFIED"`.
  - Shipment & Claim: `PRO-847293` (Cargo Damage).
  - Static Display Rows: Shortage & Lost Cargo claims.

- [ ] **Step 2: Re-run Pytest suite to verify GREEN state**
  Run `pytest apps/api/tests/test_seed_demo_data.py` and confirm 100% PASS.

---

### Task 5: Verification & Evidence Gathering

- [ ] **Step 1: Run pytest across full test suite**
- [ ] **Step 2: Run seed_demo_data twice CLI script to verify output**
- [ ] **Step 3: Document raw execution output as evidence before completion**
