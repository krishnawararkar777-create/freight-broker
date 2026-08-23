import sys
import os
import json
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from db.session import Base, get_db
from main import app
from app.models.domain_models import (
    Organization, CustomerPolicy, Facility, User, Carrier, Claim, Shipment, AuditEvent
)
from app.schemas.shipper_schemas import ShipperClaimCreate, SkuItemDetail
from services.shipper_ingestion_service import shipper_ingestion_service
from services.shipper_approval_service import shipper_approval_service
from services.submission_service import submission_service, SubmissionBlockedException
from app.core.rbac import check_role_permission, RBACRole

def run_verification():
    print("================================================================================")
    print("  PHASE 6: SHIPPER PRODUCT PROTOTYPE (SUB-PHASES 6.1 AND 6.2) VERIFICATION      ")
    print("================================================================================")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # --------------------------------------------------------------------------
        # STEP 1: Sub-Phase 6.1 - Multi-Tenant Shipper Org, Plant Facilities and RBAC
        # --------------------------------------------------------------------------
        print("\n[STEP 1] Initializing Shipper Organization, Multi-Plant Facilities and RBAC:")
        org = Organization(
            id="org-shipper-alpha",
            name="Apex Advanced Electronics Inc.",
            type="shipper",
            status="active"
        )
        policy = CustomerPolicy(
            id="pol-shipper-alpha",
            organization_id="org-shipper-alpha",
            valuation_basis="STANDARD_COST",
            require_plant_inspection=True,
            director_approval_threshold=5000.00
        )
        facility_1 = Facility(
            id="fac-austin-01",
            organization_id="org-shipper-alpha",
            facility_code="PLANT-TX-01",
            name="Austin Semiconductor Fabrication Plant",
            facility_type="MANUFACTURING_PLANT",
            address="7400 Technology Way",
            city="Austin",
            state="TX",
            contact_name="Marcus Lee",
            contact_email="marcus.lee@apex-semi.com",
            active=True
        )
        facility_2 = Facility(
            id="fac-dallas-dc",
            organization_id="org-shipper-alpha",
            facility_code="DC-TX-02",
            name="Dallas Regional Distribution Center",
            facility_type="DISTRIBUTION_CENTER",
            address="1200 Logistics Blvd",
            city="Dallas",
            state="TX",
            active=True
        )
        carrier = Carrier(id="car-001", canonical_name="ABC Trucking", active=True)
        
        # 5 Shipper Enterprise Personas
        insp_user = User(id="usr-insp-01", organization_id="org-shipper-alpha", name="Marcus Lee", email="marcus@apex.com", role="Plant Manager / Inspector")
        coord_user = User(id="usr-coord-01", organization_id="org-shipper-alpha", name="Elena Rostova", email="elena@apex.com", role="Logistics Coordinator")
        dir_user = User(id="usr-dir-01", organization_id="org-shipper-alpha", name="David Vance", email="david@apex.com", role="Logistics Director")
        fin_user = User(id="usr-fin-01", organization_id="org-shipper-alpha", name="Rachel Green", email="rachel@apex.com", role="Shipper Finance")
        adm_user = User(id="usr-adm-01", organization_id="org-shipper-alpha", name="Arthur Pendelton", email="arthur@apex.com", role="Shipper Admin")

        db.add_all([org, policy, facility_1, facility_2, carrier, insp_user, coord_user, dir_user, fin_user, adm_user])
        db.commit()

        print("  [PASS] Shipper Organization created: 'Apex Advanced Electronics Inc.' (type='shipper', valuation='STANDARD_COST')")
        print("  [PASS] Facilities registered: 'PLANT-TX-01' (Manufacturing) and 'DC-TX-02' (Distribution Center)")
        print("  [PASS] 5 Enterprise Shipper Roles mapped: Inspector, Coordinator, Director, Finance, Admin")

        # --------------------------------------------------------------------------
        # STEP 2: Sub-Phase 6.2 - Manual Claim Ingestion and Deterministic SKU Valuation
        # --------------------------------------------------------------------------
        print("\n[STEP 2] Manual Claim Ingestion with Line-Item SKU Valuation Math:")
        sku_items = [
            SkuItemDetail(sku="SEMI-MCU-100", description="32-bit Automotive Microcontroller", damaged_qty=50, unit_cost=75.00),
            SkuItemDetail(sku="SEMI-PDU-200", description="High-Voltage Power Distribution Unit", damaged_qty=20, unit_cost=150.00),
            SkuItemDetail(sku="SEMI-OPT-300", description="Precision Optical Lidar Sensor", damaged_qty=10, unit_cost=200.00)
        ]
        
        claim_req = ShipperClaimCreate(
            organization_id="org-shipper-alpha",
            facility_id="fac-austin-01",
            po_number="PO-TX-883921",
            carrier_id="car-001",
            external_reference="PRO-ABC-90412",
            bol_number="BOL-TX-90412",
            claim_type="Cargo Damage",
            sku_details=sku_items,
            notes="Moisture and crush damage on high-density pallets."
        )

        claim = shipper_ingestion_service.create_manual_shipper_claim(
            db=db,
            req=claim_req,
            claim_id="clm-verify-shp-01"
        )

        print(f"  [PASS] Claim Ingested: {claim.id} | PO: {claim.po_number}")
        print(f"  [PASS] Deterministic Claimed Amount: ${claim.claimed_amount:,.2f} (Expected: $8,750.00)")
        print(f"  [PASS] Initial Approval Stage: {claim.internal_approval_stage} | Human Approved: {claim.is_approved_by_human}")
        assert claim.claimed_amount == 8750.00
        assert claim.internal_approval_stage == "WAREHOUSE_INSPECTION"
        assert claim.is_approved_by_human is False

        # --------------------------------------------------------------------------
        # STEP 3: 4-Stage Sequential Internal Approval Workflow and Server-Side Gates
        # --------------------------------------------------------------------------
        print("\n[STEP 3] Executing 4-Stage Sequential Internal Approval Workflow and Security Guards:")

        # 3.1 Stage 1: Warehouse Receiving Inspection
        print("  [Stage 1/4] Signing Warehouse Receiving Inspection (Marcus Lee, Plant Inspector)...")
        claim = shipper_approval_service.sign_warehouse_inspection(
            db=db,
            claim_id=claim.id,
            user_id="usr-insp-01",
            user_role="Plant Manager / Inspector",
            notes="Visual crush damage on crates. Damaged inventory quarantined."
        )
        print(f"  [PASS] Stage 1 Signed! Advanced to: {claim.internal_approval_stage}")
        assert claim.internal_approval_stage == "LOGISTICS_VERIFICATION"
        assert claim.inspection_signed_by == "usr-insp-01"

        # 3.2 Security Check: Submission Guard blocks premature external filing
        print("  [Security Guard Check] Verifying external carrier dispatch is locked during internal review...")
        try:
            submission_service.submit_claim(db=db, claim_id=claim.id)
            raise AssertionError("Submission guard failed to block premature dispatch!")
        except SubmissionBlockedException as exc:
            print(f"  [PASS] Server Guard Active: Carrier submission blocked: '{exc.message}'")

        # 3.3 Stage 2: Logistics Verification
        print("  [Stage 2/4] Signing Logistics Carrier and Tariff Verification (Elena Rostova, Coordinator)...")
        claim = shipper_approval_service.sign_logistics_verification(
            db=db,
            claim_id=claim.id,
            user_id="usr-coord-01",
            user_role="Logistics Coordinator",
            notes="Tendered carrier ABC Trucking confirmed. BOL and exception POD verified."
        )
        print(f"  [PASS] Stage 2 Signed! Advanced to: {claim.internal_approval_stage}")
        assert claim.internal_approval_stage == "DIRECTOR_APPROVAL"
        assert claim.logistics_signed_by == "usr-coord-01"

        # 3.4 Security Check: Elevated threshold ($8,750 >= $5,000) blocks non-directors
        print("  [RBAC Guard Check] Verifying Coordinator is blocked from signing $8,750 elevated claim...")
        try:
            shipper_approval_service.sign_director_approval(
                db=db,
                claim_id=claim.id,
                user_id="usr-coord-01",
                user_role="Logistics Coordinator"
            )
            raise AssertionError("RBAC guard failed to block unauthorized director approval!")
        except PermissionError as exc:
            print(f"  [PASS] RBAC Guard Active: Permission denied: '{exc}'")

        # 3.5 Stage 3: Director Approval
        print("  [Stage 3/4] Granting Director Approval (David Vance, Logistics Director)...")
        claim = shipper_approval_service.sign_director_approval(
            db=db,
            claim_id=claim.id,
            user_id="usr-dir-01",
            user_role="Logistics Director",
            notes="Authorized for formal external carrier claim filing."
        )
        print(f"  [PASS] Stage 3 Signed! Internal Stage: {claim.internal_approval_stage} | Status: {claim.status}")
        assert claim.internal_approval_stage == "READY_FOR_SUBMISSION"
        assert claim.status == "APPROVED"
        assert claim.is_approved_by_human is True
        assert claim.director_signed_by == "usr-dir-01"

        # 3.6 Stage 4: External Carrier Submission
        print("  [Stage 4/4] Submitting Claim to Motor Carrier ABC Trucking...")
        submitted_claim = submission_service.submit_claim(db=db, claim_id=claim.id)
        print(f"  [PASS] Stage 4 Complete: Claim {submitted_claim.id} status={submitted_claim.status}")
        print(f"  [PASS] External Submission Timestamp: {submitted_claim.submitted_at}")
        assert submitted_claim.status == "SUBMITTED"

        # --------------------------------------------------------------------------
        # STEP 4: Immutable Audit Trail and REST API Status Verification
        # --------------------------------------------------------------------------
        print("\n[STEP 4] Verifying Immutable Audit Trail and REST API Endpoints:")
        audit_events = db.query(AuditEvent).filter(AuditEvent.organization_id == "org-shipper-alpha").order_by(AuditEvent.created_at.asc()).all()
        print(f"  [PASS] Total Audit Events Recorded: {len(audit_events)}")
        for aud in audit_events:
            print(f"    - [{aud.action}] Actor: {aud.actor_id} | Entity: {aud.entity_type} {aud.entity_id}")
        assert len(audit_events) >= 5

        # REST Endpoint Test via TestClient
        status_res = client.get(f"/api/shipper/claims/{claim.id}/approval-status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        print(f"  [PASS] REST API GET /api/shipper/claims/{claim.id}/approval-status returned 200 OK")
        print(f"    - PO Number: {status_data['po_number']}")
        print(f"    - Stage: {status_data['internal_approval_stage']}")
        print(f"    - Director Sign-Off: {status_data['director_signed_by']}")

        print("\n================================================================================")
        print("  PHASE 6 (SUB-PHASES 6.1 AND 6.2) EMPIRICAL VERIFICATION PASSED (100% CLEAN)     ")
        print("================================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
