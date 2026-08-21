import os
import json
import uuid
import datetime
from typing import Dict, Any, Optional, Type, Union, Callable, List
from dateutil.parser import parse as parse_date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.domain_models import (
    Shipment,
    Claim,
    Document,
    Organization,
    CustomerPolicy,
    Carrier,
    AuditEvent,
)
from app.integrations.tms.base import (
    TMSAdapter,
    NormalizedShipmentData,
    NormalizedDocumentRef,
)
from app.integrations.tms.mcleod_mock_adapter import McLeodMockAdapter
from services.document_service import document_service, DuplicateDocumentException
from services.extraction_service import extraction_service
from services.carmack_engine import calculate_carmack_deadline, calculate_concealed_deadline


class TMSAdapterFactory:
    """Factory for managing and instantiating TMS adapter implementations."""

    def __init__(self):
        self._registry: Dict[str, Union[Type[TMSAdapter], Callable[[], TMSAdapter]]] = {
            "mcleod": McLeodMockAdapter,
            "mock": McLeodMockAdapter,
        }

    def register_adapter(
        self,
        provider: str,
        adapter_factory_or_cls: Union[Type[TMSAdapter], Callable[[], TMSAdapter]],
    ) -> None:
        """Register a new TMS adapter class or factory callable for a provider key."""
        self._registry[provider.lower().strip()] = adapter_factory_or_cls

    def get_adapter(self, provider: str, **kwargs) -> TMSAdapter:
        """Instantiate and return the registered TMSAdapter for a provider."""
        key = provider.lower().strip()
        if key not in self._registry:
            raise ValueError(f"Unsupported TMS provider: '{provider}'")

        target = self._registry[key]
        if callable(target):
            try:
                return target(**kwargs)
            except TypeError:
                return target()
        return target


