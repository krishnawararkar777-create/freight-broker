import pytest
from datetime import datetime, timedelta
from app.workflows.workflow_triggers import evaluate_workflow_triggers

def test_day_30_sla_overdue_trigger():
    """Verify Day 30 SLA overdue trigger when submitted > 30 days ago without acknowledgment."""
    submitted_at = datetime.now() - timedelta(days=35)
    delivery_at = datetime.now() - timedelta(days=40)
    
    triggers = evaluate_workflow_triggers(
        submitted_at=submitted_at,
        delivery_at=delivery_at,
        carrier_acknowledged=False
    )
    
    assert "DAY_30_SLA_OVERDUE" in triggers


def test_day_30_sla_not_overdue_when_acknowledged():
    """Verify Day 30 SLA trigger is NOT present if carrier acknowledged."""
    submitted_at = datetime.now() - timedelta(days=35)
    delivery_at = datetime.now() - timedelta(days=40)
    
    triggers = evaluate_workflow_triggers(
        submitted_at=submitted_at,
        delivery_at=delivery_at,
        carrier_acknowledged=True  # Acknowledged!
    )
    
    assert "DAY_30_SLA_OVERDUE" not in triggers


def test_day_90_carmack_warning_trigger():
    """Verify Day 90 warning trigger when delivery occurred > 240 days (~8 months) ago."""
    submitted_at = None
    delivery_at = datetime.now() - timedelta(days=250)
    
    triggers = evaluate_workflow_triggers(
        submitted_at=submitted_at,
        delivery_at=delivery_at,
        carrier_acknowledged=False
    )
    
    assert "DAY_90_CARMACK_WARNING" in triggers


def test_day_120_resolution_escalation_trigger():
    """Verify Day 120 resolution escalation trigger when submitted > 120 days ago."""
    submitted_at = datetime.now() - timedelta(days=125)
    delivery_at = datetime.now() - timedelta(days=150)
    
    triggers = evaluate_workflow_triggers(
        submitted_at=submitted_at,
        delivery_at=delivery_at,
        carrier_acknowledged=True
    )
    
    assert "DAY_120_RESOLUTION_ESCALATION" in triggers
