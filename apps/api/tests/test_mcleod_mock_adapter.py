import hmac
import hashlib
import json
import pytest
from app.integrations.tms.base import (
    NormalizedDocumentRef,
    NormalizedShipmentData,
    TMSAdapter,
)
from app.integrations.tms.mcleod_mock_adapter import McLeodMockAdapter


@pytest.fixture
def sample_mcleod_payload():
    return {
        "order_number": "MCL-998821",
        "bol_number": "BOL-MCLEOD-501",
        "pro_number": "PRO-884920",
        "carrier_name": "Knight-Swift Transportation",
        "shipper": {
            "name": "Midwest Distribution Hub",
            "address": "100 Warehouse Way",
            "city": "Chicago",
            "state": "IL",
            "zip": "60601",
        },
        "consignee": {
            "name": "Apex Retail Center",
            "address": "500 Commerce Blvd",
            "city": "Dallas",
            "state": "TX",
            "zip": "75201",
        },
        "origin": "Chicago, IL",
        "destination": "Dallas, TX",
        "pickup_at": "2026-08-15T08:30:00Z",
        "delivery_at": "2026-08-18T14:15:00Z",
        "declared_value": 45000.00,
        "currency": "USD",
        "commodity": "Commercial HVAC Units",
        "quantity": 6,
        "weight": 8400.5,
        "status": "DELIVERED_DAMAGED",
        "documents": [
            {
                "type": "BOL",
                "filename": "mcleod_bol_501.pdf",
                "url": "https://mcleod.mock.tms/api/v1/orders/MCL-998821/docs/bol_501.pdf",
                "mime_type": "application/pdf",
            },
            {
                "type": "POD",
                "filename": "mcleod_pod_signed.pdf",
                "url": "https://mcleod.mock.tms/api/v1/orders/MCL-998821/docs/pod_signed.pdf",
                "mime_type": "application/pdf",
            },
            {
                "type": "PHOTO",
                "filename": "cargo_damage_1.jpg",
                "url": "https://mcleod.mock.tms/api/v1/orders/MCL-998821/docs/cargo_damage_1.jpg",
                "mime_type": "image/jpeg",
            },
        ],
    }


def test_mcleod_adapter_inherits_tms_adapter():
    """Verify that McLeodMockAdapter is a subclass of TMSAdapter."""
    adapter = McLeodMockAdapter()
    assert isinstance(adapter, TMSAdapter)


def test_mcleod_signature_verification_with_secret():
    """Verify HMAC SHA-256 signature verification when a secret is configured."""
    secret = "super_mcleod_webhook_secret_key"
    adapter = McLeodMockAdapter(webhook_secret=secret)

    payload_data = {"event": "shipment.updated", "order_number": "MCL-1234"}
    payload_bytes = json.dumps(payload_data).encode("utf-8")

    # Compute valid signature
    valid_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    # Valid signature in X-McLeod-Signature header
    assert adapter.verify_webhook_signature(payload_bytes, {"X-McLeod-Signature": valid_sig}) is True
    # Case-insensitive header check
    assert adapter.verify_webhook_signature(payload_bytes, {"x-mcleod-signature": valid_sig}) is True
    # Support X-Signature header as fallback
    assert adapter.verify_webhook_signature(payload_bytes, {"X-Signature": valid_sig}) is True
    # Support 'sha256=' prefix in signature header
    assert adapter.verify_webhook_signature(payload_bytes, {"X-McLeod-Signature": f"sha256={valid_sig}"}) is True

    # Invalid signature
    assert adapter.verify_webhook_signature(payload_bytes, {"X-McLeod-Signature": "invalid_signature_hex"}) is False
    # Missing header
    assert adapter.verify_webhook_signature(payload_bytes, {}) is False


def test_mcleod_signature_verification_without_secret():
    """Verify that when no secret is configured, signature verification passes by default."""
    adapter = McLeodMockAdapter(webhook_secret=None)
    payload_bytes = b'{"event": "test"}'
    assert adapter.verify_webhook_signature(payload_bytes, {}) is True


def test_mcleod_parse_webhook_shipment(sample_mcleod_payload):
    """Verify parsing of standard McLeod LoadMaster webhook shipment JSON."""
    adapter = McLeodMockAdapter()
    normalized = adapter.parse_webhook_shipment(sample_mcleod_payload)

    assert isinstance(normalized, NormalizedShipmentData)
    assert normalized.external_reference == "MCL-998821"
    assert normalized.bol_number == "BOL-MCLEOD-501"
    assert normalized.pro_number == "PRO-884920"
    assert normalized.carrier_canonical_name == "Knight-Swift Transportation"
    assert normalized.shipper_name == "Midwest Distribution Hub"
    assert normalized.consignee_name == "Apex Retail Center"
    assert normalized.origin == "Chicago, IL"
    assert normalized.destination == "Dallas, TX"
    assert normalized.pickup_at == "2026-08-15T08:30:00Z"
    assert normalized.delivery_at == "2026-08-18T14:15:00Z"
    assert normalized.declared_value == 45000.00
    assert normalized.currency == "USD"
    assert normalized.commodity == "Commercial HVAC Units"
    assert normalized.quantity == 6
    assert normalized.weight == 8400.5
    assert normalized.raw_status == "DELIVERED_DAMAGED"


