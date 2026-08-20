from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple, Any
from pydantic import BaseModel, ConfigDict, Field


class NormalizedShipmentData(BaseModel):
    """Normalized shipment representation extracted from external TMS webhooks or APIs."""

    model_config = ConfigDict(from_attributes=True)

    external_reference: str = Field(description="Unique identifier for the shipment in the TMS")
    bol_number: str = Field(description="Bill of Lading number")
    pro_number: Optional[str] = Field(default=None, description="Carrier PRO tracking number")
    carrier_canonical_name: str = Field(description="Standardized carrier name")
    shipper_name: str = Field(description="Shipper company or facility name")
    consignee_name: str = Field(description="Consignee company or facility destination name")
    origin: str = Field(description="Origin city, state or address")
    destination: str = Field(description="Destination city, state or address")
    pickup_at: Optional[str] = Field(default=None, description="Pickup timestamp or date string")
    delivery_at: Optional[str] = Field(default=None, description="Delivery timestamp or date string")
    declared_value: float = Field(description="Declared cargo monetary value")
    currency: str = Field(default="USD", description="Monetary currency code")
    commodity: str = Field(description="Description of commodity or cargo")
    quantity: int = Field(description="Total piece/handling unit quantity")
    weight: float = Field(description="Total shipment weight in lbs")
    raw_status: str = Field(description="Original status string reported by the TMS")


class NormalizedDocumentRef(BaseModel):
    """Normalized reference to a document available for retrieval from TMS."""

    model_config = ConfigDict(from_attributes=True)

    document_type: str = Field(description="Type of document (e.g. BOL, POD, COMMERCIAL_INVOICE, PHOTO)")
    filename: str = Field(description="Original or synthesized filename")
    download_url: str = Field(description="URL or endpoint to fetch document payload")
    mime_type: str = Field(default="application/pdf", description="MIME content type")


class TMSAdapter(ABC):
    """Abstract interface defining the contract for Transportation Management System (TMS) adapters."""

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, headers: Dict[str, Any]) -> bool:
        """Verify the cryptographic signature or authorization header of an incoming webhook."""
        pass

    @abstractmethod
    def parse_webhook_shipment(self, raw_payload: Dict[str, Any]) -> NormalizedShipmentData:
        """Normalize raw TMS shipment JSON payload into a standardized NormalizedShipmentData instance."""
        pass

    @abstractmethod
    def extract_document_references(self, raw_payload: Dict[str, Any]) -> List[NormalizedDocumentRef]:
        """Extract all document references (BOL, POD, photos, invoices) attached to the TMS event."""
        pass

    @abstractmethod
    def is_claim_trigger_event(self, raw_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Determine whether the incoming event represents a claim trigger (e.g., damage, shortage, loss).

        Returns:
            Tuple[bool, Optional[str]]: (is_trigger, reason_or_description)
        """
        pass

    @abstractmethod
    async def fetch_document_bytes(self, doc_ref: NormalizedDocumentRef) -> bytes:
        """Asynchronously fetch the binary contents of a document reference."""
        pass
