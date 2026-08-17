import os
import sys
import datetime
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import SessionLocal, Base, engine
from app.models.domain_models import (
    Organization, User, CustomerPolicy, Carrier, CarrierRuleSet,
    CarrierClaimRule, Shipment, Claim, ClaimFact, ClaimRequirement
)

def seed_data(db: Session) -> dict:
    """
    Idempotent seed function for demo data.
    Returns dictionary with counts of newly created items.
    """
    created_counts = {
        "organizations": 0,
        "users": 0,
        "customer_policies": 0,
        "carriers": 0,
        "carrier_rule_sets": 0,
        "carrier_claim_rules": 0,
        "shipments": 0,
        "claims": 0
    }

    # 1. Organization
    org = db.query(Organization).filter(Organization.id == "org-apex").first()
    if not org:
        org = Organization(
            id="org-apex",
            name="Apex Freight Brokers",
            type="broker",
            status="active",
            timezone="America/New_York",
            currency="USD",
            contingency_rate=0.20,
            high_value_threshold=5000.0
        )
        db.add(org)
        created_counts["organizations"] += 1

    # 2. User (Sarah Jenkins)
    user = db.query(User).filter(User.id == "usr-1").first()
    if not user:
        user = User(
            id="usr-1",
            organization_id="org-apex",
            name="Sarah Jenkins",
            email="sarah.jenkins@apexfreight.com",
            role="Claims Manager",
            status="active"
        )
        db.add(user)
        created_counts["users"] += 1

    # 3. Customer Policy
    policy = db.query(CustomerPolicy).filter(CustomerPolicy.id == "pol-apex-v1").first()
    if not policy:
        policy = CustomerPolicy(
            id="pol-apex-v1",
            organization_id="org-apex",
            high_value_threshold=5000.0,
            approval_policy_version="v1.0",
            contingency_rate=0.20,
            timezone="America/New_York"
        )
        db.add(policy)
        created_counts["customer_policies"] += 1

    # 4. Carriers
    # Primary Verified Carrier: ABC Trucking
    abc_carrier = db.query(Carrier).filter(Carrier.id == "car-abc").first()
    if not abc_carrier:
        abc_carrier = Carrier(
            id="car-abc",
            canonical_name="ABC Trucking",
            aliases={"names": ["ABC Freight", "ABC Express"]},
            mc_number="MC-847291",
            active=True
        )
        db.add(abc_carrier)
        created_counts["carriers"] += 1

        # Rule Set for ABC Trucking
        abc_rule_set = CarrierRuleSet(
            id="crs-abc-2026",
            carrier_id="car-abc",
            version="v2026.1",
            rule_status="active",
            source_reference="ABC Freight Tariff 100-A Item 450 (Verified)"
        )
        db.add(abc_rule_set)
        created_counts["carrier_rule_sets"] += 1

        # Claim Rule for ABC Trucking
        abc_rule = CarrierClaimRule(
            id="ccr-abc-damage",
            carrier_rule_set_id="crs-abc-2026",
            claim_type="Cargo Damage",
            filing_window_type="Carmack",
            filing_window_value=9,
            filing_window_unit="months",
            required_document_type={"required": ["BOL", "POD", "Invoice", "Photo"]},
            submission_channel="email"
        )
        db.add(abc_rule)
        created_counts["carrier_claim_rules"] += 1

    # Unverified Secondary Carriers (Tagged explicitly per rules.md)
    swift_carrier = db.query(Carrier).filter(Carrier.id == "car-swift").first()
    if not swift_carrier:
        swift_carrier = Carrier(
            id="car-swift",
            canonical_name="Swift Line Logistics",
            mc_number="MC-192837",
            active=True
        )
        db.add(swift_carrier)
        created_counts["carriers"] += 1

        swift_rule_set = CarrierRuleSet(
            id="crs-swift-2026",
            carrier_id="car-swift",
            version="v2026.1",
            rule_status="active",
            source_reference="DEMO DATA — UNVERIFIED"
        )
        db.add(swift_rule_set)

    midwest_carrier = db.query(Carrier).filter(Carrier.id == "car-midwest").first()
    if not midwest_carrier:
        midwest_carrier = Carrier(
            id="car-midwest",
            canonical_name="Midwest Freight Co.",
            mc_number="MC-564738",
            active=True
        )
        db.add(midwest_carrier)
        created_counts["carriers"] += 1

        midwest_rule_set = CarrierRuleSet(
            id="crs-midwest-2026",
            carrier_id="car-midwest",
            version="v2026.1",
            rule_status="active",
            source_reference="DEMO DATA — UNVERIFIED"
        )
        db.add(midwest_rule_set)

    # 5. Primary Shipment & Claim: PRO-847293 (Cargo Damage, live processed)
    shipment_primary = db.query(Shipment).filter(Shipment.id == "shp-847293").first()
    if not shipment_primary:
        shipment_primary = Shipment(
            id="shp-847293",
            organization_id="org-apex",
            external_reference="PRO-847293",
            bol_number="BOL-847293",
            carrier_id="car-abc",
            shipper_name="Acme Industrial Corp",
            consignee_name="Global Distribution Logistics",
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_at=datetime.datetime(2025, 12, 10, 10, 0, tzinfo=datetime.timezone.utc),
            delivery_at=datetime.datetime(2025, 12, 15, 14, 30, tzinfo=datetime.timezone.utc),
            declared_value=20000.0,
            currency="USD",
            commodity="Electronics / Server Racks",
            quantity=10,
            weight=4500.0
        )
        db.add(shipment_primary)
        created_counts["shipments"] += 1

    claim_primary = db.query(Claim).filter(Claim.id == "clm-847293").first()
    if not claim_primary:
        claim_primary = Claim(
            id="clm-847293",
            organization_id="org-apex",
            shipment_id="shp-847293",
            claim_type="Cargo Damage",
            status="UNDER_REVIEW",
            claimed_amount=8000.0,
            currency="USD",
            deadline_at=datetime.datetime(2026, 9, 15, 23, 59, 59, tzinfo=datetime.timezone.utc),
            concealed_deadline_at=datetime.datetime(2025, 12, 20, 23, 59, 59, tzinfo=datetime.timezone.utc),
            human_threshold_triggered=True,
            elevated_approval_acknowledged=False,
            is_approved_by_human=False,
            owner_user_id="usr-1"
        )
        db.add(claim_primary)
        created_counts["claims"] += 1

    # 6. Secondary Static Display Rows for UI Testing (Shortage & Lost Cargo)
    claim_shortage = db.query(Claim).filter(Claim.id == "clm-773920").first()
    if not claim_shortage:
        shp_shortage = Shipment(
            id="shp-773920",
            organization_id="org-apex",
            external_reference="PRO-773920",
            bol_number="BOL-773920",
            carrier_id="car-swift",
            shipper_name="Midwest Supply Co",
            consignee_name="Target Corp Warehouse",
            declared_value=1200.0
        )
        db.add(shp_shortage)
        claim_shortage = Claim(
            id="clm-773920",
            organization_id="org-apex",
            shipment_id="shp-773920",
            claim_type="Shortage",
            status="DRAFT",
            claimed_amount=1200.0,
            owner_user_id="usr-1"
        )
        db.add(claim_shortage)

    db.commit()
    return created_counts

if __name__ == "__main__":
    if os.getenv("ENV", "local") == "local":
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            res = seed_data(db)
            print(f"Seed completed successfully: {res}")
        finally:
            db.close()
    else:
        print("Skipped auto-seed: ENV is not set to 'local'")