def test_mcleod_parse_webhook_shipment_string_shipper_consignee_and_nested_locations():
    """Verify parsing when shipper/consignee are simple strings and origin/dest are nested dicts."""
    adapter = McLeodMockAdapter()
    payload = {
        "id": "ORD-5544",
        "bol": "BOL-5544-B",
        "carrier": "Old Dominion Freight Line",
        "shipper_name": "Simple Shipper Inc",
        "consignee_name": "Simple Consignee Co",
        "origin": {"city": "Atlanta", "state": "GA"},
        "destination": {"city": "Miami", "state": "FL"},
        "cargo_value": "12000.75",
        "pieces": 2,
        "weight_lbs": 1500,
        "status": "SHORTAGE_REPORTED",
    }
    normalized = adapter.parse_webhook_shipment(payload)

    assert normalized.external_reference == "ORD-5544"
    assert normalized.bol_number == "BOL-5544-B"
    assert normalized.carrier_canonical_name == "Old Dominion Freight Line"
    assert normalized.shipper_name == "Simple Shipper Inc"
    assert normalized.consignee_name == "Simple Consignee Co"
    assert normalized.origin == "Atlanta, GA"
    assert normalized.destination == "Miami, FL"
    assert normalized.declared_value == 12000.75
    assert normalized.quantity == 2
    assert normalized.weight == 1500.0
    assert normalized.raw_status == "SHORTAGE_REPORTED"


def test_mcleod_is_claim_trigger_event():
    """Verify claim trigger event detection based on status codes."""
    adapter = McLeodMockAdapter()

    # Trigger events
    trigger_statuses = [
        "DELIVERED_DAMAGED",
        "delivered_damaged",
        "SHORTAGE_REPORTED",
        "shortage_reported",
        "CLAIM_PENDING",
        "claim_pending",
        "DAMAGED_IN_TRANSIT",
        "CARGO_LOSS",
    ]

    for status in trigger_statuses:
        is_trigger, reason = adapter.is_claim_trigger_event({"status": status, "order_number": "MCL-1"})
        assert is_trigger is True, f"Status {status} should trigger a claim"
        assert reason is not None
        assert status.upper() in reason or "claim" in reason.lower() or "damage" in reason.lower()

    # Non-trigger events
    non_trigger_statuses = [
        "DELIVERED",
        "IN_TRANSIT",
        "DISPATCHED",
        "PENDING",
        "LOADED",
        "COMPLETED",
    ]

    for status in non_trigger_statuses:
        is_trigger, reason = adapter.is_claim_trigger_event({"status": status, "order_number": "MCL-2"})
        assert is_trigger is False, f"Status {status} should NOT trigger a claim"
        assert reason is None


def test_mcleod_extract_document_references(sample_mcleod_payload):
    """Verify extraction of document references from payload."""
    adapter = McLeodMockAdapter()
    docs = adapter.extract_document_references(sample_mcleod_payload)

    assert len(docs) == 3
    assert all(isinstance(doc, NormalizedDocumentRef) for doc in docs)

    bol_doc = docs[0]
    assert bol_doc.document_type == "BOL"
    assert bol_doc.filename == "mcleod_bol_501.pdf"
    assert "bol_501.pdf" in bol_doc.download_url
    assert bol_doc.mime_type == "application/pdf"

    photo_doc = docs[2]
    assert photo_doc.document_type == "PHOTO"
    assert photo_doc.mime_type == "image/jpeg"


def test_mcleod_extract_document_references_empty():
    """Verify extraction handles missing or empty document lists gracefully."""
    adapter = McLeodMockAdapter()
    docs = adapter.extract_document_references({"order_number": "MCL-EMPTY"})
    assert docs == []


@pytest.mark.asyncio
async def test_mcleod_fetch_document_bytes():
    """Verify mock binary document retrieval returning synthetic document bytes."""
    adapter = McLeodMockAdapter()
    doc_ref = NormalizedDocumentRef(
        document_type="BOL",
        filename="bol_mcleod_test.pdf",
        download_url="https://mcleod.mock.tms/api/v1/orders/MCL-998821/docs/bol_test.pdf",
        mime_type="application/pdf",
    )

    content = await adapter.fetch_document_bytes(doc_ref)
    assert isinstance(content, bytes)
    assert len(content) > 0
    assert content.startswith(b"%PDF")
    assert b"bol_mcleod_test.pdf" in content or b"McLeod" in content
