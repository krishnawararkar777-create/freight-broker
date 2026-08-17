import os
import sys
import datetime
import pytest
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_carmack_9_calendar_month_deadline_not_270_days():
    """
    Carmack Amendment statutory deadline MUST use exact 9 calendar months (relativedelta),
    never fixed 270 days.
    """
    from services.carmack_engine import calculate_carmack_deadline

    delivery_date = datetime.date(2025, 12, 10)
    carmack_deadline = calculate_carmack_deadline(delivery_date)

    # 9 calendar months from Dec 10, 2025 is Sept 10, 2026
    expected_deadline = datetime.date(2026, 9, 10)
    assert carmack_deadline == expected_deadline

    # 270 days from Dec 10, 2025 is Sept 6, 2026 (INCORRECT)
    incorrect_270_day_deadline = delivery_date + datetime.timedelta(days=270)
    assert carmack_deadline != incorrect_270_day_deadline

def test_concealed_damage_5_business_day_deadline():
    """Concealed damage deadline calculates 5 business days, skipping weekends."""
    from services.carmack_engine import calculate_concealed_deadline

    # Wednesday Dec 10, 2025
    delivery_date = datetime.date(2025, 12, 10)
    concealed_deadline = calculate_concealed_deadline(delivery_date)

    # 5 business days: Thu (1), Fri (2), Mon (3), Tue (4), Wed (5) -> Dec 17, 2025
    expected = datetime.date(2025, 12, 17)
    assert concealed_deadline == expected

def test_claim_classification_rules():
    """Classifies claims into CARGO_DAMAGE, CARGO_LOSS, CONCEALED_DAMAGE, or OVERCHARGE."""
    from services.carmack_engine import classify_claim

    assert classify_claim(has_pod=True, damage_notes="3 cartons crushed on pallet") == "CARGO_DAMAGE"
    assert classify_claim(has_pod=False, damage_notes="Shipment missing entirely") == "CARGO_LOSS"
    assert classify_claim(has_pod=True, damage_notes="Concealed damage found inside sealed box") == "CONCEALED_DAMAGE"
    assert classify_claim(has_pod=True, damage_notes="Invoice rate mismatch $500 overcharge") == "OVERCHARGE"
