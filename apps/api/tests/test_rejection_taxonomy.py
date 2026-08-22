import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.schemas.rejection_taxonomy import (
    RejectionCategory,
    RejectionSubCode,
    DenialClassificationResult,
    CATEGORY_SUBCODE_MAP,
    SUBCODE_CITATION_MAP,
)


def test_rejection_taxonomy_enums_completeness():
    """Verifies all 5 top-level categories and 15 sub-codes exist."""
    assert len(RejectionCategory) == 5
    assert RejectionCategory.PROCEDURAL_TIMING == "PROCEDURAL_TIMING"
    assert RejectionCategory.DOCUMENTATION_DEFICIENCY == "DOCUMENTATION_DEFICIENCY"
    assert RejectionCategory.CARMACK_STATUTORY_EXCEPTION == "CARMACK_STATUTORY_EXCEPTION"
    assert RejectionCategory.SALVAGE_MITIGATION == "SALVAGE_MITIGATION"
    assert RejectionCategory.COVERAGE_TARIFF_LIMITATION == "COVERAGE_TARIFF_LIMITATION"

    # Verify subcodes are properly registered in category map
    assert len(CATEGORY_SUBCODE_MAP[RejectionCategory.PROCEDURAL_TIMING]) == 3
    assert len(CATEGORY_SUBCODE_MAP[RejectionCategory.DOCUMENTATION_DEFICIENCY]) == 4
    assert len(CATEGORY_SUBCODE_MAP[RejectionCategory.CARMACK_STATUTORY_EXCEPTION]) == 5
    assert len(CATEGORY_SUBCODE_MAP[RejectionCategory.SALVAGE_MITIGATION]) == 3
    assert len(CATEGORY_SUBCODE_MAP[RejectionCategory.COVERAGE_TARIFF_LIMITATION]) == 3


def test_rejection_subcode_citations_mapping():
    """Verifies statutory and case law citations are mapped to each denial subcode."""
    assert "Hughes v. United Van Lines" in SUBCODE_CITATION_MAP[RejectionSubCode.RELEASED_VALUE_RATES_CAP]
    assert "Elmore & Stahl" in SUBCODE_CITATION_MAP[RejectionSubCode.ACT_OF_SHIPPER_PACKAGING]
    assert "49 U.S.C. § 14706" in SUBCODE_CITATION_MAP[RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW]


def test_denial_classification_result_validation():
    """Verifies Pydantic schema validation and compound/adjudication flag logic."""
    res = DenialClassificationResult(
        primary_category=RejectionCategory.COVERAGE_TARIFF_LIMITATION,
        primary_sub_code=RejectionSubCode.RELEASED_VALUE_RATES_CAP,
        confidence=0.96,
        detected_phrases=["limited liability to $0.50 per pound", "carrier tariff rate item 100"],
        requires_human_adjudication=False,
    )
    assert res.primary_category == RejectionCategory.COVERAGE_TARIFF_LIMITATION
    assert res.primary_sub_code == RejectionSubCode.RELEASED_VALUE_RATES_CAP
    assert res.requires_human_adjudication is False

    # Compound denial flagging
    compound_res = DenialClassificationResult(
        primary_category=RejectionCategory.DOCUMENTATION_DEFICIENCY,
        primary_sub_code=RejectionSubCode.CLEAN_POD_NO_EXCEPTION,
        secondary_categories=[RejectionCategory.SALVAGE_MITIGATION],
        secondary_sub_codes=[RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION],
        confidence=0.78,
        requires_human_adjudication=True,
    )
    assert compound_res.requires_human_adjudication is True
    assert len(compound_res.secondary_categories) == 1
