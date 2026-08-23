# Phase 6: Shipper Product (Sub-Phases 6.1 & Scoped-Down 6.2) Design Specification

**Author:** Antigravity / Manus AI
**Date:** August 23, 2026
**Status:** Approved for Implementation (Validation-Gated)

---

## 1. Executive Summary & Validation-Gated Strategy

This design specifies the minimum viable prototype for the Shipper Product in Phase 6. Because the direct shipper segment has not yet been validated with a live customer interview, this build is strictly validation-gated:

1. **Sub-Phase 6.1:** Shipper Multi-Tenant Organization Model, Plant/Facility Scoping, and 5 Enterprise Shipper RBAC Roles.
2. **Sub-Phase 6.2 (Minimum Viable Slice Only):** Internal Sequential 4-Stage Approval Routing Engine (WAREHOUSE_INSPECTION -> LOGISTICS_VERIFICATION -> DIRECTOR_APPROVAL -> READY_FOR_SUBMISSION) and manual/document-upload ingestion.
3. **Validation Checkpoint (STOP):** Upon completing 6.1 and 6.2, all development halts until real feedback from an active shipper is gathered.
4. **Explicit Non-Scope:**
   - ZERO SAP/NetSuite/Oracle ERP API connectors.
   - NO Sub-Phase 6.3 (Retail AP deduction/chargeback parsing).
   - NO Sub-Phase 6.4 (Supply chain root-cause analytics engine).
   - NO Sub-Phase 6.5 (Standalone shipper portal UI).

---

## 2. Sub-Phase 6.1: Shipper Multi-Tenant Org Model & Enterprise Roles

### 2.1 Schema Extensions

#### organizations & customer_policies
- organizations.type: Validated string supporting shipper in addition to broker and 3pl.
- customer_policies:
  - aluation_basis: WHOLESALE_INVOICE (default) or STANDARD_COST.
  - equire_plant_inspection: ool (default True for shippers).
  - director_approval_threshold: loat (default 5000.0).

#### acilities (New Domain Model)
Multi-location shippers require plant and distribution center scoping:
- id: String(64), Primary Key
- organization_id: String(64), Foreign Key to organizations.id, Indexed
- acility_code: String(64), Indexed (e.g. PLANT-OH-01)
- 
ame: String(255)
- acility_type: String(64), default MANUFACTURING_PLANT (MANUFACTURING_PLANT | DISTRIBUTION_CENTER)
- ddress, city, state, contact_name, contact_email: Optional Strings
- ctive: Boolean, default True
- created_at: DateTime(timezone=True)

### 2.2 Enterprise Shipper RBAC Role Hierarchy
Built directly into pp/core/rbac.py / RBACRole:

1. **Shipper Admin**: System administration, organization setup, facility management, and unrestricted approval authority. Hierarchy: 100.
2. **Logistics Director**: Senior transportation executive. High-value claim approval authority (>= ,000), final sign-off before carrier submission. Hierarchy: 80.
3. **Logistics Coordinator**: Transportation planner. Drafts claims, verifies BOL/POD/carrier matching, advances claims through logistics stage. Hierarchy: 50.
4. **Plant Manager / Inspector**: Receiving / QA lead at a specific plant. Uploads receiving damage photos, fills inspection checklists, signs off on warehouse inspection. Hierarchy: 40.
5. **Shipper Finance**: Accounting / AP analyst. Audit view, write-off ledger access, salvage reconciliation. Hierarchy: 20.

---

## 3. Sub-Phase 6.2: Internal Sequential Approval Engine & Manual Ingestion

### 3.1 Claims Schema Extension
- acility_id: Optional String(64), Foreign Key to facilities.id, Indexed
- po_number: Optional String(128), Indexed
- sku_details: Optional JSON (list of items with sku, description, damaged_qty, unit_cost, total_loss)
- internal_approval_stage: String(64), default WAREHOUSE_INSPECTION
- inspection_signed_by: Optional String(64), Foreign Key to users.id
- inspection_signed_at: Optional DateTime(timezone=True)
- inspection_notes: Optional Text
- logistics_signed_by: Optional String(64), Foreign Key to users.id
- logistics_signed_at: Optional DateTime(timezone=True)
- logistics_notes: Optional Text
- director_signed_by: Optional String(64), Foreign Key to users.id
- director_signed_at: Optional DateTime(timezone=True)
- director_notes: Optional Text

### 3.2 Sequential Internal Approval State Machine
Stages:
1. WAREHOUSE_INSPECTION -> Signed by Plant Manager / Inspector or Shipper Admin.
2. LOGISTICS_VERIFICATION -> Signed by Logistics Coordinator, Logistics Director, or Shipper Admin.
3. DIRECTOR_APPROVAL -> Signed by Logistics Director or Shipper Admin (Mandatory for claimed_amount >= ,000; auto-passable if < ,000).
4. READY_FOR_SUBMISSION -> Status updated to APPROVED and is_approved_by_human = True.
5. SUBMITTED -> Dispatched to carrier via POST /api/claims/{id}/submit.
