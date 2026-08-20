import pytest
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.session import Base
from scripts.seed_demo_data import seed_data
from app.models.domain_models import Shipment, Claim, AuditEvent, Carrier, Organization
from app.parsers.edi.edi_204_211_parser import parse_edi_204_211, EDI204211ParseResult
from app.parsers.edi.edi_214_parser import EDI214ParseResult
from app.parsers.edi.edi_210_parser import EDI210ParseResult
from app.services.edi_service import EDIService, edi_service

# Sample Payloads
SAMPLE_EDI_204 = """ISA*00*          *00*          *ZZ*SHIPPERSYS     *ZZ*CARRIERHUB     *260820*1000*U*00401*000000010*0*P*>~
GS*SM*SHIPPERSYS*CARRIERHUB*20260820*1000*10*X*004010~
ST*204*0010~
B2**FXFE*LD-2026-9901**PP~
B2A*00*LT~
L11*BOL-887766*BM~
N1*SH*ACME LOGISTICS ORIGIN~
N3*100 INDUSTRIAL PKWY~
N4*CHICAGO*IL*60601*USA~
N1*CN*GLOBAL DISTRIBUTION DEST~
N3*500 COMMERCE WAY~
N4*DALLAS*TX*75201*USA~
L5*1*INDUSTRIAL BEARINGS*35400*CL70~
L0*1*18500.50*LB*18500.50*G*150*PLT~
AMT*DV*45000.00~
SE*12*0010~
GE*1*10~
IEA*1*000000010~"""

SAMPLE_EDI_211 = """ISA*00*          *00*          *ZZ*SHIPPERSYS     *ZZ*CARRIERHUB     *260820*1100*U*00401*000000020*0*P*>~
GS*BL*SHIPPERSYS*CARRIERHUB*20260820*1100*20*X*004010~
ST*211*0020~
BOL*BOL-554433*FXFE*20260820*1100~
B2**FXFE*SHIP-554433**PP~
N1*SH*MIDWEST AUTO PARTS~
N4*DETROIT*MI*48201*USA~
N1*CN*PACIFIC RETAIL LOGISTICS~
N4*LOS ANGELES*CA*90001*USA~
L5*1*AUTOMOTIVE BRAKE ASSEMBLIES*20150*CL60~
L0*1*8200.00*LB*8200.00*G*65*CTN~
AMT*DV*28500.00~
SE*11*0020~
GE*1*20~
IEA*1*000000020~"""

SAMPLE_EDI_214_DAMAGED = """ISA*00*          *00*          *02*FXFE           *01*RECEIVER       *260820*1430*U*00401*000000001*0*P*:~
GS*QM*FXFE*RECEIVER*20260820*1430*1*X*004010~
ST*214*0001~
B10*PRO-998877*BOL-112233*FXFE~
L11*PO-445566*PO~
AT7*AG*DM***20260820*1430*LT~
MS1*CHICAGO*IL*USA~
SE*6*0001~
GE*1*1~
IEA*1*000000001~"""

SAMPLE_EDI_214_SHORTAGE = """ST*214*0002~
B10*PRO-771122*BOL-554433*ODFL~
AT7*SD*SH***20260820*0900*LT~
SE*3*0002~"""

SAMPLE_EDI_214_CLEAN = """ST*214*0003~
B10*PRO-123456*BOL-654321*RDFS~
AT7*D1*NS***20260820*1000*LT~
SE*3*0003~"""

SAMPLE_EDI_210 = """ST*210*0002~
B3*INV-889900*BOL-445566**PP*20260820*1500000**20260820*035~
N1*SH*APEX MANUFACTURING LLC~
N1*CN*WESTERN DISTRIBUTION INC~
L11*PRO-778899*CN~
L3*25000*G***1500000*****250~
SE*6*0002~"""