class TMSService:
    """Universal service for processing inbound TMS webhooks, managing shipment upserts,
    enforcing human-in-the-loop claim auto-creation (in DRAFT status), and auto-ingesting documents.
    """

    def __init__(self, adapter_factory: Optional[TMSAdapterFactory] = None):
        self.adapter_factory = adapter_factory or TMSAdapterFactory()

    def _parse_datetime(self, val: Optional[str]) -> Optional[datetime.datetime]:
        """Safely parse various datetime string formats into UTC-aware datetime."""
        if not val:
            return None
        if isinstance(val, datetime.datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=datetime.timezone.utc)
            return val
        try:
            dt = parse_date(str(val))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except Exception:
            return None

    async def process_webhook(
        self,
        provider: str,
        raw_payload: Dict[str, Any],
        headers: Dict[str, Any],
        payload_bytes: Optional[bytes] = None,
        db: Optional[Session] = None,
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process an inbound TMS webhook event:
        1. Resolve adapter and verify webhook cryptographic signature.
        2. Normalize payload and upsert into shipments table.
        3. Evaluate claim trigger events: auto-create claim in DRAFT status with is_approved_by_human=False.
        4. Auto-fetch attached documents, stream to document/storage service, and trigger extraction.
        """
        if db is None:
            raise ValueError("A valid database Session is required to process TMS webhooks.")

        # 1. Resolve Adapter
        try:
            adapter = self.adapter_factory.get_adapter(provider)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": "unsupported_provider", "message": str(exc)},
            )

        # 2. Verify Signature
        if payload_bytes is None:
            payload_bytes = json.dumps(raw_payload).encode("utf-8")

        if not adapter.verify_webhook_signature(payload_bytes, headers):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "unauthorized", "message": "Invalid TMS webhook signature"},
            )

        # 3. Parse Normalized Shipment
        shipment_data: NormalizedShipmentData = adapter.parse_webhook_shipment(raw_payload)

        # 4. Resolve Organization
        if not org_id:
            org = db.query(Organization).first()
            if org:
                org_id = org.id
            else:
                org = Organization(
                    id="org-apex",
                    name="Apex Freight Brokers",
                    type="broker",
                    status="active",
                )
                db.add(org)
                db.flush()
                org_id = org.id

        # 5. Resolve / Create Carrier
        carrier = (
            db.query(Carrier)
            .filter(Carrier.canonical_name == shipment_data.carrier_canonical_name)
            .first()
        )
        if not carrier:
            carrier = Carrier(
                id=f"car-{uuid.uuid4().hex[:8]}",
                canonical_name=shipment_data.carrier_canonical_name,
                active=True,
            )
            db.add(carrier)
            db.flush()

        # 6. Upsert Shipment
        shipment = (
            db.query(Shipment)
            .filter(
                Shipment.organization_id == org_id,
                (Shipment.external_reference == shipment_data.external_reference)
                | (Shipment.bol_number == shipment_data.bol_number),
            )
            .first()
        )

        pickup_dt = self._parse_datetime(shipment_data.pickup_at)
        delivery_dt = self._parse_datetime(shipment_data.delivery_at)

        if shipment:
            shipment.carrier_id = carrier.id
            shipment.shipper_name = shipment_data.shipper_name
            shipment.consignee_name = shipment_data.consignee_name
            shipment.origin = shipment_data.origin
            shipment.destination = shipment_data.destination
            if pickup_dt:
                shipment.pickup_at = pickup_dt
            if delivery_dt:
                shipment.delivery_at = delivery_dt
            shipment.declared_value = shipment_data.declared_value
            shipment.currency = shipment_data.currency
            shipment.commodity = shipment_data.commodity
            shipment.quantity = shipment_data.quantity
            shipment.weight = shipment_data.weight
        else:
            shipment = Shipment(
                id=f"shp-{uuid.uuid4().hex[:12]}",
                organization_id=org_id,
                external_reference=shipment_data.external_reference,
                bol_number=shipment_data.bol_number,
                carrier_id=carrier.id,
                shipper_name=shipment_data.shipper_name,
                consignee_name=shipment_data.consignee_name,
                origin=shipment_data.origin,
                destination=shipment_data.destination,
                pickup_at=pickup_dt,
                delivery_at=delivery_dt,
                declared_value=shipment_data.declared_value,
                currency=shipment_data.currency,
                commodity=shipment_data.commodity,
                quantity=shipment_data.quantity,
                weight=shipment_data.weight,
            )
            db.add(shipment)
            db.flush()

        # Record Audit Event for Shipment Ingestion
        db.add(
            AuditEvent(
                id=f"aud-{uuid.uuid4().hex[:12]}",
                organization_id=org_id,
                actor_type="SYSTEM",
                actor_id=f"TMS_WEBHOOK_{provider.upper()}",
                entity_type="Shipment",
                entity_id=shipment.id,
                action="SHIPMENT_INGESTED_FROM_TMS",
                after_json={
                    "external_reference": shipment.external_reference,
                    "bol_number": shipment.bol_number,
                    "raw_status": shipment_data.raw_status,
                },
            )
        )

        # 7. Evaluate Claim Trigger Conditions
        is_trigger, trigger_reason = adapter.is_claim_trigger_event(raw_payload)
        claim = db.query(Claim).filter(Claim.shipment_id == shipment.id).first()
        claim_created = False

        if is_trigger and not claim:
            # Policy threshold evaluation
            policy = (
                db.query(CustomerPolicy)
                .filter(CustomerPolicy.organization_id == org_id)
                .first()
            )
            high_val_threshold = policy.high_value_threshold if policy else 5000.0
            is_high_value = bool(
                shipment.declared_value and shipment.declared_value >= high_val_threshold
            )

            # Compute Carmack statutory filing deadlines (9 calendar months, 5 business days)
            deadline_at = None
            concealed_deadline_at = None
            base_date = delivery_dt.date() if delivery_dt else datetime.date.today()
            try:
                carmack_d = calculate_carmack_deadline(base_date)
                deadline_at = datetime.datetime.combine(
                    carmack_d, datetime.time(23, 59, 59, tzinfo=datetime.timezone.utc)
                )
                concealed_d = calculate_concealed_deadline(base_date)
                concealed_deadline_at = datetime.datetime.combine(
                    concealed_d, datetime.time(23, 59, 59, tzinfo=datetime.timezone.utc)
                )
            except Exception:
                pass

            claim = Claim(
                id=f"clm-{uuid.uuid4().hex[:12]}",
                organization_id=org_id,
                shipment_id=shipment.id,
                claim_type="Cargo Damage",
                status="DRAFT",  # Strictly DRAFT - never auto-approved/submitted
                claimed_amount=shipment.declared_value or 0.0,
                currency=shipment.currency or "USD",
                deadline_at=deadline_at,
                concealed_deadline_at=concealed_deadline_at,
                human_threshold_triggered=is_high_value,
                elevated_approval_acknowledged=False,
                is_approved_by_human=False,  # Human approval guard intact
            )
            db.add(claim)
            db.flush()
            claim_created = True

            # Write Audit Event for Claim Auto-Creation
            db.add(
                AuditEvent(
                    id=f"aud-{uuid.uuid4().hex[:12]}",
                    organization_id=org_id,
                    actor_type="SYSTEM",
                    actor_id=f"TMS_WEBHOOK_{provider.upper()}",
                    entity_type="Claim",
                    entity_id=claim.id,
                    action="CLAIM_AUTO_CREATED_FROM_TMS",
                    after_json={
                        "shipment_id": shipment.id,
                        "status": "DRAFT",
                        "claimed_amount": claim.claimed_amount,
                        "trigger_reason": trigger_reason,
                    },
                )
            )

        # 8. Auto-Fetch Attached Documents & Extract Facts
        doc_refs: List[NormalizedDocumentRef] = adapter.extract_document_references(raw_payload)
        ingested_count = 0

        if claim and doc_refs:
            for doc_ref in doc_refs:
                try:
                    doc_bytes = await adapter.fetch_document_bytes(doc_ref)
                    if not doc_bytes:
                        continue

                    # Ingest via DocumentService
                    try:
                        doc = document_service.ingest_document(
                            db=db,
                            claim_id=claim.id,
                            file_bytes=doc_bytes,
                            filename=doc_ref.filename,
                            mime_type=doc_ref.mime_type,
                            document_type=doc_ref.document_type,
                            uploaded_by=None,
                        )
                    except DuplicateDocumentException as dup_exc:
                        doc = (
                            db.query(Document)
                            .filter(Document.id == dup_exc.existing_document_id)
                            .first()
                        )

                    # Trigger extraction pipeline
                    if doc:
                        try:
                            extraction_service.extract_and_persist(
                                db=db,
                                claim_id=claim.id,
                                document_id=doc.id,
                                file_bytes=doc_bytes,
                            )
                        except Exception:
                            pass
                        ingested_count += 1
                except Exception:
                    pass

        db.commit()

        return {
            "status": "processed",
            "shipment_id": shipment.id,
            "claim_id": claim.id if claim else None,
            "claim_created": claim_created,
            "documents_ingested": ingested_count,
        }


tms_service = TMSService()
