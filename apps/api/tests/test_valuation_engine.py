import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_valuation_engine_ratio_math():
    """
    Valuation engine calculates claimed_amount = total_invoice * (damaged_units / total_units).
    e.g. $20,000 * (2 / 5) = $8,000.00
    """
    from services.valuation_engine import calculate_claim_valuation

    result = calculate_claim_valuation(
        total_invoice_amount=20000.00,
        damaged_units=2,
        total_units=5
    )

    assert result["claimed_amount"] == 8000.00
    assert result["damage_ratio"] == 0.4
    assert result["formula_summary"] == "$20,000.00 Total Invoice × 40.0% Damaged Goods = $8,000.00 Claimed"

def test_valuation_engine_full_loss_fallback():
    """If no item breakdown is provided, valuation defaults to total invoice amount."""
    from services.valuation_engine import calculate_claim_valuation

    result = calculate_claim_valuation(
        total_invoice_amount=15000.00,
        damaged_units=None,
        total_units=None
    )

    assert result["claimed_amount"] == 15000.00
    assert result["damage_ratio"] == 1.0
