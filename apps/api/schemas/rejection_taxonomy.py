from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RejectionCategory(str, Enum):
    """
    Top-Level Standardized Rejection Reason Taxonomy (Tier 1).
    """
    PROCEDURAL_TIMING = "PROCEDURAL_TIMING"
    DOCUMENTATION_DEFICIENCY = "DOCUMENTATION_DEFICIENCY"
    CARMACK_STATUTORY_EXCEPTION = "CARMACK_STATUTORY_EXCEPTION"
    SALVAGE_MITIGATION = "SALVAGE_MITIGATION"
    COVERAGE_TARIFF_LIMITATION = "COVERAGE_TARIFF_LIMITATION"


class RejectionSubCode(str, Enum):
    """
    Granular Rejection Reason Sub-Codes (Tier 2).
    """
    # 1. PROCEDURAL_TIMING
    MISSED_9_MONTH_CARMACK = "MISSED_9_MONTH_CARMACK"
    MISSED_CONCEALED_DAMAGE_WINDOW = "MISSED_CONCEALED_DAMAGE_WINDOW"
    UNTIMELY_INSPECTION_REQUEST = "UNTIMELY_INSPECTION_REQUEST"

    # 2. DOCUMENTATION_DEFICIENCY
    CLEAN_POD_NO_EXCEPTION = "CLEAN_POD_NO_EXCEPTION"
    MISSING_ORIGINAL_BOL = "MISSING_ORIGINAL_BOL"
    MISSING_COMMERCIAL_INVOICE = "MISSING_COMMERCIAL_INVOICE"
    LACK_OF_DAMAGE_PHOTOS = "LACK_OF_DAMAGE_PHOTOS"

    # 3. CARMACK_STATUTORY_EXCEPTION
    ACT_OF_SHIPPER_PACKAGING = "ACT_OF_SHIPPER_PACKAGING"
    ACT_OF_SHIPPER_LOADING = "ACT_OF_SHIPPER_LOADING"
    ACT_OF_GOD = "ACT_OF_GOD"
    INHERENT_VICE = "INHERENT_VICE"
    PUBLIC_AUTHORITY = "PUBLIC_AUTHORITY"

    # 4. SALVAGE_MITIGATION
    CARGO_DISCARDED_BEFORE_INSPECTION = "CARGO_DISCARDED_BEFORE_INSPECTION"
    FAILURE_TO_MITIGATE_LOSS = "FAILURE_TO_MITIGATE_LOSS"
    UNCREDITED_SALVAGE_VALUE = "UNCREDITED_SALVAGE_VALUE"

    # 5. COVERAGE_TARIFF_LIMITATION
    RELEASED_VALUE_RATES_CAP = "RELEASED_VALUE_RATES_CAP"
    UNAUTHORIZED_COMMODITY_EXCLUSION = "UNAUTHORIZED_COMMODITY_EXCLUSION"
    FORCE_MAJEURE_DELAY_EXCLUSION = "FORCE_MAJEURE_DELAY_EXCLUSION"


CATEGORY_SUBCODE_MAP: Dict[RejectionCategory, List[RejectionSubCode]] = {
    RejectionCategory.PROCEDURAL_TIMING: [
        RejectionSubCode.MISSED_9_MONTH_CARMACK,
        RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW,
        RejectionSubCode.UNTIMELY_INSPECTION_REQUEST,
    ],
    RejectionCategory.DOCUMENTATION_DEFICIENCY: [
        RejectionSubCode.CLEAN_POD_NO_EXCEPTION,
        RejectionSubCode.MISSING_ORIGINAL_BOL,
        RejectionSubCode.MISSING_COMMERCIAL_INVOICE,
        RejectionSubCode.LACK_OF_DAMAGE_PHOTOS,
    ],
    RejectionCategory.CARMACK_STATUTORY_EXCEPTION: [
        RejectionSubCode.ACT_OF_SHIPPER_PACKAGING,
        RejectionSubCode.ACT_OF_SHIPPER_LOADING,
        RejectionSubCode.ACT_OF_GOD,
        RejectionSubCode.INHERENT_VICE,
        RejectionSubCode.PUBLIC_AUTHORITY,
    ],
    RejectionCategory.SALVAGE_MITIGATION: [
        RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION,
        RejectionSubCode.FAILURE_TO_MITIGATE_LOSS,
        RejectionSubCode.UNCREDITED_SALVAGE_VALUE,
    ],
    RejectionCategory.COVERAGE_TARIFF_LIMITATION: [
        RejectionSubCode.RELEASED_VALUE_RATES_CAP,
        RejectionSubCode.UNAUTHORIZED_COMMODITY_EXCLUSION,
        RejectionSubCode.FORCE_MAJEURE_DELAY_EXCLUSION,
    ],
}


