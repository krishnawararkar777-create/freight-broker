from typing import Dict, Any, List

SUBMISSION_THRESHOLD = 80

def calculate_readiness_score(
    has_bol: bool = False,
    has_pod: bool = False,
    has_invoice: bool = False,
    has_photos: bool = False,
    has_carrier_pro: bool = False
) -> Dict[str, Any]:
    """
    Calculates dynamic readiness score and evidence compliance checklist for a claim package.
    Weights:
    - BOL: 25%
    - POD: 25%
    - Invoice: 20%
    - Photos: 15%
    - Carrier PRO/ID: 15%
    """
    checklist: List[Dict[str, Any]] = [
        {"criterion": "Bill of Lading Present", "points": 25, "passed": bool(has_bol)},
        {"criterion": "Proof of Delivery Present", "points": 25, "passed": bool(has_pod)},
        {"criterion": "Vendor Invoice Present", "points": 20, "passed": bool(has_invoice)},
        {"criterion": "Damage Photos Present", "points": 15, "passed": bool(has_photos)},
        {"criterion": "Carrier Identity Verified", "points": 15, "passed": bool(has_carrier_pro)},
    ]

    total_score = sum(item["points"] for item in checklist if item["passed"])
    is_ready = total_score >= SUBMISSION_THRESHOLD

    explanations = []
    for item in checklist:
        mark = "✓" if item["passed"] else "✗"
        explanations.append(f"{mark} {item['criterion']} (+{item['points']}%)")

    return {
        "readiness_score": total_score,
        "is_ready_for_submission": is_ready,
        "submission_threshold": SUBMISSION_THRESHOLD,
        "itemized_checklist": checklist,
        "explanations": explanations
    }
