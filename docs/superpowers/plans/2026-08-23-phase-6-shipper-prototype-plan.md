# Phase 6: Shipper Product (Sub-Phases 6.1 & Scoped-Down 6.2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build the validated core prototype for the Shipper Product (Sub-Phase 6.1 & Minimum Viable Slice of Sub-Phase 6.2) with enterprise multi-tenancy, plant facilities, 5 shipper RBAC roles, manual/document ingestion, and a 4-stage sequential internal approval state machine, stopping at the validation checkpoint.

**Architecture:** Extend SQLAlchemy organizations and customer_policies models, create a new acilities table with multi-tenant isolation, expand the existing RBAC system with 5 shipper personas, and build a dedicated ShipperApprovalService with a 4-stage sequential state machine and server-side submission gate.

**Tech Stack:** Python 3.11/3.14, FastAPI, SQLAlchemy ORM, Alembic, PostgreSQL 16 (Supabase RLS), Pydantic v2, Pytest.

**Spec:** docs/superpowers/specs/2026-08-23-phase-6-shipper-prototype-design.md

## Global Constraints

- Scope Discipline: Only build Sub-Phase 6.1 and the minimum viable slice of Sub-Phase 6.2.
- Validation Checkpoint: STOP immediately after 6.1 and 6.2 are verified before building 6.3, 6.4, or 6.5.
- Zero ERP Connectors: Manual entry and document upload only; no speculative SAP/NetSuite/Oracle connectors.
- Unified RBAC: Integrate shipper roles into existing Phase 2.1 RBAC; no parallel permission system.
- Deterministic Validation: All state machine transitions are guarded server-side and logged to udit_events.
- TDD Requirement: Write failing tests first before implementing models, services, and endpoints.

---

### Task 1: Sub-Phase 6.1 — Multi-Tenant Org & Facilities Domain Schema

**Files:**
- Create: pps/api/app/schemas/shipper_schemas.py
- Modify: pps/api/app/models/domain_models.py
- Modify: pps/api/routers/facilities.py (or pps/api/routers/shipper.py)
- Test: pps/api/tests/test_shipper_org_isolation.py

**Interfaces:**
- Produces: Facility model, CustomerPolicy shipper fields, FacilityCreate, FacilityResponse schemas.

- [ ] **Step 1: Write the failing test**
Create pps/api/tests/test_shipper_org_isolation.py testing that a Shipper organization with Facilities cannot be accessed by another Broker organization, and verifying Facility model creation.

- [ ] **Step 2: Run test to verify it fails**
Run: pytest apps/api/tests/test_shipper_org_isolation.py -v
Expected: FAIL (Facility model not found)

- [ ] **Step 3: Write minimal implementation**
Modify pps/api/app/models/domain_models.py to add Facility model, update CustomerPolicy with shipper fields (aluation_basis, equire_plant_inspection, director_approval_threshold), and create pps/api/app/schemas/shipper_schemas.py.

- [ ] **Step 4: Run test to verify it passes**
Run: pytest apps/api/tests/test_shipper_org_isolation.py -v
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 2: Sub-Phase 6.1 — 5-Tier Enterprise Shipper RBAC Role Hierarchy

**Files:**
- Modify: pps/api/app/core/rbac.py
- Test: pps/api/tests/test_shipper_rbac.py

**Interfaces:**
- Consumes: RBACRole
- Produces: RBACRole.SHIPPER_ADMIN, RBACRole.LOGISTICS_DIRECTOR, RBACRole.LOGISTICS_COORDINATOR, RBACRole.PLANT_MANAGER_INSPECTOR, RBACRole.SHIPPER_FINANCE, and updated check_role_permission.

- [ ] **Step 1: Write the failing test**
Create pps/api/tests/test_shipper_rbac.py testing role permissions, hierarchy levels, and elevated threshold checks (,000+) across all 5 shipper roles.

- [ ] **Step 2: Run test to verify it fails**
Run: pytest apps/api/tests/test_shipper_rbac.py -v
Expected: FAIL (Role values missing in enum)

