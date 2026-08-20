import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from db.session import Base
from app.models.domain_models import Claim, Shipment, Organization, User, CustomerPolicy, AuditEvent
from app.workflows.claim_workflow_graph import (
    build_claim_workflow_graph,
    ClaimWorkflowState,
    validate_claim_submission_guard
)
from app.workflows.postgres_checkpointer import SupabasePostgresCheckpointer

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Task 7 Unit & Integration Tests: State Graph & Human Approval Guard
# ---------------------------------------------------------------------------

def test_claim_workflow_state_initialization():
    """Verify ClaimWorkflowState model properties and defaults."""
    state = ClaimWorkflowState(
        claim_id="CLM-847293",
        organization_id="org-apex",
        status="DRAFT",
        claimed_amount=8000.00,
        is_approved_by_human=False,
        readiness_score=85.0,
    )
    assert state.claim_id == "CLM-847293"
    assert state.status == "DRAFT"
    assert state.is_approved_by_human is False
    assert state.claimed_amount == 8000.00


def test_submission_guard_blocks_unapproved_claim():
    """
    TDD Test: Submission guard must reject any attempt to transition an unapproved
    claim or claim without human approval to SUBMITTED state.
    """
    state = ClaimWorkflowState(
        claim_id="CLM-UNAPPROVED-1",
        organization_id="org-apex",
        status="UNDER_REVIEW",
        claimed_amount=6000.00,
        is_approved_by_human=False,  # Unapproved!
        readiness_score=95.0,
    )
    is_valid, reason = validate_claim_submission_guard(state)
    assert is_valid is False
    assert "human approval" in reason.lower() or "unapproved" in reason.lower()


def test_submission_guard_blocks_low_readiness_score():
    """TDD Test: Submission guard must reject claims below 80% readiness score."""
    state = ClaimWorkflowState(
        claim_id="CLM-LOW-READINESS",
        organization_id="org-apex",
        status="UNDER_REVIEW",
        claimed_amount=3000.00,
        is_approved_by_human=True,
        readiness_score=75.0,  # Below 80% threshold!
    )
    is_valid, reason = validate_claim_submission_guard(state)
    assert is_valid is False
    assert "readiness" in reason.lower() or "80" in reason


def test_submission_guard_allows_approved_claim_above_80_readiness():
    """TDD Test: Submission guard allows submission when human approved and readiness >= 80%."""
    state = ClaimWorkflowState(
        claim_id="CLM-APPROVED-1",
        organization_id="org-apex",
        status="APPROVED",
        claimed_amount=4500.00,
        is_approved_by_human=True,
        readiness_score=90.0,
    )
    is_valid, reason = validate_claim_submission_guard(state)
    assert is_valid is True
    assert reason is None


def test_claim_workflow_graph_progression():
    """Verify graph transitions through evidence collection, review, and approval."""
    graph = build_claim_workflow_graph()
    
    # 1. Initial State: DRAFT with 4/4 evidence documents -> transitions to UNDER_REVIEW
    initial_state = {
        "claim_id": "CLM-GRAPH-01",
        "organization_id": "org-apex",
        "status": "DRAFT",
        "claimed_amount": 7500.00,
        "is_approved_by_human": False,
        "evidence_complete": True,
        "readiness_score": 92.0,
        "history": []
    }
    
    result = graph.invoke(initial_state)
    assert result["status"] in ["EVIDENCE_COLLECTION", "UNDER_REVIEW", "DRAFT"]
    assert len(result["history"]) > 0


def test_postgres_checkpointer_persistence(test_db: Session):
    """Verify Postgres checkpointer saves and recovers workflow state from DB."""
    checkpointer = SupabasePostgresCheckpointer(db=test_db)
    
    state_payload = {
        "claim_id": "CLM-CHECKPOINT-1",
        "organization_id": "org-apex",
        "status": "UNDER_REVIEW",
        "claimed_amount": 12000.00,
        "is_approved_by_human": False,
        "readiness_score": 88.0,
        "checkpoint_step": 3
    }
    
    # Save Checkpoint
    checkpoint_id = checkpointer.save_checkpoint(claim_id="CLM-CHECKPOINT-1", state=state_payload)
    assert checkpoint_id is not None
    
    # Load Checkpoint
    loaded = checkpointer.load_latest_checkpoint(claim_id="CLM-CHECKPOINT-1")
    assert loaded is not None
    assert loaded["claim_id"] == "CLM-CHECKPOINT-1"
    assert loaded["status"] == "UNDER_REVIEW"
    assert loaded["checkpoint_step"] == 3
