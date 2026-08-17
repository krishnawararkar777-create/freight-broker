import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app
from db.session import Base, get_db
from scripts.seed_demo_data import seed_data

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

def test_submit_unapproved_claim_returns_403_forbidden():
    """
    Submitting an unapproved claim returns HTTP 403 Forbidden with submission_blocked error code.
    """
    res = client.post("/api/claims/clm-847293/submit")
    assert res.status_code == 403
    err = res.json()
    assert err["error_code"] == "submission_blocked"

def test_approve_and_submit_claim_workflow_success():
    """
    Approving claim updates status to APPROVED, then submission succeeds returning HTTP 200.
    """
    # 1. Human Approval Endpoint -> 200 OK
    approve_res = client.post(
        "/api/claims/clm-847293/approve",
        json={"user_id": "usr-1", "notes": "Approved by Claims Manager Sarah Jenkins"}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"
    assert approve_res.json()["is_approved_by_human"] is True

    # 2. Submission Endpoint -> 200 OK
    submit_res = client.post("/api/claims/clm-847293/submit")
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["status"] == "SUBMITTED"
    assert "submission_reference" in submit_data
