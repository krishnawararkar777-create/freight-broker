from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.models.domain_models import Claim

ACKNOWLEDGMENT_SLA_DAYS = 30
RESOLUTION_SLA_DAYS = 120

def calculate_sla_deadlines(submitted_at: datetime) -> Dict[str, Any]:
    """
    Calculate statutory SLA deadlines under 49 CFR § 370.9 based on claim submission timestamp.
    """
    if not submitted_at:
        return {
            "acknowledgment_due_at": None,
            "resolution_due_at": None,
            "is_acknowledgment_overdue": False,
            "is_resolution_overdue": False,
            "days_since_submission": 0
        }

    # Ensure UTC timezone awareness
    if submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    ack_due = submitted_at + timedelta(days=ACKNOWLEDGMENT_SLA_DAYS)
    res_due = submitted_at + timedelta(days=RESOLUTION_SLA_DAYS)

    days_elapsed = (now - submitted_at).days

    return {
        "acknowledgment_due_at": ack_due.isoformat(),
        "resolution_due_at": res_due.isoformat(),
        "is_acknowledgment_overdue": now > ack_due,
        "is_resolution_overdue": now > res_due,
        "days_since_submission": days_elapsed
    }

def check_claim_sla_status(claim: Claim) -> Dict[str, Any]:
    """
    Evaluate SLA status for a given Claim domain model instance.
    """
    if not claim.submitted_at:
        return {
            "status": "NOT_SUBMITTED",
            "is_acknowledgment_overdue": False,
            "is_resolution_overdue": False
        }

    sla_info = calculate_sla_deadlines(claim.submitted_at)
    
    status_label = "ON_TRACK"
    if claim.status not in ("RESOLVED", "CLOSED", "RECOVERED"):
        if sla_info["is_resolution_overdue"]:
            status_label = "RESOLUTION_OVERDUE"
        elif sla_info["is_acknowledgment_overdue"]:
            status_label = "ACKNOWLEDGMENT_OVERDUE"

    sla_info["status"] = status_label
    return sla_info
