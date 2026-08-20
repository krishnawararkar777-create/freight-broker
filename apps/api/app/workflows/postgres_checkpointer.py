"""
Supabase Postgres-Backed Checkpointer for LangGraph Workflow State Persistence.
Ensures claim graph execution checkpoints survive worker restarts and multi-month delays.
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.domain_models import AuditEvent, Claim

logger = logging.getLogger(__name__)


class SupabasePostgresCheckpointer:
    """Checkpointer persisting LangGraph workflow state into PostgreSQL AuditEvents table."""
    
    def __init__(self, db: Session):
        self.db = db

    def save_checkpoint(self, claim_id: str, state: Dict[str, Any]) -> str:
        """Saves a workflow checkpoint for a claim."""
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        org_id = claim.organization_id if claim else "system"
        
        checkpoint_id = f"chk_{uuid.uuid4().hex[:12]}"
        
        audit_event = AuditEvent(
            id=checkpoint_id,
            organization_id=org_id,
            actor_type="SYSTEM",
            actor_id="POSTGRES_CHECKPOINTER",
            entity_type="ClaimWorkflowCheckpoint",
            entity_id=claim_id,
            action="WORKFLOW_CHECKPOINT_SAVED",
            after_json={"state": state, "saved_at": datetime.now(timezone.utc).isoformat()},
            reason=f"Saved checkpoint for claim status {state.get('status')}"
        )
        self.db.add(audit_event)
        self.db.commit()
        self.db.refresh(audit_event)
        
        return audit_event.id

    def load_latest_checkpoint(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest checkpoint state for a claim."""
        audit_event = (
            self.db.query(AuditEvent)
            .filter(
                AuditEvent.entity_type == "ClaimWorkflowCheckpoint",
                AuditEvent.entity_id == claim_id,
                AuditEvent.action == "WORKFLOW_CHECKPOINT_SAVED"
            )
            .order_by(AuditEvent.created_at.desc())
            .first()
        )
        
        if not audit_event or not audit_event.after_json:
            return None
            
        return audit_event.after_json.get("state")
