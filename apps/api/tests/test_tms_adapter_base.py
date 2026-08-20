import pytest
from pydantic import ValidationError
from app.integrations.tms.base import (
    NormalizedShipmentData,
    NormalizedDocumentRef,
    TMSAdapter,
)

def test_normalized_shipment_data_instantiation():
    """Verify that NormalizedShipmentData instantiates correctly with required and default fields."""
    shipment = NormalizedShipmentData(
        external_reference="EXT-1001",
        bol_number="BOL-987654",
        carrier_canonical_name="Old Dominion Freight Line",
        shipper_name="Acme Industrial Corp",
        consignee_name="Global Logistics LLC",
        origin="Chicago, IL",
        destination="Dallas, TX",
        declared_value=12500.50,
        commodity="Industrial Machine Parts",
        quantity=4,
        weight=3200.0,
        raw_status="DAMAGED_IN_TRANSIT",
    )

    assert shipment.external_reference == "EXT-1001"
    assert shipment.bol_number == "BOL-987654"
    assert shipment.pro_number is None
    assert shipment.carrier_canonical_name == "Old Dominion Freight Line"
    assert shipment.shipper_name == "Acme Industrial Corp"
    assert shipment.consignee_name == "Global Logistics LLC"
    assert shipment.origin == "Chicago, IL"
    assert shipment.destination == "Dallas, TX"
    assert shipment.pickup_at is None
    assert shipment.delivery_at is None
    assert shipment.declared_value == 12500.50
    assert shipment.currency == "USD"
    assert shipment.commodity == "Industrial Machine Parts"
    assert shipment.quantity == 4
    assert shipment.weight == 3200.0
    assert shipment.raw_status == "DAMAGED_IN_TRANSIT"


def test_normalized_shipment_data_with_optional_fields():
    """Verify NormalizedShipmentData with explicit optional values provided."""
    shipment = NormalizedShipmentData(
        external_reference="EXT-1002",
        bol_number="BOL-112233",
        pro_number="PRO-998877",
        carrier_canonical_name="Estes Express",
        shipper_name="Beta Manufacturing",
        consignee_name="Delta Distributing",
        origin="Atlanta, GA",
        destination="Miami, FL",
        pickup_at="2026-08-01T10:00:00Z",
        delivery_at="2026-08-03T14:30:00Z",
        declared_value=5000.0,
        currency="CAD",
        commodity="Electronic Components",
        quantity=10,
        weight=850.5,
        raw_status="DELIVERED_EXCEPTION",
    )

    assert shipment.pro_number == "PRO-998877"
    assert shipment.pickup_at == "2026-08-01T10:00:00Z"
    assert shipment.delivery_at == "2026-08-03T14:30:00Z"
    assert shipment.currency == "CAD"


def test_normalized_shipment_data_validation_errors():
    """Verify strict validation errors on missing required fields or invalid types."""
    with pytest.raises(ValidationError):
        # Missing required declared_value and commodity
        NormalizedShipmentData(
            external_reference="EXT-FAIL",
            bol_number="BOL-FAIL",
            carrier_canonical_name="Carrier",
            shipper_name="Shipper",
            consignee_name="Consignee",
            origin="Origin",
            destination="Dest",
            quantity=1,
            weight=100.0,
            raw_status="PENDING",
        )


def test_normalized_document_ref_instantiation():
    """Verify NormalizedDocumentRef creation and default mime_type."""
    doc = NormalizedDocumentRef(
        document_type="BOL",
        filename="bill_of_lading_987654.pdf",
        download_url="https://api.tms.example.com/docs/987654.pdf",
    )

    assert doc.document_type == "BOL"
    assert doc.filename == "bill_of_lading_987654.pdf"
    assert doc.download_url == "https://api.tms.example.com/docs/987654.pdf"
    assert doc.mime_type == "application/pdf"


def test_normalized_document_ref_custom_mime():
    """Verify NormalizedDocumentRef with custom mime type."""
    doc = NormalizedDocumentRef(
        document_type="PHOTO",
        filename="damage_evidence.png",
        download_url="https://api.tms.example.com/photos/1.png",
        mime_type="image/png",
    )
    assert doc.mime_type == "image/png"


