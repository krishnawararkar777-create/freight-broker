from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from typing import Dict, Any

def calculate_carmack_lawsuit_deadline(denial_date: datetime) -> Dict[str, Any]:
    """
    Calculate statutory Carmack Amendment lawsuit deadline (49 U.S.C. § 14706(e)(1)):
    lawsuit_deadline_at = denial_date + relativedelta(years=2, days=1)
    """
    if not denial_date:
        return {
            "lawsuit_deadline_at": None,
            "days_remaining": 0,
            "is_lawsuit_barred": False
        }

    if denial_date.tzinfo is None:
        denial_date = denial_date.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    deadline = denial_date + relativedelta(years=2, days=1)

    days_remaining = (deadline - now).days
    is_barred = now > deadline

    return {
        "denial_date": denial_date.isoformat(),
        "lawsuit_deadline_at": deadline.isoformat(),
        "days_remaining": days_remaining,
        "is_lawsuit_barred": is_barred
    }
