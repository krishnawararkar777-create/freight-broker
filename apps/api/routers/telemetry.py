import os
import sys
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import get_db
from app.services.telemetry_service import TelemetryService
from app.services.denial_intelligence_service import DenialIntelligenceService

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry & Observability"])
telemetry_service = TelemetryService()
denial_service = DenialIntelligenceService()


@router.get("/metrics")
def get_telemetry_metrics(
    org_id: Optional[str] = Query(None, description="Optional organization ID to filter"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    db: Session = Depends(get_db),
):
    """
    Get production API latency percentiles (P50, P95, P99), request volume,
    and error rate distributions.
    """
    return telemetry_service.get_api_metrics(db=db, org_id=org_id, time_window_hours=hours)


@router.get("/accuracy")
def get_telemetry_accuracy(
    org_id: Optional[str] = Query(None, description="Optional organization ID to filter"),
    db: Session = Depends(get_db),
):
    """
    Get multi-parser extraction accuracy rates (tracking LocalPdfParser,
    PaddlePdfParser, and LlmVisionParser) and per-document-type metrics.
    """
    return telemetry_service.get_extraction_accuracy(db=db, org_id=org_id)


@router.get("/human-diffs")
def get_telemetry_human_diffs(
    org_id: Optional[str] = Query(None, description="Optional organization ID to filter"),
    db: Session = Depends(get_db),
):
    """
    Get human-in-the-loop audit diffs, intervention rates, and field edit frequencies.
    """
    return telemetry_service.get_human_edit_diffs(db=db, org_id=org_id)


@router.get("/rejections")
def get_rejection_analytics(
    org_id: Optional[str] = Query(None, description="Optional organization ID to filter"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated carrier rejection taxonomy distribution and carrier denial matrix.
    """
    return denial_service.get_rejection_analytics(db=db, org_id=org_id)


@router.get("/carrier-profiles")
def get_carrier_profiles(
    org_id: Optional[str] = Query(None, description="Optional organization ID to filter"),
    db: Session = Depends(get_db),
):
    """
    Get carrier behavioral scorecards, acceptance/denial rates, TTIR, and TTS.
    """
    return denial_service.get_all_carrier_profiles(db=db, org_id=org_id)


@router.get("/carrier-profiles/{carrier_id}")
def get_single_carrier_profile(
    carrier_id: str,
    db: Session = Depends(get_db),
):
    """
    Get individual carrier behavioral scorecard.
    """
    return denial_service.get_carrier_profile(db=db, carrier_id=carrier_id)
