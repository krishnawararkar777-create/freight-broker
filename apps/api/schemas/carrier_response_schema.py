from typing import List, Optional
from pydantic import BaseModel, Field

class CarrierResponseExtraction(BaseModel):
    carrier_claim_reference: Optional[str] = Field(None, description="Carrier's internal claim/file reference number")
    decision_type: str = Field(..., description="ACCEPTANCE, PARTIAL_SETTLEMENT, DENIAL, or INSPECTION_REQUEST")
    claimed_amount: float = Field(0.0, description="Original claimed amount")
    offer_amount: float = Field(0.0, description="Carrier's settlement offer amount")
    disputed_amount: float = Field(0.0, description="Difference between claimed and offer amount")
    denial_reasons: List[str] = Field(default_factory=list, description="Extracted denial reason codes or pretexts")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Overall extraction confidence score")
    verification_status: str = Field("verified", description="verified or needs_review")

class CarrierResponseCreate(BaseModel):
    claim_id: str
    document_id: str
    decision_type: str
    carrier_claim_reference: Optional[str] = None
    offer_amount: float = 0.0
    denial_reasons: List[str] = []
