import uuid
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.domain_models import Claim, AuditEvent, User, Organization, CustomerPolicy
from app.core.rbac import check_role_permission, RBACRole

class ShipperApprovalService:
    def sign_warehouse_inspection(
        self,
        db: Session,
        claim_id: str,
        user_id: str,
        user_role: str,
        notes: Optional[str] = None
    ) -> Claim:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f'Claim {claim_id} not found')

        # RBAC Check: Plant Manager / Inspector, Shipper Admin, Admin
        if not check_role_permission(user_role=user_role, required_role=RBACRole.PLANT_MANAGER_INSPECTOR):
            raise PermissionError(f'Role {user_role} is not authorized to sign Warehouse Inspection')

        if claim.internal_approval_stage not in ('WAREHOUSE_INSPECTION', None):
            raise ValueError(f'Cannot perform Warehouse Inspection in stage {claim.internal_approval_stage}')

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        claim.inspection_signed_by = user_id
        claim.inspection_signed_at = now_dt
        claim.inspection_notes = notes or 'Warehouse Inspection completed and signed'
        claim.internal_approval_stage = 'LOGISTICS_VERIFICATION'

        audit = AuditEvent(
            id=f'aud-{uuid.uuid4().hex[:12]}',
            organization_id=claim.organization_id,
            actor_type='HUMAN',
            actor_id=user_id,
            entity_type='Claim',
            entity_id=claim.id,
            action='SHIPPER_WAREHOUSE_INSPECTION_SIGNED',
            after_json={
                'internal_approval_stage': 'LOGISTICS_VERIFICATION',
                'signed_by': user_id,
                'role': user_role,
                'notes': notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(claim)
        return claim

    def sign_logistics_verification(
        self,
        db: Session,
        claim_id: str,
        user_id: str,
        user_role: str,
        notes: Optional[str] = None
    ) -> Claim:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f'Claim {claim_id} not found')

        # RBAC Check: Logistics Coordinator, Logistics Director, Shipper Admin, Admin
        if not check_role_permission(user_role=user_role, required_role=RBACRole.LOGISTICS_COORDINATOR):
            raise PermissionError(f'Role {user_role} is not authorized to sign Logistics Verification')

        # Sequential stage check
        if claim.internal_approval_stage == 'WAREHOUSE_INSPECTION':
            raise ValueError('Warehouse Inspection must be completed before Logistics Verification.')
        elif claim.internal_approval_stage != 'LOGISTICS_VERIFICATION':
            raise ValueError(f'Cannot perform Logistics Verification in stage {claim.internal_approval_stage}')

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        claim.logistics_signed_by = user_id
        claim.logistics_signed_at = now_dt
        claim.logistics_notes = notes or 'Logistics Verification completed and carrier matched'
        claim.internal_approval_stage = 'DIRECTOR_APPROVAL'

        audit = AuditEvent(
            id=f'aud-{uuid.uuid4().hex[:12]}',
            organization_id=claim.organization_id,
            actor_type='HUMAN',
            actor_id=user_id,
            entity_type='Claim',
            entity_id=claim.id,
            action='SHIPPER_LOGISTICS_VERIFICATION_SIGNED',
            after_json={
                'internal_approval_stage': 'DIRECTOR_APPROVAL',
                'signed_by': user_id,
                'role': user_role,
                'notes': notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(claim)
        return claim

    def sign_director_approval(
        self,
        db: Session,
        claim_id: str,
        user_id: str,
        user_role: str,
        notes: Optional[str] = None
    ) -> Claim:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f'Claim {claim_id} not found')

        # RBAC Check: Logistics Director, Shipper Admin, Admin (especially for >= $5,000)
        if not check_role_permission(user_role=user_role, required_role=RBACRole.LOGISTICS_DIRECTOR, claimed_amount=claim.claimed_amount):
            raise PermissionError(f'Role {user_role} lacks elevated authorization for Director Approval on ${claim.claimed_amount} claim')

        # Sequential stage check
        if claim.internal_approval_stage in ('WAREHOUSE_INSPECTION', 'LOGISTICS_VERIFICATION'):
            raise ValueError(f'Previous internal approval stages must be completed before Director Approval (currently: {claim.internal_approval_stage})')

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        claim.director_signed_by = user_id
        claim.director_signed_at = now_dt
        claim.director_notes = notes or 'Director Approval granted for formal carrier claim submission'
        claim.internal_approval_stage = 'READY_FOR_SUBMISSION'
        claim.is_approved_by_human = True
        claim.status = 'APPROVED'
        claim.approved_by_user_id = user_id
        if claim.claimed_amount >= 5000.00:
            claim.elevated_approval_acknowledged = True

        audit = AuditEvent(
            id=f'aud-{uuid.uuid4().hex[:12]}',
            organization_id=claim.organization_id,
            actor_type='HUMAN',
            actor_id=user_id,
            entity_type='Claim',
            entity_id=claim.id,
            action='SHIPPER_DIRECTOR_APPROVAL_SIGNED',
            after_json={
                'internal_approval_stage': 'READY_FOR_SUBMISSION',
                'status': 'APPROVED',
                'signed_by': user_id,
                'role': user_role,
                'notes': notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(claim)
        return claim

shipper_approval_service = ShipperApprovalService()