SUBCODE_CITATION_MAP: Dict[RejectionSubCode, str] = {
    RejectionSubCode.RELEASED_VALUE_RATES_CAP: (
        "Hughes v. United Van Lines, 829 F.2d 1407 (7th Cir. 1987) 4-part Carmack limitation test; 49 U.S.C. § 14706(c)(1)(A)"
    ),
    RejectionSubCode.ACT_OF_SHIPPER_PACKAGING: (
        "Missouri Pacific R. Co. v. Elmore & Stahl, 377 U.S. 134 (1964) burden of proof shifts to carrier upon prima facie showing"
    ),
    RejectionSubCode.ACT_OF_SHIPPER_LOADING: (
        "Missouri Pacific R. Co. v. Elmore & Stahl, 377 U.S. 134 (1964); carrier non-delegable cargo security duty"
    ),
    RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW: (
        "49 U.S.C. § 14706(e)(1) statutory 9-month minimum filing window; NMFC Item 300135 concealed damage protocol"
    ),
    RejectionSubCode.MISSED_9_MONTH_CARMACK: (
        "49 U.S.C. § 14706(e)(1) federal statutory minimum filing period"
    ),
    RejectionSubCode.CLEAN_POD_NO_EXCEPTION: (
        "Concealed damage latent defect doctrine; clean delivery receipt creates rebuttable presumption overcome by unpack affidavits"
    ),
    RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION: (
        "49 CFR § 370.9 carrier inspection duty; reasonable notice and photographic preservation doctrine"
    ),
    RejectionSubCode.MISSING_ORIGINAL_BOL: (
        "49 U.S.C. § 14706 prima facie element 1 tender in good condition"
    ),
    RejectionSubCode.MISSING_COMMERCIAL_INVOICE: (
        "49 U.S.C. § 14706 prima facie element 3 actual damage valuation"
    ),
    RejectionSubCode.LACK_OF_DAMAGE_PHOTOS: (
        "Evidentiary provenance standards; contemporaneous destination photos"
    ),
    RejectionSubCode.ACT_OF_GOD: (
        "Carmack Amendment narrow common carrier defenses; unpreventable natural force"
    ),
    RejectionSubCode.INHERENT_VICE: (
        "Carmack Amendment natural decay exception; temperature abuse in transit"
    ),
    RejectionSubCode.PUBLIC_AUTHORITY: (
        "Carmack Amendment sovereign authority exception"
    ),
    RejectionSubCode.FAILURE_TO_MITIGATE_LOSS: (
        "Common law mitigation duty; salvage value offset"
    ),
    RejectionSubCode.UNCREDITED_SALVAGE_VALUE: (
        "Net recovery valuation principles"
    ),
    RejectionSubCode.UNAUTHORIZED_COMMODITY_EXCLUSION: (
        "Bill of lading description estoppel and carrier tender acceptance"
    ),
    RejectionSubCode.FORCE_MAJEURE_DELAY_EXCLUSION: (
        "Carmack reasonable dispatch standard under 49 CFR § 1035"
    ),
    RejectionSubCode.UNTIMELY_INSPECTION_REQUEST: (
        "49 CFR § 370.9 & NMFC Item 300135 inspection protocol"
    ),
}


class DenialClassificationResult(BaseModel):
    """
    Structured Output of Carrier Denial Classification.
    """
    primary_category: RejectionCategory = Field(..., description="Primary taxonomy category")
    primary_sub_code: RejectionSubCode = Field(..., description="Granular sub-code")
    secondary_categories: List[RejectionCategory] = Field(default_factory=list, description="Secondary categories for compound letters")
    secondary_sub_codes: List[RejectionSubCode] = Field(default_factory=list, description="Secondary sub-codes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    detected_phrases: List[str] = Field(default_factory=list, description="Key extracted sentences or phrases justifying category")
    requires_human_adjudication: bool = Field(False, description="Flagged true if ambiguous or compound denial detected")
    governing_citation: Optional[str] = Field(None, description="Primary legal citation counter-authority")
    suggested_rebuttal_strategy: Optional[str] = Field(None, description="Recommended defense strategy summary")


class CarrierBehaviorProfile(BaseModel):
    """
    Carrier Intelligence Behavioral Profile.
    """
    carrier_id: str
    carrier_name: str
    total_claims_handled: int = 0
    acceptance_rate_pct: float = 0.0
    partial_settlement_rate_pct: float = 0.0
    denial_rate_pct: float = 0.0
    avg_settlement_ratio: float = 0.0
    time_to_initial_response_days: float = 0.0
    time_to_settlement_days: float = 0.0
    denial_tactic_distribution: Dict[str, float] = Field(default_factory=dict)
