import re
from typing import Dict, Any, List
from parsers.base import BaseDocumentParser, ExtractionResult, ExtractedField

class CarrierResponseParser(BaseDocumentParser):
    """
    Parser for inbound carrier response letters (Acceptance, Partial Settlement, Denial).
    """

    async def parse(self, file_bytes: bytes, filename: str, document_type: str = "CARRIER_RESPONSE") -> ExtractionResult:
        text_content = ""
        try:
            text_content = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text_content = ""

        # Extract carrier reference number
        ref_match = re.search(r'(?:claim|file|ref)\s*(?:#|num|no\.?)?\s*[:\s]*([A-Z0-9\-]{5,20})', text_content, re.IGNORECASE)
        carrier_ref = ref_match.group(1) if ref_match else None

        # Extract monetary amounts
        offer_amount = 0.0
        offer_match = re.search(r'(?:offer|settle|check|amount|pay)\s*(?:of)?\s*\$\s*([0-9,]+\.?[0-9]{0,2})', text_content, re.IGNORECASE)
        if offer_match:
            try:
                offer_amount = float(offer_match.group(1).replace(',', ''))
            except ValueError:
                offer_amount = 0.0

        # Classify decision type
        text_lower = text_content.lower()
        if "deny" in text_lower or "declined" in text_lower or "rejection" in text_lower:
            decision_type = "DENIAL" if offer_amount == 0.0 else "PARTIAL_SETTLEMENT"
        elif "full settlement" in text_lower or "accept" in text_lower:
            decision_type = "ACCEPTANCE"
        elif "inspection" in text_lower:
            decision_type = "INSPECTION_REQUEST"
        elif offer_amount > 0:
            decision_type = "PARTIAL_SETTLEMENT"
        else:
            decision_type = "DENIAL"

        denial_reasons: List[str] = []
        if "packaging" in text_lower:
            denial_reasons.append("improper_packaging")
        if "concealed" in text_lower or "5 day" in text_lower or "notice" in text_lower:
            denial_reasons.append("concealed_damage_late_notice")
        if "salvage" in text_lower:
            denial_reasons.append("salvage_not_retained")
        if "clean pod" in text_lower or "exception" in text_lower:
            denial_reasons.append("clean_pod_no_exception")

        fields = [
            ExtractedField(field_name="decision_type", value=decision_type, confidence=0.95),
            ExtractedField(field_name="offer_amount", value=offer_amount, confidence=0.90),
            ExtractedField(field_name="carrier_claim_reference", value=carrier_ref, confidence=0.85 if carrier_ref else 0.50),
            ExtractedField(field_name="denial_reasons", value=denial_reasons, confidence=0.90)
        ]

        return ExtractionResult(
            document_type="CARRIER_RESPONSE",
            fields=fields,
            raw_text=text_content,
            page_count=1,
            parser_name="CarrierResponseParser",
            parser_version="v1.0"
        )
