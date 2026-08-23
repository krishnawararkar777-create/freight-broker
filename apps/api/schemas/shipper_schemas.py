from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class FacilityBase(BaseModel):
    facility_code: str = Field(..., description='Unique plant/facility code within organization, e.g. PLANT-OH-01')
    name: str = Field(..., description='Facility or Plant Name')
    facility_type: str = Field('MANUFACTURING_PLANT', description='MANUFACTURING_PLANT | DISTRIBUTION_CENTER')
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    active: bool = True

class FacilityCreate(FacilityBase):
    pass

class FacilityResponse(FacilityBase):
    id: str
    organization_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FacilityListResponse(BaseModel):
    facilities: List[FacilityResponse]
    total: int

class SkuItemDetail(BaseModel):
    sku: str = Field(..., description='SKU or part number')
    description: str = Field(..., description='Description of commodity/part')
    damaged_qty: int = Field(..., ge=1, description='Number of damaged units/pieces')
    unit_cost: float = Field(..., ge=0.0, description='Cost basis per unit (standard manufacturing cost or wholesale)')
    total_loss: Optional[float] = Field(None, description='Total loss for this SKU item (computed as damaged_qty * unit_cost)')

class ShipperClaimCreate(BaseModel):
    organization_id: str = Field(..., description='Shipper Organization ID')
    facility_id: str = Field(..., description='Origin or Receiving Facility ID')
    po_number: str = Field(..., description='Purchase Order or Sales Order Reference Number')
    carrier_id: str = Field(..., description='Tendered Carrier ID')
    external_reference: str = Field(..., description='PRO or Carrier Tracking Number')
    bol_number: str = Field(..., description='Bill of Lading Number')
    claim_type: str = Field('Cargo Damage', description='Claim Type')
    sku_details: List[SkuItemDetail] = Field(..., min_length=1, description='Line item SKU breakdown')
    notes: Optional[str] = None

class ShipperStageApprovalRequest(BaseModel):
    user_id: str = Field(..., description='User ID signing off')
    user_role: str = Field(..., description='RBAC role of the signing user')
    notes: Optional[str] = Field(None, description='Inspection or sign-off notes')

class ShipperApprovalStatusResponse(BaseModel):
    claim_id: str
    organization_id: str
    facility_id: Optional[str]
    po_number: Optional[str]
    claimed_amount: float
    status: str
    internal_approval_stage: str
    is_approved_by_human: bool
    inspection_signed_by: Optional[str]
    inspection_signed_at: Optional[str]
    inspection_notes: Optional[str]
    logistics_signed_by: Optional[str]
    logistics_signed_at: Optional[str]
    logistics_notes: Optional[str]
    director_signed_by: Optional[str]
    director_signed_at: Optional[str]
    director_notes: Optional[str]
