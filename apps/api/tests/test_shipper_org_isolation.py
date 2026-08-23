import pytest
from datetime import datetime, timezone
from app.models.domain_models import Organization, User, Claim, Carrier, Shipment, Facility, CustomerPolicy

def test_shipper_facility_model_and_isolation(db_session):
    # Clean up test IDs
    db_session.query(Facility).filter(Facility.id.in_(['fac-plant-01', 'fac-plant-02'])).delete()
    db_session.query(CustomerPolicy).filter(CustomerPolicy.organization_id.in_(['org-shipper-alpha', 'org-broker-beta'])).delete()
    db_session.query(Organization).filter(Organization.id.in_(['org-shipper-alpha', 'org-broker-beta'])).delete()
    db_session.commit()

    # 1. Create Shipper Organization
    shipper_org = Organization(
        id='org-shipper-alpha',
        name='Apex Manufacturing Co.',
        type='shipper',
        status='active'
    )
    broker_org = Organization(
        id='org-broker-beta',
        name='Beta Brokerage Inc.',
        type='broker',
        status='active'
    )
    db_session.add_all([shipper_org, broker_org])
    db_session.commit()

    # 2. Add CustomerPolicy for Shipper with valuation basis
    shipper_policy = CustomerPolicy(
        id='pol-shipper-alpha',
        organization_id='org-shipper-alpha',
        valuation_basis='STANDARD_COST',
        require_plant_inspection=True,
        director_approval_threshold=5000.00
    )
    db_session.add(shipper_policy)
    db_session.commit()

    # 3. Create Facilities for Shipper Org
    facility_1 = Facility(
        id='fac-plant-01',
        organization_id='org-shipper-alpha',
        facility_code='PLANT-OH-01',
        name='Cleveland Assembly Plant',
        facility_type='MANUFACTURING_PLANT',
        city='Cleveland',
        state='OH',
        contact_name='Bob Miller',
        contact_email='bob@apexmanufacturing.com',
        active=True
    )
    db_session.add(facility_1)
    db_session.commit()

    # 4. Assert Shipper Org queries find the facility
    shipper_facilities = db_session.query(Facility).filter(Facility.organization_id == 'org-shipper-alpha').all()
    assert len(shipper_facilities) == 1
    assert shipper_facilities[0].facility_code == 'PLANT-OH-01'
    assert shipper_facilities[0].facility_type == 'MANUFACTURING_PLANT'

    # 5. Assert Broker Org queries find 0 facilities
    broker_facilities = db_session.query(Facility).filter(Facility.organization_id == 'org-broker-beta').all()
    assert len(broker_facilities) == 0

    # 6. Verify policy settings
    retrieved_policy = db_session.query(CustomerPolicy).filter(CustomerPolicy.organization_id == 'org-shipper-alpha').first()
    assert retrieved_policy.valuation_basis == 'STANDARD_COST'
    assert retrieved_policy.require_plant_inspection is True
    assert retrieved_policy.director_approval_threshold == 5000.00
