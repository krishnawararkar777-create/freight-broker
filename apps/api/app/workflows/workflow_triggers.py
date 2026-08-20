"""
Workflow Event Triggers Engine
Evaluates statutory and timeline event triggers for long-running claims:
- Day 30 SLA Overdue (49 CFR § 370.9)
- Day 90 Carmack Filing Warning (30-day countdown alert before 9-month statutory deadline)
- Day 120 Resolution Escalation (49 CFR § 370.9 statutory resolution window)
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def evaluate_workflow_triggers(
    submitted_at: Optional[datetime],
    delivery_at: Optional[datetime],
    carrier_acknowledged: bool,
    closed: bool = False
) -> List[str]:
    """
    Evaluates timeline triggers for a claim.
    Returns list of active alert strings.
    """
    if closed:
        return []

    alerts: List[str] = []
    now = datetime.now()

    # 1. Day 30 SLA Receipt Acknowledgment Overdue Trigger (49 CFR § 370.9)
    if submitted_at and not carrier_acknowledged:
        days_submitted = (now - submitted_at).days
        if days_submitted >= 30:
            alerts.append("DAY_30_SLA_OVERDUE")

    # 2. Day 90 Carmack Statutory Deadline Warning Trigger (Filing deadline within 30 days)
    if delivery_at and not submitted_at:
        days_since_delivery = (now - delivery_at).days
        # Carmack deadline is 9 months (~270 days). Day 90 warning fires at >= 240 days (~8 months).
        if days_since_delivery >= 240:
            alerts.append("DAY_90_CARMACK_WARNING")

    # 3. Day 120 Resolution Escalation Trigger (49 CFR § 370.9 120-day resolution window)
    if submitted_at:
        days_submitted = (now - submitted_at).days
        if days_submitted >= 120:
            alerts.append("DAY_120_RESOLUTION_ESCALATION")

    return alerts