@pytest.fixture
def test_db():
    """Create a fresh in-memory database for integration testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_data(db)
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# 1. EDI 204 & 211 Unit Tests
# ---------------------------------------------------------------------------

def test_parse_edi_204_load_tender_basic():
    """Verify parsing EDI 204 Motor Carrier Load Tender."""
    result = parse_edi_204_211(SAMPLE_EDI_204)

    assert isinstance(result, EDI204211ParseResult)
    assert result.transaction_set == "204"
    assert result.shipment_reference == "LD-2026-9901"
    assert result.bol_number == "BOL-887766"
    assert result.shipper_name == "ACME LOGISTICS ORIGIN"
    assert result.consignee_name == "GLOBAL DISTRIBUTION DEST"
    assert result.origin_city_state == "CHICAGO, IL"
    assert result.destination_city_state == "DALLAS, TX"
    assert result.commodity == "INDUSTRIAL BEARINGS"
    assert result.nmfc_code == "35400"
    assert result.weight == 18500.50
    assert result.total_pieces == 150
    assert result.declared_value == 45000.00


def test_parse_edi_211_bill_of_lading_basic():
    """Verify parsing EDI 211 Motor Carrier Bill of Lading."""
    result = parse_edi_204_211(SAMPLE_EDI_211)

    assert isinstance(result, EDI204211ParseResult)
    assert result.transaction_set == "211"
    assert result.bol_number == "BOL-554433"
    assert result.shipment_reference == "SHIP-554433"
    assert result.shipper_name == "MIDWEST AUTO PARTS"
    assert result.consignee_name == "PACIFIC RETAIL LOGISTICS"
    assert result.origin_city_state == "DETROIT, MI"
    assert result.destination_city_state == "LOS ANGELES, CA"
    assert result.commodity == "AUTOMOTIVE BRAKE ASSEMBLIES"
    assert result.nmfc_code == "20150"
    assert result.weight == 8200.00
    assert result.total_pieces == 65
    assert result.declared_value == 28500.00


def test_parse_edi_204_211_empty_payload_raises():
    """Verify empty payload raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        parse_edi_204_211("")


def test_parse_edi_204_211_wrong_transaction_set_raises():
    """Verify invalid transaction set in ST header raises ValueError."""
    payload = "ST*999*0001~\nB2**TEST*REF123~"
    with pytest.raises(ValueError, match="Expected EDI transaction set '204' or '211'"):
        parse_edi_204_211(payload)


def test_parse_edi_204_missing_reference_raises():
    """Verify payload without shipment reference raises ValueError."""
    payload = "ST*204*0001~\nN1*SH*ONLY SHIPPER~"
    with pytest.raises(ValueError, match="Missing shipment reference"):
        parse_edi_204_211(payload)


# ---------------------------------------------------------------------------
# 2. EDIService Unified Routing Tests
# ---------------------------------------------------------------------------

def test_edi_service_process_auto_detect_214():
    """Verify EDIService routes EDI 214 payload automatically."""
    service = EDIService()
    result = service.process_edi_payload(SAMPLE_EDI_214_DAMAGED)

    assert result["status"] == "success"
    assert result["transaction_set"] == "214"
    assert isinstance(result["parse_result"], EDI214ParseResult)
    assert result["parse_result"].pro_number == "PRO-998877"
    assert result["parse_result"].is_damage_exception is True


def test_edi_service_process_auto_detect_210():
    """Verify EDIService routes EDI 210 payload automatically."""
    service = EDIService()
    result = service.process_edi_payload(SAMPLE_EDI_210)

    assert result["status"] == "success"
    assert result["transaction_set"] == "210"
    assert isinstance(result["parse_result"], EDI210ParseResult)
    assert result["parse_result"].invoice_number == "INV-889900"


def test_edi_service_process_auto_detect_204_and_211():
    """Verify EDIService routes EDI 204 and EDI 211 payloads automatically."""
    service = EDIService()
    res_204 = service.process_edi_payload(SAMPLE_EDI_204)
    assert res_204["status"] == "success"
    assert res_204["transaction_set"] == "204"
    assert isinstance(res_204["parse_result"], EDI204211ParseResult)
    assert res_204["parse_result"].shipment_reference == "LD-2026-9901"

    res_211 = service.process_edi_payload(SAMPLE_EDI_211)
    assert res_211["status"] == "success"
    assert res_211["transaction_set"] == "211"
    assert isinstance(res_211["parse_result"], EDI204211ParseResult)
    assert res_211["parse_result"].bol_number == "BOL-554433"


def test_edi_service_process_unsupported_st_raises():
    """Verify unsupported transaction set raises ValueError."""
    service = EDIService()
    with pytest.raises(ValueError, match="Unsupported or missing EDI transaction set"):
        service.process_edi_payload("ST*850*0001~\nBEG*00*SA*PO123~")


# ---------------------------------------------------------------------------
# 3. EDIService DB Integration Tests (Damage Exceptions, Carmack & DRAFT Claims)
# ---------------------------------------------------------------------------

