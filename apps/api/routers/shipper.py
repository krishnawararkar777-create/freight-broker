import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from db.session import get_db
from app.models.domain_models import Facility, Claim, Organization
from app.schemas.shipper_schemas import (
    FacilityCreate, FacilityResponse, FacilityListResponse,
    ShipperClaimCreate, ShipperStageApprovalRequest, ShipperApprovalStatusResponse
)
from services.shipper_ingestion_service import shipper_ingestion_service
from services.shipper_approval_service import shipper_approval_service

router = APIRouter(prefix='/api/shipper', tags=['Shipper Operations'])

@router.post('/facilities', response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(
    organization_id: str,
    req: FacilityCreate,
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Organization {organization_id} not found')

    fac_id = f'fac-{uuid.uuid4().hex[:10]}'
    fac = Facility(
        id=fac_id,
        organization_id=organization_id,
        facility_code=req.facility_code,
        name=req.name,
        facility_type=req.facility_type,
        address=req.address,
        city=req.city,
        state=req.state,
        contact_name=req.contact_name,
        contact_email=req.contact_email,
        active=req.active
    )
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

@router.get('/facilities', response_model=FacilityListResponse)
def list_facilities(
    organization_id: str,
    db: Session = Depends(get_db)
):
    facilities = db.query(Facility).filter(Facility.organization_id == organization_id, Facility.active == True).all()
    return FacilityListResponse(facilities=facilities, total=len(facilities))

@router.post('/claims/manual', status_code=status.HTTP_201_CREATED)
def create_manual_shipper_claim(
    req: ShipperClaimCreate,
    db: Session = Depends(get_db)
):
    try:
        claim = shipper_ingestion_service.create_manual_shipper_claim(db=db, req=req)
        return {
            'id': claim.id,
            'organization_id': claim.organization_id,
            'facility_id': claim.facility_id,
            'po_number': claim.po_number,
            'claimed_amount': claim.claimed_amount,
            'status': claim.status,
            'internal_approval_stage': claim.internal_approval_stage,
            'sku_details': claim.sku_details
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.post('/claims/{claim_id}/approvals/inspection')
def sign_warehouse_inspection(
    claim_id: str,
    req: ShipperStageApprovalRequest,
    db: Session = Depends(get_db)
):
    try:
        claim = shipper_approval_service.sign_warehouse_inspection(
            db=db,
            claim_id=claim_id,
            user_id=req.user_id,
            user_role=req.user_role,
            notes=req.notes
        )
        return {
            'claim_id': claim.id,
            'internal_approval_stage': claim.internal_approval_stage,
            'inspection_signed_by': claim.inspection_signed_by,
            'inspection_signed_at': str(claim.inspection_signed_at) if claim.inspection_signed_at else None
        }
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.post('/claims/{claim_id}/approvals/logistics')
def sign_logistics_verification(
    claim_id: str,
    req: ShipperStageApprovalRequest,
    db: Session = Depends(get_db)
):
    try:
        claim = shipper_approval_service.sign_logistics_verification(
            db=db,
            claim_id=claim_id,
            user_id=req.user_id,
            user_role=req.user_role,
            notes=req.notes
        )
        return {
            'claim_id': claim.id,
            'internal_approval_stage': claim.internal_approval_stage,
            'logistics_signed_by': claim.logistics_signed_by,
            'logistics_signed_at': str(claim.logistics_signed_at) if claim.logistics_signed_at else None
        }
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.post('/claims/{claim_id}/approvals/director')
def sign_director_approval(
    claim_id: str,
    req: ShipperStageApprovalRequest,
    db: Session = Depends(get_db)
):
    try:
        claim = shipper_approval_service.sign_director_approval(
            db=db,
            claim_id=claim_id,
            user_id=req.user_id,
            user_role=req.user_role,
            notes=req.notes
        )
        return {
            'claim_id': claim.id,
            'internal_approval_stage': claim.internal_approval_stage,
            'status': claim.status,
            'is_approved_by_human': claim.is_approved_by_human,
            'director_signed_by': claim.director_signed_by,
            'director_signed_at': str(claim.director_signed_at) if claim.director_signed_at else None
        }
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.get('/claims/{claim_id}/approval-status', response_model=ShipperApprovalStatusResponse)
def get_approval_status(
    claim_id: str,
    db: Session = Depends(get_db)
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Claim {claim_id} not found')

    return ShipperApprovalStatusResponse(
        claim_id=claim.id,
        organization_id=claim.organization_id,
        facility_id=claim.facility_id,
        po_number=claim.po_number,
        claimed_amount=claim.claimed_amount,
        status=claim.status,
        internal_approval_stage=claim.internal_approval_stage or 'WAREHOUSE_INSPECTION',
        is_approved_by_human=claim.is_approved_by_human or False,
        inspection_signed_by=claim.inspection_signed_by,
        inspection_signed_at=str(claim.inspection_signed_at) if claim.inspection_signed_at else None,
        inspection_notes=claim.inspection_notes,
        logistics_signed_by=claim.logistics_signed_by,
        logistics_signed_at=str(claim.logistics_signed_at) if claim.logistics_signed_at else None,
        logistics_notes=claim.logistics_notes,
        director_signed_by=claim.director_signed_by,
        director_signed_at=str(claim.director_signed_at) if claim.director_signed_at else None,
        director_notes=claim.director_notes
    )
