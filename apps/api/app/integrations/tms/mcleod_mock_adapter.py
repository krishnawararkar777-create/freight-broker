import hashlib
import hmac
from typing import Any, Dict, List, Optional, Tuple

from app.integrations.tms.base import (
    NormalizedDocumentRef,
    NormalizedShipmentData,
    TMSAdapter,
)


class McLeodMockAdapter(TMSAdapter):
    """Adapter for McLeod LoadMaster TMS JSON webhooks and API payloads.

    Supports HMAC SHA-256 signature verification, document metadata extraction,
    status normalization, and synthetic document retrieval.
    """

    CLAIM_TRIGGER_STATUSES = {
        "DELIVERED_DAMAGED",
        "SHORTAGE_REPORTED",
        "CLAIM_PENDING",
        "DAMAGED_IN_TRANSIT",
        "CARGO_LOSS",
        "EXCEPTION_DAMAGED",
        "CARGO_DAMAGE",
        "REFUSED_DAMAGED",
    }

    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret

    def verify_webhook_signature(self, payload_bytes: bytes, headers: Dict[str, Any]) -> bool:
        """Verify HMAC SHA-256 webhook signature against configured secret."""
        if not self.webhook_secret:
            # If no secret is configured, accept incoming webhook in mock/development mode
            return True

        normalized_headers = {k.lower(): v for k, v in headers.items()}
        signature_header = (
            normalized_headers.get("x-mcleod-signature")
            or normalized_headers.get("x-signature")
            or normalized_headers.get("authorization")
        )

        if not signature_header:
            return False

        # Strip optional prefixes like 'sha256=' or 'Bearer '
        clean_sig = str(signature_header).strip()
        if clean_sig.lower().startswith("sha256="):
            clean_sig = clean_sig[7:].strip()
        elif clean_sig.lower().startswith("bearer "):
            clean_sig = clean_sig[7:].strip()

        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(clean_sig.lower(), expected_sig.lower())

    def parse_webhook_shipment(self, raw_payload: Dict[str, Any]) -> NormalizedShipmentData:
        """Normalize McLeod LoadMaster JSON payload into standard NormalizedShipmentData."""
        # External Reference / Order ID
        ext_ref = (
            raw_payload.get("order_number")
            or raw_payload.get("order_id")
            or raw_payload.get("id")
            or raw_payload.get("external_reference")
            or "UNKNOWN_MCLEOD_ORDER"
        )

        # BOL and PRO numbers
        bol = (
            raw_payload.get("bol_number")
            or raw_payload.get("bol")
            or raw_payload.get("bill_of_lading")
            or str(ext_ref)
        )
        pro = (
            raw_payload.get("pro_number")
            or raw_payload.get("pro")
            or raw_payload.get("tracking_number")
        )

        # Carrier
        carrier = (
            raw_payload.get("carrier_name")
            or raw_payload.get("carrier")
            or raw_payload.get("carrier_canonical_name")
            or "Unknown Carrier"
        )

        # Shipper Name
        shipper_val = raw_payload.get("shipper") or raw_payload.get("shipper_name")
        if isinstance(shipper_val, dict):
            shipper_name = shipper_val.get("name") or "Unknown Shipper"
        elif shipper_val:
            shipper_name = str(shipper_val)
        else:
            shipper_name = "Unknown Shipper"

        # Consignee Name
        consignee_val = raw_payload.get("consignee") or raw_payload.get("consignee_name")
        if isinstance(consignee_val, dict):
            consignee_name = consignee_val.get("name") or "Unknown Consignee"
        elif consignee_val:
            consignee_name = str(consignee_val)
        else:
            consignee_name = "Unknown Consignee"

        # Origin
        origin_val = raw_payload.get("origin")
        if isinstance(origin_val, dict):
            origin = f"{origin_val.get('city', '')}, {origin_val.get('state', '')}".strip(" ,") or "Unknown Origin"
        elif origin_val:
            origin = str(origin_val)
        else:
            origin = "Unknown Origin"

        # Destination
        dest_val = raw_payload.get("destination")
        if isinstance(dest_val, dict):
            dest = f"{dest_val.get('city', '')}, {dest_val.get('state', '')}".strip(" ,") or "Unknown Destination"
        elif dest_val:
            dest = str(dest_val)
        else:
            dest = "Unknown Destination"

        # Timestamps
        pickup_at = (
            raw_payload.get("pickup_at")
            or raw_payload.get("pickup_date")
            or raw_payload.get("actual_pickup")
        )
        delivery_at = (
            raw_payload.get("delivery_at")
            or raw_payload.get("delivery_date")
            or raw_payload.get("actual_delivery")
        )

        # Monetary and commodity values
        declared_value_raw = (
            raw_payload.get("declared_value")
            or raw_payload.get("cargo_value")
            or raw_payload.get("value")
            or 0.0
        )
        declared_value = float(declared_value_raw)

        currency = raw_payload.get("currency") or "USD"
        commodity = (
            raw_payload.get("commodity")
            or raw_payload.get("commodity_description")
            or raw_payload.get("freight_description")
            or "General Freight"
        )

        # Quantity and weight
        qty_raw = (
            raw_payload.get("quantity")
            or raw_payload.get("pieces")
            or raw_payload.get("piece_count")
            or raw_payload.get("qty")
            or 1
        )
        quantity = int(qty_raw)

        weight_raw = (
            raw_payload.get("weight")
            or raw_payload.get("weight_lbs")
            or raw_payload.get("total_weight")
            or 0.0
        )
        weight = float(weight_raw)

        raw_status = str(
            raw_payload.get("status")
            or raw_payload.get("order_status")
            or raw_payload.get("raw_status")
            or "UNKNOWN"
        )

        return NormalizedShipmentData(
            external_reference=str(ext_ref),
            bol_number=str(bol),
            pro_number=str(pro) if pro else None,
            carrier_canonical_name=str(carrier),
            shipper_name=shipper_name,
            consignee_name=consignee_name,
            origin=origin,
            destination=dest,
            pickup_at=str(pickup_at) if pickup_at else None,
            delivery_at=str(delivery_at) if delivery_at else None,
            declared_value=declared_value,
            currency=currency,
            commodity=commodity,
            quantity=quantity,
            weight=weight,
            raw_status=raw_status,
        )

    def extract_document_references(self, raw_payload: Dict[str, Any]) -> List[NormalizedDocumentRef]:
        """Extract document references attached to the McLeod LoadMaster event."""
        docs_raw = (
            raw_payload.get("documents")
            or raw_payload.get("attachments")
            or raw_payload.get("document_list")
            or []
        )

        results: List[NormalizedDocumentRef] = []
        for doc in docs_raw:
            if not isinstance(doc, dict):
                continue

            doc_type = (
                doc.get("type")
                or doc.get("doc_type")
                or doc.get("document_type")
                or "OTHER"
            )
            filename = (
                doc.get("filename")
                or doc.get("name")
                or doc.get("file_name")
                or f"{doc_type.lower()}_{len(results) + 1}.pdf"
            )
            url = (
                doc.get("url")
                or doc.get("download_url")
                or doc.get("link")
                or f"https://mcleod.mock.tms/docs/{filename}"
            )
            mime_type = doc.get("mime_type") or doc.get("content_type") or "application/pdf"

            results.append(
                NormalizedDocumentRef(
                    document_type=str(doc_type).upper(),
                    filename=str(filename),
                    download_url=str(url),
                    mime_type=str(mime_type),
                )
            )

        return results

    def is_claim_trigger_event(self, raw_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Determine whether the McLeod event represents a claim trigger condition."""
        status = str(
            raw_payload.get("status")
            or raw_payload.get("order_status")
            or raw_payload.get("raw_status")
            or ""
        ).strip().upper()

        if status in self.CLAIM_TRIGGER_STATUSES:
            return True, f"McLeod trigger status detected: {status}"

        # Substring heuristics for potential variants
        trigger_keywords = ["DAMAG", "SHORTAG", "CLAIM", "LOSS", "REFUSED"]
        if any(keyword in status for keyword in trigger_keywords):
            return True, f"McLeod trigger keyword detected in status: {status}"

        return False, None

    async def fetch_document_bytes(self, doc_ref: NormalizedDocumentRef) -> bytes:
        """Asynchronously fetch mock binary contents for a given document reference."""
        # Generate synthetic PDF/binary content suitable for test extraction and ingestion
        content = (
            f"%PDF-1.4\n"
            f"% McLeod Mock Document System\n"
            f"BILL OF LADING\n"
            f"Carrier: ABC Trucking\n"
            f"BOL Number: {doc_ref.filename}\n"
            f"Type: {doc_ref.document_type}\n"
            f"Filename: {doc_ref.filename}\n"
            f"URL: {doc_ref.download_url}\n"
            f"MIME: {doc_ref.mime_type}\n"
            f"Declared Value: $10,000.00\n"
            f"1 0 obj << /Title ({doc_ref.filename}) /Creator (McLeod LoadMaster Mock) >> endobj\n"
            f"%%EOF\n"
        )
        return content.encode("utf-8")