def test_tms_adapter_cannot_be_instantiated_directly():
    """Verify TMSAdapter is an ABC that cannot be directly instantiated."""
    with pytest.raises(TypeError):
        TMSAdapter()


def test_incomplete_tms_adapter_subclass_fails():
    """Verify that a subclass omitting any abstract method fails to instantiate."""
    class IncompleteAdapter(TMSAdapter):
        def verify_webhook_signature(self, payload_bytes: bytes, headers: dict) -> bool:
            return True

    with pytest.raises(TypeError):
        IncompleteAdapter()


@pytest.mark.asyncio
async def test_concrete_tms_adapter_implementation():
    """Verify a complete concrete subclass of TMSAdapter behaves as expected."""
    class MockTMSAdapter(TMSAdapter):
        def verify_webhook_signature(self, payload_bytes: bytes, headers: dict) -> bool:
            return headers.get("X-Signature") == "valid-sig"

        def parse_webhook_shipment(self, raw_payload: dict) -> NormalizedShipmentData:
            return NormalizedShipmentData(
                external_reference=raw_payload["id"],
                bol_number=raw_payload["bol"],
                carrier_canonical_name=raw_payload["carrier"],
                shipper_name=raw_payload["shipper"],
                consignee_name=raw_payload["consignee"],
                origin=raw_payload["origin"],
                destination=raw_payload["destination"],
                declared_value=float(raw_payload["value"]),
                commodity=raw_payload["commodity"],
                quantity=int(raw_payload["qty"]),
                weight=float(raw_payload["weight"]),
                raw_status=raw_payload["status"],
            )

        def extract_document_references(self, raw_payload: dict) -> list[NormalizedDocumentRef]:
            docs = []
            for item in raw_payload.get("attachments", []):
                docs.append(
                    NormalizedDocumentRef(
                        document_type=item["type"],
                        filename=item["name"],
                        download_url=item["url"],
                    )
                )
            return docs

        def is_claim_trigger_event(self, raw_payload: dict) -> tuple[bool, str | None]:
            if raw_payload.get("status") == "DAMAGED":
                return True, "Shipment delivered with severe cargo damage"
            return False, None

        async def fetch_document_bytes(self, doc_ref: NormalizedDocumentRef) -> bytes:
            return b"%PDF-1.4 mock content for " + doc_ref.filename.encode("utf-8")

    adapter = MockTMSAdapter()

    # Test verify_webhook_signature
    assert adapter.verify_webhook_signature(b"{}", {"X-Signature": "valid-sig"}) is True
    assert adapter.verify_webhook_signature(b"{}", {"X-Signature": "invalid"}) is False

    # Test parse_webhook_shipment
    raw = {
        "id": "TMS-4455",
        "bol": "BOL-7788",
        "carrier": "TForce Freight",
        "shipper": "Alpha Corp",
        "consignee": "Omega Inc",
        "origin": "Denver, CO",
        "destination": "Seattle, WA",
        "value": 1500.0,
        "commodity": "Steel Pipes",
        "qty": 2,
        "weight": 1400.0,
        "status": "DAMAGED",
        "attachments": [
            {"type": "BOL", "name": "bol_7788.pdf", "url": "https://tms.test/bol"}
        ]
    }
    shipment = adapter.parse_webhook_shipment(raw)
    assert isinstance(shipment, NormalizedShipmentData)
    assert shipment.external_reference == "TMS-4455"
    assert shipment.declared_value == 1500.0

    # Test extract_document_references
    docs = adapter.extract_document_references(raw)
    assert len(docs) == 1
    assert isinstance(docs[0], NormalizedDocumentRef)
    assert docs[0].document_type == "BOL"

    # Test is_claim_trigger_event
    is_claim, reason = adapter.is_claim_trigger_event(raw)
    assert is_claim is True
    assert "cargo damage" in reason

    is_claim_norm, reason_norm = adapter.is_claim_trigger_event({"status": "IN_TRANSIT"})
    assert is_claim_norm is False
    assert reason_norm is None

    # Test async fetch_document_bytes
    content = await adapter.fetch_document_bytes(docs[0])
    assert b"%PDF-1.4 mock content for bol_7788.pdf" == content
