"""
LangGraph Claim Lifecycle State Graph & Human Approval Guard
Models the complete claim lifecycle:
DRAFT -> EVIDENCE_COLLECTION -> UNDER_REVIEW -> APPROVED -> SUBMITTED -> ACKNOWLEDGED -> SETTLED / REBUTTAL_PENDING -> LAWSUIT_CLOCK
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class ClaimWorkflowState(BaseModel):
    """Pydantic model representing state of a claim within the workflow graph."""
    claim_id: str
    organization_id: str
    status: str = "DRAFT"
    claimed_amount: float = 0.0
    is_approved_by_human: bool = False
    readiness_score: float = 0.0
    evidence_complete: bool = False
    carrier_acknowledged: bool = False
    settlement_accepted: bool = False
    rebuttal_pending: bool = False
    lawsuit_clock_active: bool = False
    history: List[str] = Field(default_factory=list)


def validate_claim_submission_guard(state: ClaimWorkflowState) -> Tuple[bool, Optional[str]]:
    """
    Server-side human approval guard enforcing non-negotiable submission rules:
    1. is_approved_by_human must be True before transitioning to SUBMITTED.
    2. readiness_score must be >= 80.0.
    """
    if not state.is_approved_by_human:
        return False, "Submission blocked: Claim requires explicit human approval sign-off."
    
    if state.readiness_score < 80.0:
        return False, f"Submission blocked: Readiness score {state.readiness_score}% is below required 80.0% threshold."

    return True, None


# Node implementations for LangGraph state machine
def draft_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = state.get("history", [])
    history.append("Entered DRAFT state")
    
    # If documents are uploaded, advance to EVIDENCE_COLLECTION
    evidence_complete = state.get("evidence_complete", False)
    next_status = "EVIDENCE_COLLECTION" if evidence_complete else "DRAFT"
    
    return {
        **state,
        "status": next_status,
        "history": history
    }


def evidence_collection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = state.get("history", [])
    history.append("Entered EVIDENCE_COLLECTION state")
    
    readiness = state.get("readiness_score", 0.0)
    next_status = "UNDER_REVIEW" if readiness >= 80.0 else "EVIDENCE_COLLECTION"
    
    return {
        **state,
        "status": next_status,
        "history": history
    }


def under_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = state.get("history", [])
    history.append("Entered UNDER_REVIEW state")
    
    # Needs explicit human approval to transition to APPROVED
    is_approved = state.get("is_approved_by_human", False)
    next_status = "APPROVED" if is_approved else "UNDER_REVIEW"
    
    return {
        **state,
        "status": next_status,
        "history": history
    }


def approved_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = state.get("history", [])
    history.append("Entered APPROVED state - ready for human submission")
    
    return {
        **state,
        "status": "APPROVED",
        "history": history
    }


def submitted_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = state.get("history", [])
    history.append("Entered SUBMITTED state")
    
    acknowledged = state.get("carrier_acknowledged", False)
    next_status = "ACKNOWLEDGED" if acknowledged else "SUBMITTED"
    
    return {
        **state,
        "status": next_status,
        "history": history
    }


def acknowledged_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = state.get("history", [])
    history.append("Entered ACKNOWLEDGED state")
    
    settled = state.get("settlement_accepted", False)
    rebuttal = state.get("rebuttal_pending", False)
    
    if settled:
        next_status = "SETTLED"
    elif rebuttal:
        next_status = "REBUTTAL_PENDING"
    else:
        next_status = "ACKNOWLEDGED"
        
    return {
        **state,
        "status": next_status,
        "history": history
    }


def route_next_status(state: Dict[str, Any]) -> str:
    """Conditional router directing flow based on current state status."""
    status = state.get("status", "DRAFT")
    if status == "DRAFT":
        return "draft"
    elif status == "EVIDENCE_COLLECTION":
        return "evidence_collection"
    elif status == "UNDER_REVIEW":
        return "under_review"
    elif status == "APPROVED":
        return "approved"
    elif status == "SUBMITTED":
        return "submitted"
    elif status == "ACKNOWLEDGED":
        return "acknowledged"
    return END


def build_claim_workflow_graph():
    """Builds and compiles the LangGraph Claim Lifecycle StateGraph."""
    workflow = StateGraph(dict)
    
    # Add nodes
    workflow.add_node("draft", draft_node)
    workflow.add_node("evidence_collection", evidence_collection_node)
    workflow.add_node("under_review", under_review_node)
    workflow.add_node("approved", approved_node)
    workflow.add_node("submitted", submitted_node)
    workflow.add_node("acknowledged", acknowledged_node)
    
    # Define entry & edges
    workflow.set_entry_point("draft")
    workflow.add_edge("draft", END)
    workflow.add_edge("evidence_collection", END)
    workflow.add_edge("under_review", END)
    workflow.add_edge("approved", END)
    workflow.add_edge("submitted", END)
    workflow.add_edge("acknowledged", END)
    
    return workflow.compile()
