import os
import sys
import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app
from db.session import Base, get_db
from scripts.seed_demo_data import seed_data
from app.models.domain_models import Shipment, Claim, Document, DocumentEvidence, ClaimFact, AuditEvent, Carrier
from app.integrations.tms.base import TMSAdapter, NormalizedShipmentData, NormalizedDocumentRef
from app.integrations.tms.mcleod_mock_adapter import McLeodMockAdapter
from app.services.tms_service import TMSAdapterFactory, TMSService, tms_service

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. TMSAdapterFactory Tests
# ---------------------------------------------------------------------------

def test_adapter_factory_returns_mcleod_adapter():
    factory = TMSAdapterFactory()
    adapter = factory.get_adapter("mcleod")
    assert isinstance(adapter, McLeodMockAdapter)

    # Test case-insensitivity
    adapter_upper = factory.get_adapter("MCLEOD")
    assert isinstance(adapter_upper, McLeodMockAdapter)

    adapter_mixed = factory.get_adapter("McLeod")
    assert isinstance(adapter_mixed, McLeodMockAdapter)


def test_adapter_factory_unsupported_provider():
    factory = TMSAdapterFactory()
    with pytest.raises(ValueError, match="Unsupported TMS provider"):
        factory.get_adapter("non_existent_tms")


def test_adapter_factory_custom_registration():
    class CustomDummyAdapter(TMSAdapter):
        def verify_webhook_signature(self, payload_bytes: bytes, headers: dict) -> bool:
            return True
        def parse_webhook_shipment(self, raw_payload: dict) -> NormalizedShipmentData:
            return NormalizedShipmentData(
                external_reference="TEST",
                bol_number="BOL-TEST",
                carrier_canonical_name="Test Carrier",
                shipper_name="Shipper",
                consignee_name="Consignee",
                origin="Origin",
                destination="Dest",
                declared_value=100.0,
                commodity="Test",
                quantity=1,
                weight=100.0,
                raw_status="OK"
            )
        def extract_document_references(self, raw_payload: dict):
            return []
        def is_claim_trigger_event(self, raw_payload: dict):
            return False, None
        async def fetch_document_bytes(self, doc_ref: NormalizedDocumentRef) -> bytes:
            return b""

    factory = TMSAdapterFactory()
    factory.register_adapter("custom_tms", CustomDummyAdapter)
    adapter = factory.get_adapter("custom_tms")
    assert isinstance(adapter, CustomDummyAdapter)


# ---------------------------------------------------------------------------
# 2. TMSService Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tms_service_signature_verification_failure():
    db = TestingSessionLocal()
    try:
        secret = "super_secret_webhook_key"
        service = TMSService()
        # Override adapter with secret
        service.adapter_factory.register_adapter("mcleod_secure", lambda: McLeodMockAdapter(webhook_secret=secret))
        
        payload = {"order_id": "ORD-999", "status": "DELIVERED_DAMAGED"}
        raw_bytes = json.dumps(payload).encode("utf-8")
        headers = {"x-mcleod-signature": "invalid_sig"}

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.process_webhook(
                provider="mcleod_secure",
                raw_payload=payload,
                headers=headers,
                payload_bytes=raw_bytes,
                db=db
            )
        assert exc_info.value.status_code == 401
    finally:
        db.close()