- [ ] **Step 3: Write minimal implementation**
Update pps/api/app/core/rbac.py to include the 5 shipper roles and update ROLE_HIERARCHY_LEVELS and check_role_permission for elevated threshold authority (,000+).

- [ ] **Step 4: Run test to verify it passes**
Run: pytest apps/api/tests/test_shipper_rbac.py -v
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 3: Sub-Phase 6.2 — Manual Claim Ingestion Path with SKU Line-Items

**Files:**
- Create: pps/api/services/shipper_ingestion_service.py
- Modify: pps/api/app/models/domain_models.py (Add acility_id, po_number, sku_details, internal_approval_stage columns to Claim)
- Create: pps/api/routers/shipper.py
- Modify: pps/api/main.py
- Test: pps/api/tests/test_shipper_claim_ingestion.py

**Interfaces:**
- Produces: ShipperClaimCreate, shipper_ingestion_service.create_manual_shipper_claim(), POST /api/shipper/claims/manual.

- [ ] **Step 1: Write the failing test**
Create pps/api/tests/test_shipper_claim_ingestion.py testing manual entry of PO, facility, and SKU line-items with deterministic valuation arithmetic.

- [ ] **Step 2: Run test to verify it fails**
Run: pytest apps/api/tests/test_shipper_claim_ingestion.py -v
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
Add columns to Claim model in domain_models.py, implement shipper_ingestion_service.py, create outers/shipper.py, and register router in main.py.

- [ ] **Step 4: Run test to verify it passes**
Run: pytest apps/api/tests/test_shipper_claim_ingestion.py -v
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 4: Sub-Phase 6.2 — 4-Stage Sequential Internal Approval State Machine

**Files:**
- Create: pps/api/services/shipper_approval_service.py
- Modify: pps/api/routers/shipper.py
- Modify: pps/api/services/submission_service.py
- Test: pps/api/tests/test_shipper_approval_engine.py

**Interfaces:**
- Produces: ShipperApprovalService, POST /api/shipper/claims/{id}/approvals/inspection, POST /api/shipper/claims/{id}/approvals/logistics, POST /api/shipper/claims/{id}/approvals/director, GET /api/shipper/claims/{id}/approval-status.

- [ ] **Step 1: Write the failing test**
Create pps/api/tests/test_shipper_approval_engine.py testing:
1. Sequential stage advance (Warehouse -> Logistics -> Director -> Ready for submission).
2. Out-of-order rejection (skipping stage returns 400).
3. Unauthorized role rejection (Inspector signing director stage returns 403).
4. Submission guard enforcement (cannot submit until all required stages approved).

- [ ] **Step 2: Run test to verify it fails**
Run: pytest apps/api/tests/test_shipper_approval_engine.py -v
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
Implement shipper_approval_service.py, add endpoints to outers/shipper.py, update submission_service.py submission guard for shipper claims.

- [ ] **Step 4: Run test to verify it passes**
Run: pytest apps/api/tests/test_shipper_approval_engine.py -v
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 5: End-to-End Verification & Validation Checkpoint Verification

**Files:**
- Create: scripts/verify_subphase_6_prototype.py
- Test: Full Pytest suite pps/api/tests/

- [ ] **Step 1: Create and run end-to-end verification script**
Walk a live test claim through:
- Shipper org creation (Apex Manufacturing)
- Facility creation (Cleveland Assembly Plant 1)
- Manual claim creation with 3 SKU line items (,200 total loss)
- Stage 1 sign-off by Plant Inspector
- Stage 2 sign-off by Logistics Coordinator
- Attempt external submission -> verify blocked (HTTP 403)
- Stage 3 sign-off by Logistics Director
- External submission -> verify success (HTTP 200, status = SUBMITTED)

- [ ] **Step 2: Run full regression test suite**
Run: pytest apps/api/tests -v
Expected: All 172+ tests pass cleanly (100% pass rate).

- [ ] **Step 3: STOP AT VALIDATION CHECKPOINT**
