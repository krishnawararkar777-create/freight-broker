import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_package_generator_contains_required_citations():
    """
    Generated legal demand letter MUST contain bracketed grounded citations:
    [BOL p.1], [POD p.1], [INV-90210], and [NMFC Item 300105].
    """
    from services.package_generator import generate_claim_package_narrative

    res = generate_claim_package_narrative(
        claim_number="CLM-847293",
        carrier_name="ABC Trucking",
        pro_number="PRO-847293",
        bol_number="BOL-847293",
        invoice_number="INV-90210",
        claimed_amount=8000.00,
        damage_description="3 cartons crushed on pallet",
        delivery_date="2025-12-10"
    )

    narrative = res["narrative_text"]

    assert "[BOL p.1]" in narrative
    assert "[POD p.1]" in narrative
    assert "[INV-90210]" in narrative
    assert "[NMFC Item 300105]" in narrative
    assert "8,000.00" in narrative
    assert res["model_name"] == "deterministic-grounded-template-v1.0"
    assert len(res["citations"]) >= 4
