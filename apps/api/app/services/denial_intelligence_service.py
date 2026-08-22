import os
import sys
import re
import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.domain_models import Claim, Shipment, Carrier, CarrierResponse, RecoveryEvent
from app.schemas.rejection_taxonomy import (
    RejectionCategory,
    RejectionSubCode,
    DenialClassificationResult,
    CarrierBehaviorProfile,
    SUBCODE_CITATION_MAP,
)


class DenialIntelligenceService:
    """
    Denial Intelligence Engine for freight cargo claims.
    Performs 2-tier rejection taxonomy classification, detects compound/ambiguous
    pretexts, and computes historical carrier behavioral profiles.
    """

    # Keyword and regex pattern definitions for all 15 sub-codes
    PATTERNS: List[Tuple[RejectionCategory, RejectionSubCode, List[str], float]] = [
        # 1. Coverage / Tariff Limitations
        (
            RejectionCategory.COVERAGE_TARIFF_LIMITATION,
            RejectionSubCode.RELEASED_VALUE_RATES_CAP,
            [
                r"released\s+val",
                r"released\s+rate",
                r"\$0\.50\s*(?:per|/)\s*pound",
                r"\$2\.00\s*(?:per|/)\s*pound",
                r"liability\s+is\s+limited\s+to",
                r"tariff\s+rule\s*100",
                r"tariff\s+rate\s+item",
                r"released\s+evaluation",
                r"maximum\s+settlement\s+liability\s+is\s+therefore\s+capped",
            ],
            0.96,
        ),
        (
            RejectionCategory.COVERAGE_TARIFF_LIMITATION,
            RejectionSubCode.UNAUTHORIZED_COMMODITY_EXCLUSION,
            [r"commodity\s+excluded", r"prohibited\s+commodity", r"not\s+authorized\s+to\s+haul"],
            0.92,
        ),
        (
            RejectionCategory.COVERAGE_TARIFF_LIMITATION,
            RejectionSubCode.FORCE_MAJEURE_DELAY_EXCLUSION,
            [r"force\s+majeure", r"transit\s+delay\s+not\s+guaranteed", r"reasonable\s+dispatch"],
            0.88,
        ),
        # 2. Carmack Statutory Exceptions
        (
            RejectionCategory.CARMACK_STATUTORY_EXCEPTION,
            RejectionSubCode.ACT_OF_SHIPPER_PACKAGING,
            [
                r"improper\s+packaging",
                r"inadequate\s+packaging",
                r"insufficient\s+shrink",
                r"improperly\s+shrink",
                r"packaging\s+integrity",
                r"pallet\s+wrapping",
                r"internal\s+cushioning",
                r"packaging\s+deficiencies",
                r"act\s+(?:or\s+default\s+)?of\s+the\s+shipper",
                r"act\s+of\s+shipper",
                r"shipper\s+improper\s+packaging",
            ],
            0.95,
        ),
        (
            RejectionCategory.CARMACK_STATUTORY_EXCEPTION,
            RejectionSubCode.ACT_OF_SHIPPER_LOADING,
            [
                r"shipper\s+load\s+(?:and|&)\s+count",
                r"sl&c",
                r"improper\s+blocking",
                r"inadequate\s+bracing",
                r"unsecured\s+load\s+by\s+shipper",
            ],
            0.93,
        ),
        (
            RejectionCategory.CARMACK_STATUTORY_EXCEPTION,
            RejectionSubCode.ACT_OF_GOD,
            [r"act\s+of\s+god", r"severe\s+storm", r"tornado", r"unpreventable\s+weather"],
            0.95,
        ),
        (
            RejectionCategory.CARMACK_STATUTORY_EXCEPTION,
            RejectionSubCode.INHERENT_VICE,
            [r"inherent\s+vice", r"natural\s+decay", r"perishable\s+spoilage"],
            0.92,
        ),
        (
            RejectionCategory.CARMACK_STATUTORY_EXCEPTION,
            RejectionSubCode.PUBLIC_AUTHORITY,
            [r"public\s+authority", r"quarantine", r"law\s+enforcement\s+seizure"],
            0.90,
        ),
        # 3. Procedural Timing
        (
            RejectionCategory.PROCEDURAL_TIMING,
            RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW,
            [
                r"concealed\s+loss\s+or\s+damage",
                r"concealed\s+damage",
                r"5\s+business\s+days",
                r"5\s+days\s+of\s+delivery",
                r"5-day\s+tariff\s+rule",
                r"late\s+notice",
                r"reported\s+\d+\s+calendar\s+days",
            ],
            0.94,
        ),
        (
            RejectionCategory.PROCEDURAL_TIMING,
            RejectionSubCode.MISSED_9_MONTH_CARMACK,
            [r"9\s+months", r"nine\s+months", r"statutory\s+filing\s+window\s+expired", r"past\s+carmack\s+window"],
            0.96,
        ),
        (
            RejectionCategory.PROCEDURAL_TIMING,
            RejectionSubCode.UNTIMELY_INSPECTION_REQUEST,
            [r"untimely\s+inspection", r"inspection\s+not\s+requested\s+in\s+time"],
            0.88,
        ),
        # 4. Documentation Deficiency
        (
            RejectionCategory.DOCUMENTATION_DEFICIENCY,
            RejectionSubCode.CLEAN_POD_NO_EXCEPTION,
            [
                r"signed\s+clean",
                r"clean\s+pod",
                r"clear\s+delivery\s+receipt",
                r"without\s+any\s+exception",
                r"no\s+damage\s+exception\s+noted",
                r"delivered\s+in\s+good\s+order",
                r"good-order\s+delivery",
            ],
            0.95,
        ),
        (
            RejectionCategory.DOCUMENTATION_DEFICIENCY,
            RejectionSubCode.MISSING_ORIGINAL_BOL,
            [r"missing\s+bol", r"no\s+bill\s+of\s+lading", r"original\s+bol\s+missing"],
            0.90,
        ),
        (
            RejectionCategory.DOCUMENTATION_DEFICIENCY,
            RejectionSubCode.MISSING_COMMERCIAL_INVOICE,
            [r"commercial\s+invoice\s+missing", r"proof\s+of\s+cost\s+not\s+provided", r"unitemized\s+loss"],
            0.90,
        ),
        (
            RejectionCategory.DOCUMENTATION_DEFICIENCY,
            RejectionSubCode.LACK_OF_DAMAGE_PHOTOS,
            [r"no\s+photographic\s+proof", r"photos\s+not\s+submitted", r"damage\s+photos\s+missing"],
            0.88,
        ),
        # 5. Salvage Mitigation
        (
            RejectionCategory.SALVAGE_MITIGATION,
            RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION,
            [
                r"discarded",
                r"destroyed\s+the\s+damaged\s+goods",
                r"before\s+carrier\s+inspection",
                r"failure\s+to\s+protect\s+salvage",
                r"salvage\s+was\s+not\s+retained",
                r"disposed\s+of\s+all\s+damaged\s+freight",
            ],
            0.95,
        ),
        (
            RejectionCategory.SALVAGE_MITIGATION,
            RejectionSubCode.FAILURE_TO_MITIGATE_LOSS,
            [r"failure\s+to\s+mitigate", r"refused\s+to\s+salvage", r"mitigate\s+damages"],
            0.90,
        ),
        (
            RejectionCategory.SALVAGE_MITIGATION,
            RejectionSubCode.UNCREDITED_SALVAGE_VALUE,
            [r"uncredited\s+salvage", r"salvage\s+allowance\s+missing"],
            0.88,
        ),
    ]

    def classify_denial_letter(self, text: str) -> DenialClassificationResult:
        """
        Classifies carrier denial text against the 2-tier taxonomy.
        Detects compound/ambiguous letters and flags them for human review.
        """
        clean_text = text.strip()
        matched_results: List[Dict[str, Any]] = []

        for category, subcode, pattern_list, base_conf in self.PATTERNS:
            detected_phrases: List[str] = []
            for pat in pattern_list:
                matches = re.findall(pat, clean_text, re.IGNORECASE)
                if matches:
                    detected_phrases.extend(matches)

            if detected_phrases:
                matched_results.append({
                    "category": category,
                    "subcode": subcode,
                    "confidence": base_conf,
                    "phrases": detected_phrases,
                })

        if not matched_results:
            # Fallback default
            return DenialClassificationResult(
                primary_category=RejectionCategory.DOCUMENTATION_DEFICIENCY,
                primary_sub_code=RejectionSubCode.CLEAN_POD_NO_EXCEPTION,
                confidence=0.50,
                detected_phrases=["Unclassified denial language"],
                requires_human_adjudication=True,
                governing_citation="49 U.S.C. § 14706",
                suggested_rebuttal_strategy="General Carmack Prima Facie Rebuttal",
            )

        # Sort matches by confidence descending
        matched_results.sort(key=lambda x: len(x["phrases"]) + x["confidence"], reverse=True)
        primary = matched_results[0]

        # Extract distinct secondary categories
        secondary_categories = list({
            m["category"] for m in matched_results[1:] if m["category"] != primary["category"]
        })
        secondary_subcodes = [
            m["subcode"] for m in matched_results[1:] if m["subcode"] != primary["subcode"]
        ]

        # Compound rule: if multiple distinct top-level categories matched, flag human review
        is_compound = len(secondary_categories) > 0
        conf = primary["confidence"]
        if is_compound:
            conf = min(conf, 0.80)

        requires_adjudication = is_compound or (conf < 0.85)

        citation = SUBCODE_CITATION_MAP.get(primary["subcode"], "49 U.S.C. § 14706")

        strategy_map = {
            RejectionSubCode.RELEASED_VALUE_RATES_CAP: (
                "Confront released-rate defense using 4-part Hughes v. United Van Lines test (lack of fair opportunity to choose rates)."
            ),
            RejectionSubCode.ACT_OF_SHIPPER_PACKAGING: (
                "Invoke Missouri Pacific R. Co. v. Elmore & Stahl burden-shifting; tender under clean BOL estops packaging defense."
            ),
            RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW: (
                "Assert 49 U.S.C. § 14706(e)(1) statutory 9-month minimum filing rights overriding unilateral 5-day tariff clauses."
            ),
            RejectionSubCode.CLEAN_POD_NO_EXCEPTION: (
                "Provide unpacking affidavits and evidence of latent transit impact overcoming clean delivery receipt presumption."
            ),
            RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION: (
                "Demonstrate mitigation compliance, photo preservation, and lack of carrier inspection diligence under 49 CFR § 370.9."
            ),
        }
        strategy = strategy_map.get(primary["subcode"], "Standard Carmack Statutory Prima Facie Rebuttal.")

        return DenialClassificationResult(
            primary_category=primary["category"],
            primary_sub_code=primary["subcode"],
            secondary_categories=secondary_categories,
            secondary_sub_codes=secondary_subcodes,
            confidence=round(conf, 2),
            detected_phrases=primary["phrases"],
            requires_human_adjudication=requires_adjudication,
            governing_citation=citation,
            suggested_rebuttal_strategy=strategy,
        )

    def get_carrier_profile(self, db: Session, carrier_id: str) -> CarrierBehaviorProfile:
        """
        Computes historical settlement rates, response timing (TTIR, TTS),
        and denial tactic distributions for a specific motor carrier.
        """
        carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
        carrier_name = carrier.canonical_name if carrier else "Unknown Carrier"

        shipments = db.query(Shipment).filter(Shipment.carrier_id == carrier_id).all()
        shipment_ids = [s.id for s in shipments]

        claims = db.query(Claim).filter(Claim.shipment_id.in_(shipment_ids)).all() if shipment_ids else []
        total_claims = len(claims)
        if total_claims == 0:
            return CarrierBehaviorProfile(
                carrier_id=carrier_id,
                carrier_name=carrier_name,
                total_claims_handled=0,
                acceptance_rate_pct=0.0,
                partial_settlement_rate_pct=0.0,
                denial_rate_pct=0.0,
                avg_settlement_ratio=0.0,
                time_to_initial_response_days=0.0,
                time_to_settlement_days=0.0,
                denial_tactic_distribution={},
            )

        claim_ids = [c.id for c in claims]
        responses = db.query(CarrierResponse).filter(CarrierResponse.claim_id.in_(claim_ids)).all()
        recoveries = db.query(RecoveryEvent).filter(RecoveryEvent.claim_id.in_(claim_ids)).all()

        acceptances = sum(1 for r in responses if r.decision_type == "ACCEPTANCE")
        partials = sum(1 for r in responses if r.decision_type == "PARTIAL_SETTLEMENT")
        denials = sum(1 for r in responses if r.decision_type == "DENIAL")

        total_claimed = sum(c.claimed_amount for c in claims)
        total_offered = sum(r.offer_amount for r in responses)
        settlement_ratio = round(total_offered / total_claimed, 2) if total_claimed > 0 else 0.0

        # Calculate TTIR (Time-to-Initial-Response in days)
        ttir_days: List[float] = []
        for c in claims:
            if c.submitted_at:
                resp = next((r for r in responses if r.claim_id == c.id), None)
                if resp and resp.created_at:
                    delta = (resp.created_at - c.submitted_at).total_seconds() / 86400.0
                    ttir_days.append(max(0.1, delta))
        avg_ttir = round(sum(ttir_days) / len(ttir_days), 1) if ttir_days else 14.0

        # Calculate TTS (Time-to-Settlement in days)
        tts_days: List[float] = []
        for rec in recoveries:
            c = next((cl for cl in claims if cl.id == rec.claim_id), None)
            if c and c.submitted_at and rec.received_at:
                delta = (rec.received_at - c.submitted_at).total_seconds() / 86400.0
                tts_days.append(max(0.1, delta))
        avg_tts = round(sum(tts_days) / len(tts_days), 1) if tts_days else (avg_ttir + 15.0)

        # Denial tactic distribution
        tactics: Dict[str, int] = {}
        for r in responses:
            if r.decision_type == "DENIAL" and r.denial_reasons_json:
                cat = r.denial_reasons_json.get("primary_category", "CARMACK_STATUTORY_EXCEPTION")
                tactics[cat] = tactics.get(cat, 0) + 1

        tactic_dist: Dict[str, float] = {}
        total_denial_tactics = sum(tactics.values())
        if total_denial_tactics > 0:
            for cat, count in tactics.items():
                tactic_dist[cat] = round((count / total_denial_tactics) * 100.0, 1)

        return CarrierBehaviorProfile(
            carrier_id=carrier_id,
            carrier_name=carrier_name,
            total_claims_handled=total_claims,
            acceptance_rate_pct=round((acceptances / total_claims) * 100.0, 1),
            partial_settlement_rate_pct=round((partials / total_claims) * 100.0, 1),
            denial_rate_pct=round((denials / total_claims) * 100.0, 1),
            avg_settlement_ratio=settlement_ratio,
            time_to_initial_response_days=avg_ttir,
            time_to_settlement_days=avg_tts,
            denial_tactic_distribution=tactic_dist,
        )

    def get_all_carrier_profiles(self, db: Session, org_id: Optional[str] = None) -> List[CarrierBehaviorProfile]:
        """Returns behavior scorecards for all registered carriers."""
        carriers = db.query(Carrier).filter(Carrier.active == True).all()
        return [self.get_carrier_profile(db, c.id) for c in carriers]

    def get_rejection_analytics(self, db: Session, org_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns aggregated rejection taxonomy counts and carrier-by-category denial matrix.
        """
        responses = db.query(CarrierResponse).filter(CarrierResponse.decision_type == "DENIAL").all()
        total_denials = len(responses)

        category_counts: Dict[str, int] = {cat.value: 0 for cat in RejectionCategory}
        subcode_counts: Dict[str, int] = {sub.value: 0 for sub in RejectionSubCode}

        for r in responses:
            if r.denial_reasons_json:
                reasons = r.denial_reasons_json.get("reasons", [])
                primary_cat = r.denial_reasons_json.get("primary_category")
                if primary_cat and primary_cat in category_counts:
                    category_counts[primary_cat] += 1
                else:
                    # Infer category from reasons
                    if any("pack" in r for r in reasons):
                        category_counts[RejectionCategory.CARMACK_STATUTORY_EXCEPTION.value] += 1
                        subcode_counts[RejectionSubCode.ACT_OF_SHIPPER_PACKAGING.value] += 1
                    elif any("conceal" in r or "5 day" in r for r in reasons):
                        category_counts[RejectionCategory.PROCEDURAL_TIMING.value] += 1
                        subcode_counts[RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW.value] += 1
                    elif any("salvage" in r for r in reasons):
                        category_counts[RejectionCategory.SALVAGE_MITIGATION.value] += 1
                        subcode_counts[RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION.value] += 1
                    elif any("released" in r or "rate" in r for r in reasons):
                        category_counts[RejectionCategory.COVERAGE_TARIFF_LIMITATION.value] += 1
                        subcode_counts[RejectionSubCode.RELEASED_VALUE_RATES_CAP.value] += 1
                    else:
                        category_counts[RejectionCategory.DOCUMENTATION_DEFICIENCY.value] += 1
                        subcode_counts[RejectionSubCode.CLEAN_POD_NO_EXCEPTION.value] += 1

        # Carrier Denial Heatmap Matrix (Carrier Canonical Name -> Category Distribution)
        carrier_matrix: List[Dict[str, Any]] = []
        carriers = db.query(Carrier).filter(Carrier.active == True).all()
        for c in carriers:
            prof = self.get_carrier_profile(db, c.id)
            carrier_matrix.append({
                "carrier_id": c.id,
                "carrier_name": c.canonical_name,
                "total_claims": prof.total_claims_handled,
                "denial_rate_pct": prof.denial_rate_pct,
                "denial_tactics": prof.denial_tactic_distribution,
            })

        return {
            "total_denials": total_denials,
            "category_distribution": category_counts,
            "subcode_distribution": subcode_counts,
            "carrier_denial_matrix": carrier_matrix,
        }
