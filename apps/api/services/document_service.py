import hashlib
import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.domain_models import Document, Claim, AuditEvent
from services.storage_service import storage_service

class DuplicateDocumentException(Exception):
    def __init__(self, sha256: str, existing_document_id: str):
        self.sha256 = sha256
        self.existing_document_id = existing_document_id
        super().__init__(f"Duplicate document fingerprint detected: {sha256}")

class DocumentService:
    def ingest_document(
        self,
        db: Session,
        claim_id: str,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        document_type: str,
        uploaded_by: Optional[str] = "usr-1"
    ) -> Document:
        """
        Streams document payload, computes SHA-256 fingerprint, checks duplicate idempotency,
        and saves document record.
        """
        # 1. Fetch claim to verify existence & organization_id
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        # 2. Compute SHA-256 checksum while streaming bytes
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # 3. Idempotency Check: Check for existing document with identical sha256 for this claim
        existing_doc = (
            db.query(Document)
            .filter(Document.claim_id == claim_id, Document.sha256 == sha256_hash)
            .first()
        )
        if existing_doc:
            raise DuplicateDocumentException(
                sha256=sha256_hash,
                existing_document_id=existing_doc.id
            )

        # 4. Generate unique document ID & object key
        doc_id = f"doc-{uuid.uuid4().hex[:12]}"
        object_key = f"{claim.organization_id}/{claim_id}/{doc_id}/{filename}"

        # 5. Upload file payload to MinIO (or memory storage in tests)
        storage_service.upload_file(file_bytes, object_key, content_type=mime_type)

        # 6. Save Document metadata record
        doc = Document(
            id=doc_id,
            organization_id=claim.organization_id,
            claim_id=claim_id,
            shipment_id=claim.shipment_id,
            document_type=document_type,
            filename=filename,
            mime_type=mime_type,
            object_key=object_key,
            sha256=sha256_hash,
            page_count=1,
            extraction_status="uploaded",
            uploaded_by=uploaded_by
        )
        db.add(doc)

        # 7. Write AuditEvent
        audit = AuditEvent(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            organization_id=claim.organization_id,
            actor_type="HUMAN",
            actor_id=uploaded_by or "usr-1",
            entity_type="Document",
            entity_id=doc_id,
            action="DOCUMENT_UPLOADED",
            after_json={
                "filename": filename,
                "document_type": document_type,
                "sha256": sha256_hash,
                "object_key": object_key
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)

        return doc

    def get_claim_documents(self, db: Session, claim_id: str) -> List[Document]:
        """Returns all documents associated with a claim."""
        return db.query(Document).filter(Document.claim_id == claim_id).all()

    def get_document_signed_url(self, db: Session, claim_id: str, document_id: str) -> str:
        """Returns short-lived signed URL for viewing a document."""
        doc = db.query(Document).filter(Document.id == document_id, Document.claim_id == claim_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found for claim {claim_id}")
        
        return storage_service.get_signed_url(doc.object_key)

document_service = DocumentService()
