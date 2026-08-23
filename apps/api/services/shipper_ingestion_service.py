import uuid
import datetime
from typing import Optional, List, Dict, Any
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.models.domain_models import Claim, Shipment, AuditEvent, Facility, Organization
from app.schemas.shipper_schemas import ShipperClaimCreate

class ShipperIngestionService:
    def create_manual_shipper_claim(
        self,
        db: Session,
        req: ShipperClaimCreate,
        claim_id: Optional[str] = None
    ) -> Claim:
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == req.organization_id).first()
        if not org:
            raise ValueError(f'Organization {req.organization_id} not found')

        # Verify facility exists if provided
        if req.facility_id:
            fac = db.query(Facility).filter(Facility.id == req.facility_id).first()
            if not fac:
                raise ValueError(f'Facility {req.facility_id} not found')

        # 1. Deterministic SKU Valuation Math
        processed_skus: List[Dict[str, Any]] = []
        total_loss_sum = 0.0
        for item in req.sku_details:
            item_total = round(item.damaged_qty * item.unit_cost, 2)
            total_loss_sum += item_total
            processed_skus.append({
                'sku': item.sku,
                'description': item.description,
                'damaged_qty': item.damaged_qty,
                'unit_cost': item.unit_cost,
                'total_loss': item_total
            })

        claimed_amount = round(total_loss_sum, 2)

        # 2. Shipment Upsert
        shp_id = f'shp-{uuid.uuid4().hex[:10]}'
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        deadline_9m = now_dt + relativedelta(months=9)

        shipment = Shipment(
            id=shp_id,
            organization_id=req.organization_id,
            external_reference=req.external_reference,
            bol_number=req.bol_number,
            carrier_id=req.carrier_id,
            commodity=f'Shipper Goods (PO {req.po_number})',
            quantity=sum(item.damaged_qty for item in req.sku_details),
            created_at=now_dt
        )
        db.add(shipment)
        db.flush()

        # 3. Create Claim
        final_claim_id = claim_id or f'clm-shp-{uuid.uuid4().hex[:8]}'
        claim = Claim(
            id=final_claim_id,
            organization_id=req.organization_id,
            shipment_id=shp_id,
            facility_id=req.facility_id,
            po_number=req.po_number,
            sku_details=processed_skus,
            claim_type=req.claim_type,
            status='DRAFT',
            claimed_amount=claimed_amount,
            is_approved_by_human=False,
            internal_approval_stage='WAREHOUSE_INSPECTION',
            deadline_at=deadline_9m,
            created_at=now_dt
        )
        db.add(claim)

        # 4. Audit Event
        audit = AuditEvent(
            id=f'aud-{uuid.uuid4().hex[:12]}',
            organization_id=req.organization_id,
            actor_type='HUMAN',
            actor_id='ShipperManualIngestion',
            entity_type='Claim',
            entity_id=final_claim_id,
            action='SHIPPER_CLAIM_MANUALLY_INGESTED',
            after_json={
                'po_number': req.po_number,
                'facility_id': req.facility_id,
                'claimed_amount': claimed_amount,
                'sku_count': len(processed_skus),
                'internal_approval_stage': 'WAREHOUSE_INSPECTION'
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(claim)
        return claim

shipper_ingestion_service = ShipperIngestionService()
