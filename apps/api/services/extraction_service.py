import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.domain_models import Document, DocumentEvidence, ClaimFact, AuditEvent
from parsers.base import BaseDocumentParser
from parsers.local_parser import LocalPdfParser
from parsers.paddle_parser import PaddlePdfParser
from schemas.extraction import ExtractionResult, ExtractedField

CONFIDENCE_THRESHOLD = 0.85
EXPECTED_CLAIM_FIELDS = [
    "carrier_name", "bol_number", "pro_number", "pickup_date",
    "delivery_date", "declared_value", "damaged_quantity", "damage_description"
]

class ExtractionService:
    def __init__(self, parser: Optional[BaseDocumentParser] = None):
        self.parser = parser or PaddlePdfParser()

    def extract_and_persist(
        self,
        db: Session,
        claim_id: str,
        document_id: str,
        file_bytes: bytes
    ) -> ExtractionResult:
        """
        Executes parser, creates document_evidence rows, populates claim_facts with confidence & provenance,
        and enforces evidence grounding rules.
        """
        doc = db.query(Document).filter(Document.id == document_id, Document.claim_id == claim_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found for claim {claim_id}")

        # 1. Invoke Provider-Abstracted Parser
        result: ExtractionResult = self.parser.parse(file_bytes, doc.filename, doc.document_type)

        extracted_field_names = set()

        # 2. Persist DocumentEvidence & ClaimFacts
        for field in result.fields:
            extracted_field_names.add(field.field_name)

            # Insert DocumentEvidence
            evidence_id = f"evd-{uuid.uuid4().hex[:12]}"
            evidence = DocumentEvidence(
                id=evidence_id,
                document_id=document_id,
                page_number=field.page_number,
                bbox_json=field.bbox.model_dump() if field.bbox else None,
                source_text=field.source_text,
                field_name=field.field_name,
                normalized_value_json=field.value_json,
                extraction_method=field.extraction_method,
                confidence=field.confidence
            )
            db.add(evidence)

            # Determine verification status based on confidence
            verification_status = (
                "extracted" if field.confidence >= CONFIDENCE_THRESHOLD else "needs_review"
            )

            # Insert or update ClaimFact
            existing_fact = (
                db.query(ClaimFact)
                .filter(ClaimFact.claim_id == claim_id, ClaimFact.field_name == field.field_name)
                .first()
            )

            if existing_fact:
                # Do NOT overwrite facts that have already been locked by a human edit
                if existing_fact.verification_status != "edited_by_human":
                    existing_fact.value_json = field.value_json
                    existing_fact.source_document_id = document_id
                    existing_fact.source_location = f"{doc.filename} p.{field.page_number}"
                    existing_fact.confidence = field.confidence
                    existing_fact.verification_status = verification_status
            else:
                new_fact = ClaimFact(
                    id=f"fact-{uuid.uuid4().hex[:12]}",
                    claim_id=claim_id,
                    field_name=field.field_name,
                    value_json=field.value_json,
                    source_document_id=document_id,
                    source_location=f"{doc.filename} p.{field.page_number}",
                    confidence=field.confidence,
                    verification_status=verification_status
                )
                db.add(new_fact)

        # 3. Grounding Rule Enforcement for Missing expected fields (null / UNKNOWN with needs_review)
        for expected_field in EXPECTED_CLAIM_FIELDS:
            if expected_field not in extracted_field_names:
                existing_fact = (
                    db.query(ClaimFact)
                    .filter(ClaimFact.claim_id == claim_id, ClaimFact.field_name == expected_field)
                    .first()
                )
                if not existing_fact:
                    unfound_fact = ClaimFact(
                        id=f"fact-{uuid.uuid4().hex[:12]}",
                        claim_id=claim_id,
                        field_name=expected_field,
                        value_json=None,  # null / UNKNOWN
                        source_document_id=document_id,
                        source_location=f"{doc.filename} p.1",
                        confidence=0.0,
                        verification_status="needs_review"  # Flagged for human review
                    )
                    db.add(unfound_fact)

        # 4. Update Document extraction status
        doc.extraction_status = "processed"

        # 5. Write AuditEvent
        audit = AuditEvent(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            organization_id=doc.organization_id,
            actor_type="AI",
            actor_id="LocalPdfParser-v1.0",
            entity_type="Document",
            entity_id=document_id,
            action="DOCUMENT_PARSED_AND_EXTRACTED",
            after_json={"extracted_fields_count": len(result.fields), "status": "processed"}
        )
        db.add(audit)
        db.commit()

        return result

extraction_service = ExtractionService()
