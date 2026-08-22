import os
import sys
import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base, get_db
from app.models.telemetry_model import APITelemetryLog
from app.models.domain_models import Document, DocumentEvidence, ClaimFact, AuditEvent
from main import app


@pytest.fixture
def test_db_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed sample telemetry and document data
    db = TestingSessionLocal()
    now = datetime.datetime.now(datetime.timezone.utc)
    for i in range(1, 21):
        status = 200 if i <= 18 else 500
        log = APITelemetryLog(
            organization_id="org-apex-001",
            endpoint_path="/api/claims",
            http_method="GET",
            status_code=status,
            latency_ms=10.0 + i,
            request_bytes=100,
            response_bytes=500,
            created_at=now,
        )
        db.add(log)

    doc = Document(
        id="doc-tel-1",
        organization_id="org-apex-001",
        claim_id="clm-1",
        document_type="BOL",
        filename="bol.pdf",
        mime_type="application/pdf",
        object_key="k1",
        sha256="h1",
        extraction_status="processed",
    )
    db.add(doc)

    ev1 = DocumentEvidence(
        id="ev-tel-1",
        document_id="doc-tel-1",
        page_number=1,
        source_text="Carrier: ABC Trucking",
        field_name="carrier_name",
        normalized_value_json={"value": "ABC Trucking"},
        extraction_method="LocalPdfParser",
        confidence=0.95,
    )
    ev2 = DocumentEvidence(
        id="ev-tel-2",
        document_id="doc-tel-1",
        page_number=1,
        source_text="Carrier: ABC Trucking",
        field_name="carrier_name",
        normalized_value_json={"value": "ABC Trucking"},
        extraction_method="PaddleOCR PP-OCRv4 Engine",
        confidence=0.99,
    )
    db.add_all([ev1, ev2])

    fact = ClaimFact(
        id="fact-tel-1",
        claim_id="clm-1",
        field_name="carrier_name",
        value_json={"value": "ABC Trucking"},
        confidence=0.99,
        verification_status="verified",
    )
    db.add(fact)
    db.commit()
    db.close()

    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_get_telemetry_metrics_endpoint(test_db_client):
    """Verifies GET /api/telemetry/metrics returns structured latency & request data."""
    response = test_db_client.get("/api/telemetry/metrics?hours=24")
    assert response.status_code == 200
    data = response.json()

    assert data["total_requests"] >= 20
    assert "error_rate_pct" in data
    assert "avg_latency_ms" in data
    assert "p50_latency_ms" in data
    assert "p95_latency_ms" in data
    assert "p99_latency_ms" in data
    assert "status_code_distribution" in data
    assert "heavy_endpoints" in data


def test_get_telemetry_accuracy_endpoint(test_db_client):
    """Verifies GET /api/telemetry/accuracy returns multi-parser accuracy analytics."""
    response = test_db_client.get("/api/telemetry/accuracy")
    assert response.status_code == 200
    data = response.json()

    assert data["total_documents"] >= 1
    assert data["schema_validation_pass_rate_pct"] == 100.0
    assert "by_parser" in data
    assert "by_document_type" in data
    assert "LocalPdfParser" in data["by_parser"]
    assert "PaddlePdfParser" in data["by_parser"]
    assert "LlmVisionParser" in data["by_parser"]


def test_get_telemetry_human_diffs_endpoint(test_db_client):
    """Verifies GET /api/telemetry/human-diffs returns human edit statistics."""
    response = test_db_client.get("/api/telemetry/human-diffs")
    assert response.status_code == 200
    data = response.json()

    assert "total_facts" in data
    assert "edited_facts_count" in data
    assert "human_intervention_rate_pct" in data
    assert "field_edit_frequencies" in data
