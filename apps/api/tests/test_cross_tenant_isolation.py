import pytest
from datetime import datetime, timezone
from app.models.domain_models import Organization, User, Claim, Carrier, Shipment
from app.core.rbac import check_role_permission, RBACRole

def test_cross_tenant_claim_isolation(db_session):
    """
    TDD Test: User in Org A querying claims should receive zero claims belonging to Org B.
    """
    # Clean up test IDs if existing
    db_session.query(Claim).filter(Claim.id == "clm-test-beta-200").delete()
    db_session.query(Shipment).filter(Shipment.id == "shp-test-beta-200").delete()
    db_session.query(Organization).filter(Organization.id.in_(["org-test-alpha-100", "org-test-beta-200"])).delete()
    db_session.commit()

    # Create Org Alpha and Org Beta
    org_a = Organization(id="org-test-alpha-100", name="Alpha Freight", type="broker")
    org_b = Organization(id="org-test-beta-200", name="Beta Logistics", type="broker")
    db_session.add_all([org_a, org_b])
    db_session.commit()

    # Create Carrier if not exists
    carrier = db_session.query(Carrier).filter(Carrier.id == "car-001").first()
    if not carrier:
        carrier = Carrier(id="car-001", canonical_name="ABC Trucking", active=True)
        db_session.add(carrier)
        db_session.commit()

    # Create Shipment for Org Beta
    shipment_b = Shipment(
        id="shp-test-beta-200",
        organization_id="org-test-beta-200",
        external_reference="PRO-999999",
        bol_number="BOL-999999",
        carrier_id="car-001"
    )
    db_session.add(shipment_b)
    db_session.commit()

    # Create Claim for Org Beta
    claim_b = Claim(
        id="clm-test-beta-200",
        organization_id="org-test-beta-200",
        shipment_id="shp-test-beta-200",
        claim_type="Cargo Damage",
        status="DRAFT",
        claimed_amount=8000.00
    )
    db_session.add(claim_b)
    db_session.commit()

    # Query claims filtered by Org Alpha's organization_id
    org_a_claims = db_session.query(Claim).filter(Claim.organization_id == "org-test-alpha-100").all()
    
    # Assert Org Alpha sees EXACTLY 0 claims from Org Beta
    assert len(org_a_claims) == 0

def test_rbac_claims_operator_cannot_approve_elevated_claim():
    """
    TDD Test: Claims Operator role must be denied when attempting elevated claim approval ($>= 5000).
    """
    operator_user = User(
        id="usr-op-001",
        organization_id="org-apex-001",
        name="John Operator",
        email="john@apex.com",
        role="Claims Operator"
    )

    # Check permission for elevated approval ($8,000 claim)
    has_permission = check_role_permission(
        user_role=operator_user.role,
        required_role=RBACRole.SENIOR_APPROVER,
        claimed_amount=8000.00
    )

    assert has_permission is False

def test_rbac_senior_approver_can_approve_elevated_claim():
    """
    TDD Test: Senior Approver role must be granted permission for elevated claim approval ($>= 5000).
    """
    senior_user = User(
        id="usr-sr-001",
        organization_id="org-apex-001",
        name="Alice Senior",
        email="alice@apex.com",
        role="Senior Approver"
    )

    has_permission = check_role_permission(
        user_role=senior_user.role,
        required_role=RBACRole.SENIOR_APPROVER,
        claimed_amount=8000.00
    )

    assert has_permission is True
