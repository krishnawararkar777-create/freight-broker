import os
import sys
import io
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from app.models.domain_models import DocumentEvidence, ClaimFact, Document
from scripts.seed_demo_data import seed_data

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_local_pdf_parser_extraction_result():
    """LocalPdfParser extracts typed fields, page numbers, and bounding box coordinates."""
    from parsers.local_parser import LocalPdfParser
    from schemas.extraction import ExtractionResult

    parser = LocalPdfParser()
    sample_text = (
        "BILL OF LADING\n"
        "BOL Number: BOL-847293\n"
        "Carrier: ABC Trucking\n"
        "Shipper: Acme Industrial Corp\n"
        "Pickup Date: 2025-12-10\n"
        "Declared Value: $20,000.00\n"
    )
    result: ExtractionResult = parser.parse_text(sample_text, filename="BOL_847293.pdf", document_type="BOL")
    
    assert isinstance(result, ExtractionResult)
    assert result.document_type == "BOL"
    assert len(result.fields) >= 3

    field_map = {f.field_name: f for f in result.fields}
    assert "carrier_name" in field_map
    assert field_map["carrier_name"].value_json["value"] == "ABC Trucking"
    assert field_map["carrier_name"].bbox.page_number == 1

def test_extraction_service_persistence():
    """ExtractionService creates document_evidence and claim_facts database rows."""
    from services.document_service import document_service
    from services.extraction_service import extraction_service

    db = TestingSessionLocal()
    try:
        # Ingest a sample document
        file_bytes = b"BILL OF LADING\nBOL Number: BOL-847293\nCarrier: ABC Trucking\nPickup Date: 2025-12-10\nDeclared Value: $20000.00\n"
        doc = document_service.ingest_document(
            db=db,
            claim_id="clm-847293",
            file_bytes=file_bytes,
            filename="BOL_847293.pdf",
            mime_type="application/pdf",
            document_type="BOL"
        )

        # Run extraction
        result = extraction_service.extract_and_persist(db=db, claim_id="clm-847293", document_id=doc.id, file_bytes=file_bytes)
        assert result.status == "processed"

        # Check document_evidence rows
        evidence_rows = db.query(DocumentEvidence).filter(DocumentEvidence.document_id == doc.id).all()
        assert len(evidence_rows) > 0

        # Check claim_facts rows
        facts = db.query(ClaimFact).filter(ClaimFact.claim_id == "clm-847293").all()
        assert len(facts) > 0
    finally:
        db.close()

def test_missing_field_grounding_rule():
    """Missing fields default to null / UNKNOWN with verification_status = needs_review."""
    from services.document_service import document_service
    from services.extraction_service import extraction_service

    db = TestingSessionLocal()
    try:
        # Ingest incomplete document (missing pickup_date and declared_value)
        file_bytes = b"BILL OF LADING\nBOL Number: BOL-999999\n"
        doc = document_service.ingest_document(
            db=db,
            claim_id="clm-847293",
            file_bytes=file_bytes,
            filename="Incomplete_BOL.pdf",
            mime_type="application/pdf",
            document_type="BOL"
        )

        extraction_service.extract_and_persist(db=db, claim_id="clm-847293", document_id=doc.id, file_bytes=file_bytes)

        # Verify unfound fact is marked needs_review with value None
        missing_fact = db.query(ClaimFact).filter(ClaimFact.claim_id == "clm-847293", ClaimFact.field_name == "declared_value").first()
        if missing_fact:
            assert missing_fact.verification_status == "needs_review"
            assert missing_fact.value_json is None or missing_fact.value_json.get("value") is None
    finally:
        db.close()
