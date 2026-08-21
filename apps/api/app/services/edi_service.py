"""
Unified EDI Service for processing inbound X12 EDI transaction payloads.
Auto-detects transaction types (214, 210, 204, 211) from the ST segment, routes to specialized
parsers, upserts shipment state, and automates Carmack 9-month statutory deadline calculations
and DRAFT claim generation with strict human-in-the-loop approval guards.
"""
import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Shipment,
    Claim,
    Organization,
    Carrier,
    AuditEvent,
)
from app.parsers.edi.x12_segment_parser import tokenize_x12, find_first_segment
from app.parsers.edi.edi_214_parser import parse_edi_214, EDI214ParseResult
from app.parsers.edi.edi_210_parser import parse_edi_210, EDI210ParseResult
from app.parsers.edi.edi_204_211_parser import parse_edi_204_211, EDI204211ParseResult


class EDIService:
    """Unified service for ingesting and processing EDI transaction payloads."""

    def process_edi_payload(
        self,
        raw_content: str,
        db: Optional[Session] = None,
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process an inbound raw EDI X12 transaction payload:
        1. Inspects ST header segment to auto-detect transaction set (214, 210, 204, 211).
        2. Routes to corresponding specialized EDI parser.
        3. When a database session is provided:
           - Ingests / upserts Shipment record.
           - On EDI 214 damage exception (AG, SD, CD, A7), computes statutory Carmack filing deadline
             (9 calendar months) and auto-creates a Claim strictly in DRAFT status (is_approved_by_human=False).
           - Records immutable audit trail events.
        """
        if not raw_content or not raw_content.strip():
            raise ValueError("EDI payload is empty")

        segments = tokenize_x12(raw_content)
        if not segments:
            raise ValueError("Failed to parse any segments from EDI payload")

        st_seg = find_first_segment(segments, "ST")
        if not st_seg or not st_seg.get(1):
            raise ValueError("Unsupported or missing EDI transaction set in payload (no ST segment found)")

        transaction_set = st_seg.get(1).strip()
        if transaction_set not in ("214", "210", "204", "211"):
            raise ValueError(f"Unsupported or missing EDI transaction set in ST segment: '{transaction_set}'")

        # Route to specialized parser
        parse_result: Any
        if transaction_set == "214":
            parse_result = parse_edi_214(raw_content)
        elif transaction_set == "210":
            parse_result = parse_edi_210(raw_content)
        elif transaction_set in ("204", "211"):
            parse_result = parse_edi_204_211(raw_content)
        else:
            raise ValueError(f"No parser available for transaction set '{transaction_set}'")

        response: Dict[str, Any] = {
            "status": "success",
            "transaction_set": transaction_set,
            "parse_result": parse_result,
            "shipment_id": None,
            "claim_id": None,
            "claim_created": False,
        }

        # If database session is not provided, return parsed payload directly
        if db is None:
            return response

        # Resolve Organization
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

        # -----------------------------------------------------------------------
        # Process EDI 214 (Carrier Shipment Status)
        # -----------------------------------------------------------------------
        if transaction_set == "214":
            res_214: EDI214ParseResult = parse_result
            carrier_name = res_214.carrier_scac or "CARRIER"
            carrier = (
                db.query(Carrier)
                .filter(Carrier.canonical_name == carrier_name)
                .first()
            )
            if not carrier:
                carrier = Carrier(
                    id=f"car-{uuid.uuid4().hex[:8]}",
                    canonical_name=carrier_name,
                    active=True,
                )
                db.add(carrier)
                db.flush()

            # Upsert Shipment
            from sqlalchemy import or_
            conds_214 = [Shipment.external_reference == res_214.pro_number]
            if res_214.bol_number:
                conds_214.append(Shipment.bol_number == res_214.bol_number)

            shipment = (
                db.query(Shipment)
                .filter(
                    Shipment.organization_id == org_id,
                    or_(*conds_214)
                )
                .first()
            )

            if shipment:
                shipment.delivery_at = res_214.delivery_at
                if res_214.bol_number and not shipment.bol_number:
                    shipment.bol_number = res_214.bol_number
            else:
                shipment = Shipment(
                    id=f"shp-{uuid.uuid4().hex[:12]}",
                    organization_id=org_id,
                    external_reference=res_214.pro_number,
                    bol_number=res_214.bol_number or res_214.pro_number,
                    carrier_id=carrier.id,
                    delivery_at=res_214.delivery_at,
                )
                db.add(shipment)
                db.flush()

            response["shipment_id"] = shipment.id

            # Evaluate damage exception trigger
            if res_214.is_damage_exception:
                existing_claim = (
                    db.query(Claim)
                    .filter(Claim.shipment_id == shipment.id)
                    .first()
                )
                if existing_claim:
                    response["claim_id"] = existing_claim.id
                    response["claim_created"] = False
                else:
                    carmack_deadline = res_214.carmack_deadline_at
                    concealed_deadline = res_214.concealed_deadline_at
                    claim_type = "Shortage" if res_214.status_code == "SD" else "Cargo Damage"
                    declared_val = shipment.declared_value or 0.0
                    is_high_value = bool(declared_val >= 5000.0)

                    new_claim = Claim(
                        id=f"clm-{uuid.uuid4().hex[:12]}",
                        organization_id=org_id,
                        shipment_id=shipment.id,
                        claim_type=claim_type,
                        status="DRAFT",  # Strictly DRAFT - never auto-approved/submitted
                        claimed_amount=declared_val,
                        currency=shipment.currency or "USD",
                        deadline_at=carmack_deadline,
                        concealed_deadline_at=concealed_deadline,
                        human_threshold_triggered=is_high_value,
                        elevated_approval_acknowledged=False,
                        is_approved_by_human=False,  # Human approval guard intact
                    )
                    db.add(new_claim)
                    db.flush()

                    # Record Audit Event
                    db.add(
                        AuditEvent(
                            id=f"aud-{uuid.uuid4().hex[:12]}",
                            organization_id=org_id,
                            actor_type="SYSTEM",
                            actor_id="EDI_SERVICE_214",
                            entity_type="Claim",
                            entity_id=new_claim.id,
                            action="CLAIM_AUTO_CREATED_FROM_EDI_214",
                            after_json={
                                "shipment_id": shipment.id,
                                "status": "DRAFT",
                                "status_code": res_214.status_code,
                                "carmack_deadline_at": carmack_deadline.isoformat(),
                                "concealed_deadline_at": concealed_deadline.isoformat(),
                            },
                        )
                    )
                    db.flush()
                    response["claim_id"] = new_claim.id
                    response["claim_created"] = True

        # -----------------------------------------------------------------------
        # Process EDI 204 & EDI 211 (Load Tender & Bill of Lading)
        # -----------------------------------------------------------------------
        elif transaction_set in ("204", "211"):
            res_load: EDI204211ParseResult = parse_result
            carrier = (
                db.query(Carrier)
                .filter(Carrier.canonical_name == "CARRIER")
                .first()
            )
            if not carrier:
                carrier = Carrier(
                    id=f"car-{uuid.uuid4().hex[:8]}",
                    canonical_name="CARRIER",
                    active=True,
                )
                db.add(carrier)
                db.flush()

            shipment = (
                db.query(Shipment)
                .filter(
                    Shipment.organization_id == org_id,
                    (
                        (Shipment.external_reference == res_load.shipment_reference)
                        | (
                            (Shipment.bol_number == res_load.bol_number)
                            if res_load.bol_number
                            else False
                        )
                    ),
                )
                .first()
            )

            if shipment:
                if res_load.bol_number:
                    shipment.bol_number = res_load.bol_number
                if res_load.shipper_name:
                    shipment.shipper_name = res_load.shipper_name
                if res_load.consignee_name:
                    shipment.consignee_name = res_load.consignee_name
                if res_load.origin_city_state:
                    shipment.origin = res_load.origin_city_state
                if res_load.destination_city_state:
                    shipment.destination = res_load.destination_city_state
                if res_load.commodity:
                    shipment.commodity = res_load.commodity
                if res_load.weight:
                    shipment.weight = res_load.weight
                if res_load.total_pieces:
                    shipment.quantity = res_load.total_pieces
                if res_load.declared_value:
                    shipment.declared_value = res_load.declared_value
            else:
                shipment = Shipment(
                    id=f"shp-{uuid.uuid4().hex[:12]}",
                    organization_id=org_id,
                    external_reference=res_load.shipment_reference,
                    bol_number=res_load.bol_number or res_load.shipment_reference,
                    carrier_id=carrier.id,
                    shipper_name=res_load.shipper_name,
                    consignee_name=res_load.consignee_name,
                    origin=res_load.origin_city_state,
                    destination=res_load.destination_city_state,
                    commodity=res_load.commodity,
                    weight=res_load.weight,
                    quantity=res_load.total_pieces,
                    declared_value=res_load.declared_value,
                )
                db.add(shipment)
                db.flush()

            # Record Audit Event
            db.add(
                AuditEvent(
                    id=f"aud-{uuid.uuid4().hex[:12]}",
                    organization_id=org_id,
                    actor_type="SYSTEM",
                    actor_id=f"EDI_SERVICE_{transaction_set}",
                    entity_type="Shipment",
                    entity_id=shipment.id,
                    action=f"SHIPMENT_INGESTED_FROM_EDI_{transaction_set}",
                    after_json={
                        "shipment_reference": res_load.shipment_reference,
                        "bol_number": res_load.bol_number,
                        "weight": res_load.weight,
                        "quantity": res_load.total_pieces,
                        "declared_value": res_load.declared_value,
                    },
                )
            )
            db.flush()
            response["shipment_id"] = shipment.id

        # -----------------------------------------------------------------------
        # Process EDI 210 (Freight Invoice)
        # -----------------------------------------------------------------------
        elif transaction_set == "210":
            res_210: EDI210ParseResult = parse_result
            shipment = None
            if res_210.pro_number or res_210.bol_number:
                from sqlalchemy import or_
                conds_210 = []
                if res_210.pro_number:
                    conds_210.append(Shipment.external_reference == res_210.pro_number)
                if res_210.bol_number:
                    conds_210.append(Shipment.bol_number == res_210.bol_number)

                if conds_210:
                    shipment = (
                        db.query(Shipment)
                        .filter(
                            Shipment.organization_id == org_id,
                            or_(*conds_210)
                        )
                        .first()
                    )

            if shipment:
                if res_210.shipper_name and not shipment.shipper_name:
                    shipment.shipper_name = res_210.shipper_name
                if res_210.consignee_name and not shipment.consignee_name:
                    shipment.consignee_name = res_210.consignee_name
                if res_210.weight and not shipment.weight:
                    shipment.weight = res_210.weight
                if res_210.total_pieces and not shipment.quantity:
                    shipment.quantity = res_210.total_pieces
                response["shipment_id"] = shipment.id

            db.add(
                AuditEvent(
                    id=f"aud-{uuid.uuid4().hex[:12]}",
                    organization_id=org_id,
                    actor_type="SYSTEM",
                    actor_id="EDI_SERVICE_210",
                    entity_type="Invoice",
                    entity_id=res_210.invoice_number,
                    action="INVOICE_INGESTED_FROM_EDI_210",
                    after_json={
                        "invoice_number": res_210.invoice_number,
                        "invoice_total": res_210.invoice_total,
                        "bol_number": res_210.bol_number,
                        "pro_number": res_210.pro_number,
                    },
                )
            )
            db.flush()

        return response


edi_service = EDIService()
