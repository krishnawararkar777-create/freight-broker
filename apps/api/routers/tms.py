import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.session import get_db
from app.services.tms_service import tms_service

router = APIRouter(prefix="/api/integrations/tms", tags=["tms"])


@router.post("/{provider}/webhook", status_code=status.HTTP_200_OK)
async def tms_webhook_endpoint(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Ingests TMS webhooks (e.g., McLeod LoadMaster), normalizes shipment payloads,
    upserts shipments, auto-creates claims in DRAFT status upon trigger events,
    and streams attached documents into the extraction pipeline.
    """
    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "invalid_json", "message": f"Invalid JSON payload: {str(exc)}"},
        )

    headers = dict(request.headers)

    result = await tms_service.process_webhook(
        provider=provider,
        raw_payload=payload,
        headers=headers,
        payload_bytes=body_bytes,
        db=db,
    )

    return result