@pytest.mark.asyncio
async def test_tms_service_non_trigger_event_upserts_shipment_only():
    db = TestingSessionLocal()
    try:
        service = TMSService()
        payload = {
            "order_number": "MCL-10001",
            "bol_number": "BOL-MCL-10001",
            "pro_number": "PRO-MCL-10001",
            "carrier_name": "Swift Line Logistics",
            "shipper": "Alpha Manufacturing",
            "consignee": "Beta Warehouse",
            "origin": {"city": "Chicago", "state": "IL"},
            "destination": {"city": "Dallas", "state": "TX"},
            "pickup_at": "2026-08-01T08:00:00Z",
            "delivery_at": "2026-08-03T16:00:00Z",
            "declared_value": 15000.0,
            "commodity": "Industrial Pumps",
            "quantity": 4,
            "weight": 2400.0,
            "status": "DELIVERED_NORMAL"
        }

        result = await service.process_webhook(
            provider="mcleod",
            raw_payload=payload,
            headers={},
            db=db
        )

        assert result["status"] == "processed"
        assert result["claim_created"] is False
        assert result["claim_id"] is None
        assert result["shipment_id"] is not None

        # Verify DB state
        shipment = db.query(Shipment).filter(Shipment.external_reference == "MCL-10001").first()
        assert shipment is not None
        assert shipment.bol_number == "BOL-MCL-10001"
        assert shipment.declared_value == 15000.0
        assert shipment.shipper_name == "Alpha Manufacturing"

        # Verify NO claim exists
        claim = db.query(Claim).filter(Claim.shipment_id == shipment.id).first()
        assert claim is None
    finally:
        db.close()


@pytest.mark.asyncio
async def test_tms_service_claim_trigger_auto_creates_draft_claim():
    db = TestingSessionLocal()
    try:
        service = TMSService()
        payload = {
            "order_number": "MCL-DAMAGE-01",
            "bol_number": "BOL-MCL-DAMAGE-01",
            "carrier_name": "ABC Trucking",
            "shipper": "Apex Supply",
            "consignee": "Global Distribution",
            "origin": "Atlanta, GA",
            "destination": "Miami, FL",
            "delivery_at": "2026-08-10T12:00:00Z",
            "declared_value": 8500.0,
            "commodity": "Sensitive Medical Monitors",
            "quantity": 10,
            "weight": 1200.0,
            "status": "DELIVERED_DAMAGED"
        }

        result = await service.process_webhook(
            provider="mcleod",
            raw_payload=payload,
            headers={},
            db=db
        )

        assert result["status"] == "processed"
        assert result["claim_created"] is True
        assert result["claim_id"] is not None

        # Verify Claim in DB - strictly enforcing DRAFT status and NOT human approved!
        claim = db.query(Claim).filter(Claim.id == result["claim_id"]).first()
        assert claim is not None
        assert claim.status == "DRAFT"
        assert claim.is_approved_by_human is False
        assert claim.claimed_amount == 8500.0
        assert claim.human_threshold_triggered is True  # > $5000 threshold
        assert claim.deadline_at is not None  # Carmack 9 calendar month deadline computed

        # Check AuditEvent
        audit = db.query(AuditEvent).filter(
            AuditEvent.entity_type == "Claim",
            AuditEvent.entity_id == claim.id,
            AuditEvent.action == "CLAIM_AUTO_CREATED_FROM_TMS"
        ).first()
        assert audit is not None
    finally:
        db.close()


@pytest.mark.asyncio
async def test_tms_service_idempotency_claim_creation():
    db = TestingSessionLocal()
    try:
        service = TMSService()
        payload = {
            "order_number": "MCL-IDEMPOTENT-01",
            "bol_number": "BOL-IDEM-01",
            "carrier_name": "ABC Trucking",
            "declared_value": 3000.0,
            "status": "SHORTAGE_REPORTED"
        }

        # 1st Webhook Ingestion
        res1 = await service.process_webhook(provider="mcleod", raw_payload=payload, headers={}, db=db)
        assert res1["claim_created"] is True
        claim_id = res1["claim_id"]

        # 2nd Webhook Ingestion with same shipment
        res2 = await service.process_webhook(provider="mcleod", raw_payload=payload, headers={}, db=db)
        assert res2["claim_created"] is False
        assert res2["claim_id"] == claim_id

        # Ensure only 1 claim in DB
        claims = db.query(Claim).filter(Claim.shipment_id == res1["shipment_id"]).all()
        assert len(claims) == 1
    finally:
        db.close()


