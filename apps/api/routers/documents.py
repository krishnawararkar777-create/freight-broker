from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from db.session import get_db
from services.document_service import document_service, DuplicateDocumentException
from services.extraction_service import extraction_service

router = APIRouter(prefix="/api/claims", tags=["documents"])

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    claim_id: str
    document_type: str
    filename: str
    mime_type: str
    object_key: str
    sha256: str
    extraction_status: str
    created_at: str

class SignedUrlResponse(BaseModel):
    document_id: str
    signed_url: str

@router.post("/{claim_id}/documents/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Streams file payload, computes SHA-256 fingerprint, checks duplicate idempotency,
    stores payload in MinIO, creates document record, and triggers extraction worker.
    """
    try:
        file_bytes = file.file.read()
        doc = document_service.ingest_document(
            db=db,
            claim_id=claim_id,
            file_bytes=file_bytes,
            filename=file.filename or "uploaded_document.pdf",
            mime_type=file.content_type or "application/pdf",
            document_type=document_type
        )
        # Trigger extraction worker & provenance persistence
        extraction_service.extract_and_persist(db=db, claim_id=claim_id, document_id=doc.id, file_bytes=file_bytes)
        return {
            "id": doc.id,
            "organization_id": doc.organization_id,
            "claim_id": doc.claim_id,
            "document_type": doc.document_type,
            "filename": doc.filename,
            "mime_type": doc.mime_type,
            "object_key": doc.object_key,
            "sha256": doc.sha256,
            "extraction_status": doc.extraction_status,
            "created_at": str(doc.created_at)
        }
    except DuplicateDocumentException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "duplicate_document",
                "message": "Duplicate document fingerprint detected",
                "details": {
                    "sha256": exc.sha256,
                    "existing_document_id": exc.existing_document_id
                }
            }
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "not_found", "message": str(exc)}
        )

@router.get("/{claim_id}/documents")
def get_claim_documents(claim_id: str, db: Session = Depends(get_db)):
    """Returns list of documents attached to a claim."""
    docs = document_service.get_claim_documents(db, claim_id)
    return [
        {
            "id": d.id,
            "claim_id": d.claim_id,
            "document_type": d.document_type,
            "filename": d.filename,
            "mime_type": d.mime_type,
            "sha256": d.sha256,
            "extraction_status": d.extraction_status
        }
        for d in docs
    ]

@router.get("/{claim_id}/documents/{document_id}/url")
def get_document_signed_url(claim_id: str, document_id: str, db: Session = Depends(get_db)):
    """Returns a short-lived presigned URL for document access."""
    try:
        url = document_service.get_document_signed_url(db, claim_id, document_id)
        return {"document_id": document_id, "signed_url": url}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "not_found", "message": str(exc)}
        )
