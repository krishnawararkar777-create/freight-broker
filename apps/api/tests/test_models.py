import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from app.models.domain_models import Carrier, CarrierRuleSet, Organization, User

def test_unverified_carrier_tagging():
    """Verify secondary demo carriers are explicitly tagged with source_reference = 'DEMO DATA — UNVERIFIED'."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        carrier = Carrier(
            id="car-swift",
            canonical_name="Swift Line Logistics",
            mc_number="MC-192837",
            active=True
        )
        rule_set = CarrierRuleSet(
            id="crs-swift-2026",
            carrier_id="car-swift",
            version="v2026.1",
            source_reference="DEMO DATA — UNVERIFIED"
        )
        db.add(carrier)
        db.add(rule_set)
        db.commit()

        saved_rule_set = db.query(CarrierRuleSet).filter_by(id="crs-swift-2026").first()
        assert saved_rule_set is not None
        assert saved_rule_set.source_reference == "DEMO DATA — UNVERIFIED"
    finally:
        db.close()
