import datetime
from typing import Optional
from dateutil.relativedelta import relativedelta

def calculate_carmack_deadline(delivery_date: datetime.date) -> datetime.date:
    """
    Calculates 49 U.S.C. § 14706 (Carmack Amendment) statutory filing deadline.
    MUST use exact 9 calendar months via relativedelta(months=9).
    Fixed 270-day (9 * 30) arithmetic is STRICTLY FORBIDDEN per rules.md Section 5.
    """
    if not isinstance(delivery_date, datetime.date):
        raise ValueError("delivery_date must be a valid datetime.date object")

    return delivery_date + relativedelta(months=9)

def calculate_concealed_deadline(delivery_date: datetime.date) -> datetime.date:
    """
    Calculates NMFC Item 300100 concealed damage notification deadline (5 business days).
    Skips weekends (Saturday = 5, Sunday = 6).
    """
    if not isinstance(delivery_date, datetime.date):
        raise ValueError("delivery_date must be a valid datetime.date object")

    current = delivery_date
    business_days_added = 0

    while business_days_added < 5:
        current += datetime.timedelta(days=1)
        # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        if current.weekday() < 5:
            business_days_added += 1

    return current

def classify_claim(has_pod: bool, damage_notes: str = "") -> str:
    """
    Classifies claim type based on extracted evidence and keywords.
    Categories:
    - CARGO_DAMAGE: Damaged goods with POD notation
    - CARGO_LOSS: Missing shipment / short receipt without POD
    - CONCEALED_DAMAGE: Unopened box / inner contents damaged notation
    - OVERCHARGE: Billing discrepancy / rate overcharge
    """
    notes_lower = (damage_notes or "").lower()

    if "overcharge" in notes_lower or "billed rate" in notes_lower:
        return "OVERCHARGE"

    if "concealed" in notes_lower or "inner contents" in notes_lower:
        return "CONCEALED_DAMAGE"

    if not has_pod or "shortage" in notes_lower or "lost" in notes_lower or "missing" in notes_lower:
        return "CARGO_LOSS"

    return "CARGO_DAMAGE"