def test_edi_service_214_damage_trigger_db_integration_draft_claim(test_db):
    """
    TDD Test: EDI 214 delivery damage exception (AG) with DB session must:
    1. Upsert shipment with external_reference, bol_number, delivery timestamp.
    2. Compute Carmack 9-month statutory deadline (relativedelta(months=9)).
    3. Auto-create claim in DRAFT status with is_approved_by_human=False.
    4. Write audit log for claim creation.
    """
    service = EDIService()
    response = service.process_edi_payload(SAMPLE_EDI_214_DAMAGED, db=test_db)

    assert response["status"] == "success"
    assert response["transaction_set"] == "214"
    assert response["claim_created"] is True
    assert response["shipment_id"] is not None
    assert response["claim_id"] is not None

    # Verify Shipment Record
    shipment = test_db.query(Shipment).filter(Shipment.id == response["shipment_id"]).first()
    assert shipment is not None
    assert shipment.external_reference == "PRO-998877"
    assert shipment.bol_number == "BOL-112233"
    assert shipment.delivery_at == datetime(2026, 8, 20, 14, 30)

    # Verify Auto-created Claim Record
    claim = test_db.query(Claim).filter(Claim.id == response["claim_id"]).first()
    assert claim is not None
    assert claim.shipment_id == shipment.id
    assert claim.status == "DRAFT"  # Mandatory DRAFT status
    assert claim.is_approved_by_human is False  # Guard intact

    # Verify Carmack 9-Month Deadline: 2026-08-20 + 9 months = 2027-05-20
    expected_carmack = datetime(2026, 8, 20, 14, 30) + relativedelta(months=9)
    assert claim.deadline_at == expected_carmack
    assert claim.deadline_at == datetime(2027, 5, 20, 14, 30)

    # Verify Audit Event
    audit = (
        test_db.query(AuditEvent)
        .filter(AuditEvent.entity_id == claim.id, AuditEvent.action == "CLAIM_AUTO_CREATED_FROM_EDI_214")
        .first()
    )
    assert audit is not None
    assert audit.actor_type == "SYSTEM"
    assert audit.actor_id == "EDI_SERVICE_214"


def test_edi_service_214_shortage_trigger_db_integration_draft_claim(test_db):
    """Verify EDI 214 shortage exception (SD) auto-creates claim in DRAFT status."""
    service = EDIService()
    response = service.process_edi_payload(SAMPLE_EDI_214_SHORTAGE, db=test_db)

    assert response["claim_created"] is True
    claim = test_db.query(Claim).filter(Claim.id == response["claim_id"]).first()
    assert claim.status == "DRAFT"
    assert claim.is_approved_by_human is False
    assert claim.claim_type in ("Shortage", "Cargo Damage")


def test_edi_service_214_clean_delivery_no_claim_created(test_db):
    """Verify normal completed delivery (D1) does NOT create a claim."""
    service = EDIService()
    response = service.process_edi_payload(SAMPLE_EDI_214_CLEAN, db=test_db)

    assert response["status"] == "success"
    assert response["claim_created"] is False
    assert response["claim_id"] is None
    assert response["shipment_id"] is not None

    shipment = test_db.query(Shipment).filter(Shipment.id == response["shipment_id"]).first()
    assert shipment.external_reference == "PRO-123456"
    assert shipment.delivery_at == datetime(2026, 8, 20, 10, 0)

    claims = test_db.query(Claim).filter(Claim.shipment_id == shipment.id).all()
    assert len(claims) == 0


def test_edi_service_214_duplicate_damage_idempotent(test_db):
    """Verify processing duplicate EDI 214 damage events is idempotent and does not duplicate claims."""
    service = EDIService()
    first_res = service.process_edi_payload(SAMPLE_EDI_214_DAMAGED, db=test_db)
    assert first_res["claim_created"] is True
    first_claim_id = first_res["claim_id"]

    second_res = service.process_edi_payload(SAMPLE_EDI_214_DAMAGED, db=test_db)
    assert second_res["claim_created"] is False
    assert second_res["claim_id"] == first_claim_id

    total_claims = test_db.query(Claim).filter(Claim.id == first_claim_id).count()
    assert total_claims == 1


def test_edi_service_204_db_integration_shipment_upsert(test_db):
    """Verify processing EDI 204 with DB session creates or updates Shipment details."""
    service = EDIService()
    response = service.process_edi_payload(SAMPLE_EDI_204, db=test_db)

    assert response["status"] == "success"
    assert response["transaction_set"] == "204"
    assert response["shipment_id"] is not None

    shipment = test_db.query(Shipment).filter(Shipment.id == response["shipment_id"]).first()
    assert shipment is not None
    assert shipment.external_reference == "LD-2026-9901"
    assert shipment.bol_number == "BOL-887766"
    assert shipment.shipper_name == "ACME LOGISTICS ORIGIN"
    assert shipment.consignee_name == "GLOBAL DISTRIBUTION DEST"
    assert shipment.origin == "CHICAGO, IL"
    assert shipment.destination == "DALLAS, TX"
    assert shipment.commodity == "INDUSTRIAL BEARINGS"
    assert shipment.quantity == 150
    assert shipment.weight == 18500.50
    assert shipment.declared_value == 45000.00
