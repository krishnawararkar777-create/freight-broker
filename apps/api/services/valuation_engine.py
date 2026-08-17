from typing import Optional, Dict, Any

def calculate_claim_valuation(
    total_invoice_amount: float,
    damaged_units: Optional[int] = None,
    total_units: Optional[int] = None
) -> Dict[str, Any]:
    """
    Deterministic Freight Claim Valuation Engine.
    Formula: claimed_amount = total_invoice_amount * (damaged_units / total_units)
    """
    invoice_val = float(total_invoice_amount or 0.0)

    if damaged_units is not None and total_units is not None and total_units > 0:
        ratio = min(1.0, max(0.0, float(damaged_units) / float(total_units)))
        claimed_val = round(invoice_val * ratio, 2)
        formula = f"${invoice_val:,.2f} Total Invoice × {ratio * 100:.1f}% Damaged Goods = ${claimed_val:,.2f} Claimed"
    else:
        ratio = 1.0
        claimed_val = round(invoice_val, 2)
        formula = f"${invoice_val:,.2f} Total Invoice (Full Loss / Unitemized) = ${claimed_val:,.2f} Claimed"

    return {
        "total_invoice_amount": invoice_val,
        "damaged_units": damaged_units,
        "total_units": total_units,
        "damage_ratio": ratio,
        "claimed_amount": claimed_val,
        "currency": "USD",
        "formula_summary": formula
    }
