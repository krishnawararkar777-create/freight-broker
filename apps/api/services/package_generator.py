import datetime
from typing import Dict, Any, List

def generate_claim_package_narrative(
    claim_number: str,
    carrier_name: str,
    pro_number: str,
    bol_number: str,
    invoice_number: str,
    claimed_amount: float,
    damage_description: str,
    delivery_date: str
) -> Dict[str, Any]:
    """
    Generates formal legal claim demand narrative with mandatory evidence citations.
    Every factual assertion MUST cite grounded evidence [BOL p.1], [POD p.1], [INV-90210], or [NMFC Item 300105].
    """
    citations = [
        "[BOL p.1]",
        "[POD p.1]",
        f"[{invoice_number}]",
        "[49 U.S.C. § 14706 (Carmack Amendment)]",
        "[NMFC Item 300105]"
    ]

    narrative_text = (
        f"FORMAL FREIGHT CLAIM DEMAND NOTICE\n"
        f"Claim Reference: {claim_number}\n"
        f"Carrier: {carrier_name} [BOL p.1]\n"
        f"Shipment PRO#: {pro_number} [BOL p.1]\n"
        f"Bill of Lading #: {bol_number} [BOL p.1]\n"
        f"Delivery Date: {delivery_date} [POD p.1]\n\n"
        f"1. STATEMENT OF CLAIM & CARRIER LIABILITY:\n"
        f"Pursuant to 49 U.S.C. § 14706 (Carmack Amendment) [49 U.S.C. § 14706 (Carmack Amendment)] "
        f"and NMFC Item 300105 [NMFC Item 300105], formal claim demand is hereby submitted for cargo damage "
        f"sustained during transportation under carrier's custody.\n\n"
        f"2. EVIDENCE & DAMAGE EXPLANATION:\n"
        f"Upon delivery on {delivery_date}, physical inspection revealed: \"{damage_description}\" [POD p.1]. "
        f"The shipment was tendered to carrier in good order and condition [BOL p.1].\n\n"
        f"3. CLAIM VALUATION & REIMBURSEMENT DEMAND:\n"
        f"Based on Commercial Vendor Invoice #{invoice_number} [{invoice_number}], the total monetary claim "
        f"amount demanded is ${claimed_amount:,.2f} USD [{invoice_number}].\n\n"
        f"Please acknowledge receipt of this claim within 30 days and remit payment per 49 CFR Part 370."
    )

    return {
        "claim_number": claim_number,
        "narrative_text": narrative_text,
        "citations": citations,
        "model_name": "deterministic-grounded-template-v1.0",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
