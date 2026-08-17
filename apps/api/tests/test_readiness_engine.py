import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_readiness_score_100_percent_when_all_documents_present():
    """Calculates 100% readiness score when all 5 evidence items exist."""
    from services.readiness_engine import calculate_readiness_score

    result = calculate_readiness_score(
        has_bol=True,
        has_pod=True,
        has_invoice=True,
        has_photos=True,
        has_carrier_pro=True
    )

    assert result["readiness_score"] == 100
    assert result["is_ready_for_submission"] is True
    assert len(result["itemized_checklist"]) == 5

def test_readiness_score_partial_deduction():
    """Missing damage photos (-15%) yields 85% readiness score."""
    from services.readiness_engine import calculate_readiness_score

    result = calculate_readiness_score(
        has_bol=True,
        has_pod=True,
        has_invoice=True,
        has_photos=False,
        has_carrier_pro=True
    )

    assert result["readiness_score"] == 85
    assert result["is_ready_for_submission"] is True

def test_readiness_score_below_80_threshold_blocks_submission():
    """Score below 80% marks is_ready_for_submission as False."""
    from services.readiness_engine import calculate_readiness_score

    result = calculate_readiness_score(
        has_bol=True,
        has_pod=False,
        has_invoice=True,
        has_photos=False,
        has_carrier_pro=True
    )

    # 25 + 0 + 20 + 0 + 15 = 60
    assert result["readiness_score"] == 60
    assert result["is_ready_for_submission"] is False
