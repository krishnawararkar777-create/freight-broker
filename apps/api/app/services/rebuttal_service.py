from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.domain_models import Claim, Communication, Shipment, Carrier

def generate_rebuttal_package(db: Session, claim_id: str, denial_pretext: str = "improper_packaging") -> Dict[str, Any]:
    """
    Generate evidence-backed rebuttal demand packet confronting common carrier denial pretexts under Carmack (49 U.S.C. § 14706).
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    shipment = db.query(Shipment).filter(Shipment.id == claim.shipment_id).first() if claim.shipment_id else None
    pro_num = shipment.external_reference if shipment else "N/A"
    carrier = db.query(Carrier).filter(Carrier.id == shipment.carrier_id).first() if (shipment and shipment.carrier_id) else None
    carrier_name = carrier.canonical_name if carrier else "Carrier"

    if denial_pretext == "improper_packaging":
        subject = f"FORMAL REBUTTAL & DEMAND: Claim {claim.id} (PRO# {pro_num}) — Rejection of Packaging Defense"
        body = (
            f"Dear {carrier_name} Claims Department,\n\n"
            f"RE: FORMAL REBUTTAL & FINAL DEMAND FOR CARGO CLAIM {claim.id} (PRO# {pro_num})\n"
            f"Amount Claimed: ${claim.claimed_amount:,.2f}\n\n"
            f"We are in receipt of your declination letter citing 'shipper improper packaging'. We formally reject this defense.\n\n"
            f"1. PRIMA FACIE CARMACK COMPLIANCE (49 U.S.C. § 14706):\n"
            f"The carrier accepted the freight at origin under a clean Bill of Lading [BOL p.1] with zero exceptions "
            f"noted regarding packaging integrity. Under standard Carmack Amendment jurisprudence, accepting freight without exception "
            f"establishes prima facie proof of good condition at tender.\n\n"
            f"2. EVIDENTIARY REBUTTAL:\n"
            f"Photo evidence [Photo p.1] explicitly shows damage resulted from physical impact vectors during transit, "
            f"not internal pallet breakdown.\n\n"
            f"Please respond within 14 calendar days to avoid formal legal escalation.\n\n"
            f"Sincerely,\nSarah Jenkins (Claims Manager)"
        )
    elif denial_pretext == "concealed_damage_late_notice":
        subject = f"FORMAL REBUTTAL: Claim {claim.id} (PRO# {pro_num}) — Concealed Damage Notice Compliance"
        body = (
            f"Dear {carrier_name} Claims Department,\n\n"
            f"RE: FORMAL REBUTTAL TO CONCEALED DAMAGE DENIAL FOR CLAIM {claim.id} (PRO# {pro_num})\n"
            f"Amount Claimed: ${claim.claimed_amount:,.2f}\n\n"
            f"We reject your declination citing late notice. Written notice of concealed damage was transmitted within "
            f"the required protocol window following uncrating. Under 49 U.S.C. § 14706, statutory Carmack liability "
            f"cannot be extinguished by unilateral tariff limitation clauses when damage occurred in carrier custody.\n\n"
            f"Photo evidence [Photo p.1] and clean origin BOL [BOL p.1] confirm carrier liability.\n\n"
            f"Sincerely,\nSarah Jenkins (Claims Manager)"
        )
    else:
        subject = f"FORMAL REBUTTAL & RECONSIDERATION DEMAND: Claim {claim.id} (PRO# {pro_num})"
        body = (
            f"Dear {carrier_name} Claims Department,\n\n"
            f"We formally dispute your denial of Claim {claim.id} (PRO# {pro_num}) under 49 U.S.C. § 14706.\n"
            f"Clean origin BOL [BOL p.1] and delivery POD exception notes confirm carrier liability for actual loss of ${claim.claimed_amount:,.2f}.\n\n"
            f"Sincerely,\nSarah Jenkins (Claims Manager)"
        )

    comm = Communication(
        id=f"comm-rebut-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        claim_id=claim_id,
        channel="email",
        direction="outbound",
        sender="sarah@apex.com",
        recipient=f"claims@{carrier_name.lower().replace(' ', '')}.com",
        subject=subject,
        body=body,
        draft_status="DRAFT"
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)

    return {
        "id": comm.id,
        "claim_id": comm.claim_id,
        "subject": comm.subject,
        "body": comm.body,
        "draft_status": comm.draft_status
    }
