import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.domain_models import Claim, AuditEvent, User

ELEVATED_APPROVAL_THRESHOLD = 5000.00

class SubmissionBlockedException(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class SubmissionService:
    def approve_claim(
        self,
        db: Session,
        claim_id: str,
        user_id: str = "usr-1",
        notes: str = "Approved by Claims Manager"
    ) -> Claim:
        """
        Records human approval sign-off and unlocks submission lock.
        """
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        # Ensure user exists to satisfy foreign key
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                organization_id=claim.organization_id,
                name="Sarah Jenkins",
                email=f"{user_id}@marajet.com",
                role="Admin",
                status="active"
            )
            db.add(user)
            db.flush()

        claim.status = "APPROVED"
        claim.is_approved_by_human = True
        claim.approved_by_user_id = user.id
        if claim.claimed_amount >= ELEVATED_APPROVAL_THRESHOLD:
            claim.elevated_approval_acknowledged = True

        # Audit event
        audit = AuditEvent(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            organization_id=claim.organization_id,
            actor_type="HUMAN",
            actor_id=user_id,
            entity_type="Claim",
            entity_id=claim_id,
            action="CLAIM_APPROVED_BY_HUMAN",
            after_json={
                "status": "APPROVED",
                "approved_by_user_id": user_id,
                "notes": notes,
                "claimed_amount": claim.claimed_amount
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(claim)
        return claim

    def submit_claim(self, db: Session, claim_id: str) -> Claim:
        """
        Submits claim package to carrier. Enforces server-side submission guard.
        Returns HTTP 403 / SubmissionBlockedException if claim is unapproved or lacks sign-off.
        """
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        # Server-Side Submission Guard Enforcement
        if not claim.is_approved_by_human or claim.status != "APPROVED":
            raise SubmissionBlockedException(
                message="Server-side submission guard active: Human approval sign-off required prior to carrier dispatch.",
                details={
                    "claim_id": claim_id,
                    "claimed_amount": claim.claimed_amount,
                    "status": claim.status,
                    "is_approved_by_human": claim.is_approved_by_human,
                    "requires_approval_threshold": ELEVATED_APPROVAL_THRESHOLD
                }
            )

        # Release Lock & Transition to SUBMITTED
        sub_ref = f"CARRIER-SUB-{uuid.uuid4().hex[:8].upper()}"
        claim.status = "SUBMITTED"
        claim.submitted_at = datetime.datetime.now(datetime.timezone.utc)

        # Audit Event
        audit = AuditEvent(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            organization_id=claim.organization_id,
            actor_type="SYSTEM",
            actor_id="CarrierDispatchWorker-v1.0",
            entity_type="Claim",
            entity_id=claim_id,
            action="CLAIM_SUBMITTED_TO_CARRIER",
            after_json={
                "status": "SUBMITTED",
                "submission_reference": sub_ref,
                "submitted_at": str(claim.submitted_at)
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(claim)
        return claim

submission_service = SubmissionService()
