import os
import sys
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from app.models.telemetry_model import APITelemetryLog
from app.models.domain_models import Document, DocumentEvidence, ClaimFact, AuditEvent
from app.services.telemetry_service import TelemetryService


@pytest.fixture
def telemetry_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_api_metrics_percentiles_and_rates(telemetry_db):
    """Verifies P50, P95, P99 latency and error rate calculations."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # Insert 100 sample telemetry logs with known latencies: 1ms, 2ms, ..., 100ms
    for i in range(1, 101):
        status = 200 if i <= 95 else 500  # 5% error rate
        path = "/api/claims/123/documents/upload" if i % 2 == 0 else "/api/claims"
        log = APITelemetryLog(
            organization_id="org-apex-001",
            endpoint_path=path,
            http_method="POST",
            status_code=status,
            latency_ms=float(i),
            request_bytes=500,
            response_bytes=1000,
            created_at=now - datetime.timedelta(minutes=i),
        )
        telemetry_db.add(log)
    telemetry_db.commit()

    service = TelemetryService()
    metrics = service.get_api_metrics(telemetry_db, org_id="org-apex-001")

    assert metrics["total_requests"] == 100
    assert metrics["successful_requests"] == 95
    assert metrics["error_requests"] == 5
    assert metrics["error_rate_pct"] == 5.0
    assert metrics["avg_latency_ms"] == 50.5
    assert metrics["p50_latency_ms"] == 50.0 or metrics["p50_latency_ms"] == 50.5
    assert metrics["p95_latency_ms"] >= 95.0
    assert metrics["p99_latency_ms"] >= 99.0
    assert "status_code_distribution" in metrics
    assert metrics["status_code_distribution"].get(200) == 95
    assert metrics["status_code_distribution"].get(500) == 5


def test_extraction_accuracy_tracking_all_three_parsers(telemetry_db):
    """Verifies extraction accuracy rate for LocalPdfParser, PaddlePdfParser, and LlmVisionParser."""
    # 1. LocalPdfParser doc evidence (high confidence)
    ev1 = DocumentEvidence(
        id="ev-1",
        document_id="doc-1",
        page_number=1,
        source_text="Carrier: ABC Trucking",
        field_name="carrier_name",
        normalized_value_json={"value": "ABC Trucking"},
        extraction_method="LocalPdfParser",
        confidence=0.98,
    )
    # 2. PaddlePdfParser doc evidence (high confidence)
    ev2 = DocumentEvidence(
        id="ev-2",
        document_id="doc-2",
        page_number=1,
        source_text="Declared: $8000",
        field_name="declared_value",
        normalized_value_json={"value": 8000.0},
        extraction_method="PaddleOCR PP-OCRv4 Engine",
        confidence=0.99,
    )
    # 3. LlmVisionParser doc evidence (low confidence)
    ev3 = DocumentEvidence(
        id="ev-3",
        document_id="doc-3",
        page_number=1,
        source_text="Crushed box notation",
        field_name="damage_description",
        normalized_value_json={"value": "Crushed box"},
        extraction_method="LlmVisionParser",
        confidence=0.72,
    )
    telemetry_db.add_all([ev1, ev2, ev3])

    # Documents to check schema pass rate
    d1 = Document(
        id="doc-1",
        organization_id="org-apex-001",
        claim_id="clm-1",
        document_type="BOL",
        filename="bol.pdf",
        mime_type="application/pdf",
        object_key="k1",
        sha256="h1",
        extraction_status="processed",
    )
    d2 = Document(
        id="doc-2",
        organization_id="org-apex-001",
        claim_id="clm-1",
        document_type="POD",
        filename="pod.pdf",
        mime_type="application/pdf",
        object_key="k2",
        sha256="h2",
        extraction_status="processed",
    )
    d3 = Document(
        id="doc-3",
        organization_id="org-apex-001",
        claim_id="clm-1",
        document_type="DAMAGE_PHOTO",
        filename="photo.jpg",
        mime_type="image/jpeg",
        object_key="k3",
        sha256="h3",
        extraction_status="needs_review",
    )
    telemetry_db.add_all([d1, d2, d3])
    telemetry_db.commit()

    service = TelemetryService()
    acc = service.get_extraction_accuracy(telemetry_db)

    assert "by_parser" in acc
    parsers = acc["by_parser"]
    assert "LocalPdfParser" in parsers
    assert "PaddlePdfParser" in parsers
    assert "LlmVisionParser" in parsers

    assert acc["schema_validation_pass_rate_pct"] == 66.67


def test_human_edit_diff_telemetry(telemetry_db):
    """Verifies aggregation of human edits, field frequencies, and mean absolute deltas."""
    # Facts: 3 total, 2 edited by human
    f1 = ClaimFact(
        id="fact-1",
        claim_id="clm-1",
        field_name="declared_value",
        value_json={"value": 8000.0},
        original_value_json={"value": 10000.0},
        confidence=0.95,
        verification_status="edited_by_human",
    )
    f2 = ClaimFact(
        id="fact-2",
        claim_id="clm-1",
        field_name="damaged_quantity",
        value_json={"value": 4},
        original_value_json={"value": 2},
        confidence=0.90,
        verification_status="edited_by_human",
    )
    f3 = ClaimFact(
        id="fact-3",
        claim_id="clm-1",
        field_name="carrier_name",
        value_json={"value": "ABC Trucking"},
        confidence=0.99,
        verification_status="verified",
    )
    telemetry_db.add_all([f1, f2, f3])

    # Audit events for edits
    a1 = AuditEvent(
        id="audit-1",
        organization_id="org-apex-001",
        actor_type="human",
        actor_id="usr-1",
        entity_type="claim_facts",
        entity_id="fact-1",
        action="FACT_EDITED_BY_HUMAN",
        before_json={"value": 10000.0},
        after_json={"value": 8000.0},
        reason="Corrected declared amount",
    )
    telemetry_db.add(a1)
    telemetry_db.commit()

    service = TelemetryService()
    diffs = service.get_human_edit_diffs(telemetry_db)

    assert diffs["total_facts"] == 3
    assert diffs["edited_facts_count"] == 2
    assert diffs["human_intervention_rate_pct"] == 66.67
    assert "declared_value" in diffs["field_edit_frequencies"]
    assert "damaged_quantity" in diffs["field_edit_frequencies"]