@pytest.mark.asyncio
async def test_tms_service_document_auto_ingestion_and_extraction():
    db = TestingSessionLocal()
    try:
        service = TMSService()
        payload = {
            "order_number": "MCL-DOCS-01",
            "bol_number": "BOL-DOCS-01",
            "carrier_name": "ABC Trucking",
            "declared_value": 4500.0,
            "status": "DELIVERED_DAMAGED",
            "documents": [
                {
                    "type": "BOL",
                    "filename": "bol_mcl_docs_01.pdf",
                    "url": "https://mcleod.mock.tms/docs/bol_mcl_docs_01.pdf",
                    "mime_type": "application/pdf"
                },
                {
                    "type": "POD",
                    "filename": "pod_mcl_docs_01.pdf",
                    "url": "https://mcleod.mock.tms/docs/pod_mcl_docs_01.pdf",
                    "mime_type": "application/pdf"
                }
            ]
        }

        result = await service.process_webhook(
            provider="mcleod",
            raw_payload=payload,
            headers={},
            db=db
        )

        assert result["claim_created"] is True
        claim_id = result["claim_id"]

        # Verify documents were ingested into DB
        docs = db.query(Document).filter(Document.claim_id == claim_id).all()
        assert len(docs) == 2
        doc_types = {d.document_type for d in docs}
        assert "BOL" in doc_types
        assert "POD" in doc_types

        # Verify extraction ran on ingested documents
        evidences = db.query(DocumentEvidence).join(Document).filter(Document.claim_id == claim_id).all()
        assert len(evidences) > 0

        facts = db.query(ClaimFact).filter(ClaimFact.claim_id == claim_id).all()
        assert len(facts) > 0
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Router HTTP API Endpoint Tests
# ---------------------------------------------------------------------------

def test_router_tms_webhook_endpoint_success():
    payload = {
        "order_number": "ROUTER-MCL-001",
        "bol_number": "BOL-ROUTER-001",
        "carrier_name": "ABC Trucking",
        "shipper": "Apex Logistics",
        "consignee": "Coastal Distributors",
        "declared_value": 12000.0,
        "status": "DELIVERED_DAMAGED",
        "documents": [
            {"type": "BOL", "filename": "bol_001.pdf"}
        ]
    }

    res = client.post("/api/integrations/tms/mcleod/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert data["claim_created"] is True
    assert data["claim_id"] is not None
    assert data["shipment_id"] is not None

    # Query DB to confirm claim is DRAFT and unapproved
    db = TestingSessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.id == data["claim_id"]).first()
        assert claim.status == "DRAFT"
        assert claim.is_approved_by_human is False
    finally:
        db.close()


def test_router_tms_webhook_endpoint_invalid_signature():
    # Configure webhook secret in adapter factory
    secret = "production_secret_key"
    tms_service.adapter_factory.register_adapter("mcleod_secured_endpoint", lambda: McLeodMockAdapter(webhook_secret=secret))

    payload = {"order_number": "SECURE-001", "status": "DELIVERED_DAMAGED"}
    raw_body = json.dumps(payload)

    # Missing signature or invalid signature
    res = client.post(
        "/api/integrations/tms/mcleod_secured_endpoint/webhook",
        content=raw_body,
        headers={"Content-Type": "application/json", "x-mcleod-signature": "wrong_signature"}
    )
    assert res.status_code == 401
    assert res.json()["error_code"] == "unauthorized"


def test_router_tms_webhook_endpoint_unsupported_provider():
    res = client.post("/api/integrations/tms/unknown_provider_xyz/webhook", json={"order_id": "123"})
    assert res.status_code == 400
    assert res.json()["error_code"] == "unsupported_provider"


def test_router_tms_webhook_endpoint_non_trigger():
    payload = {
        "order_number": "ROUTER-MCL-NORMAL",
        "bol_number": "BOL-ROUTER-NORMAL",
        "carrier_name": "ABC Trucking",
        "declared_value": 5000.0,
        "status": "DELIVERED_NORMAL"
    }

    res = client.post("/api/integrations/tms/mcleod/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert data["claim_created"] is False
    assert data["claim_id"] is None
