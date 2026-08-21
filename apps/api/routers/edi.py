import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File
from sqlalchemy.orm import Session

from db.session import get_db
from app.services.edi_service import edi_service

router = APIRouter(prefix="/api/integrations/edi", tags=["edi"])


@router.post("/ingest", status_code=status.HTTP_200_OK)
async def ingest_edi_endpoint(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Ingests inbound EDI X12 payloads (EDI 214, EDI 210, EDI 204, EDI 211).
    Auto-detects transaction set from ST segment, parses fields, computes statutory deadlines,
    upserts shipment state, and generates DRAFT claims upon damage/shortage exceptions.
    """
    body_bytes = await request.body()
    if not body_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "empty_payload", "message": "EDI payload is empty"},
        )

    # Decode body
    raw_content = body_bytes.decode("utf-8", errors="replace")

    # If payload is JSON wrapping raw EDI, extract it
    if raw_content.strip().startswith("{"):
        try:
            data = json.loads(raw_content)
            raw_content = data.get("raw_content") or data.get("edi_text") or raw_content
        except Exception:
            pass

    try:
        result = edi_service.process_edi_payload(
            raw_content=raw_content,
            db=db,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "edi_parse_error", "message": str(exc)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "edi_processing_error", "message": str(exc)},
        )
