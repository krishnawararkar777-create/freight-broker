"""
EDI 204 Motor Carrier Load Tender & EDI 211 Motor Carrier Bill of Lading Parser.
Extracts shipment load tenders, bills of lading references, shipper/consignee entities,
origin/destination geographic details, commodity/NMFC details, weights, piece counts, and declared values.
"""
import re
from typing import Optional
from pydantic import BaseModel, Field

from app.parsers.edi.x12_segment_parser import (
    tokenize_x12,
    find_segments,
    find_first_segment,
    X12Segment,
)


class EDI204211ParseResult(BaseModel):
    """Structured result from parsing an EDI 204 (Load Tender) or EDI 211 (Bill of Lading) message."""
    transaction_set: str = Field(description="EDI transaction set identifier ('204' or '211')")
    shipment_reference: str = Field(description="Shipment identification or load tender reference number")
    bol_number: Optional[str] = Field(default=None, description="Bill of Lading number")
    shipper_name: Optional[str] = Field(default=None, description="Shipper / origin facility name")
    consignee_name: Optional[str] = Field(default=None, description="Consignee / delivery destination name")
    origin_city_state: Optional[str] = Field(default=None, description="Origin city and state (e.g. 'CHICAGO, IL')")
    destination_city_state: Optional[str] = Field(default=None, description="Destination city and state (e.g. 'DALLAS, TX')")
    commodity: Optional[str] = Field(default=None, description="Commodity description / lading item description")
    nmfc_code: Optional[str] = Field(default=None, description="National Motor Freight Classification code")
    weight: float = Field(default=0.0, description="Gross/billed shipment weight in lbs")
    total_pieces: int = Field(default=0, description="Total carton / piece count")
    declared_value: float = Field(default=0.0, description="Declared shipment value in USD")


def _parse_edi_amount(amt_str: str) -> float:
    """Parse EDI monetary amount string into a float."""
    clean = amt_str.strip().replace("$", "").replace(",", "")
    if not clean:
        return 0.0
    try:
        return round(float(clean), 2)
    except ValueError:
        return 0.0


def _parse_edi_weight(weight_str: str) -> float:
    """Parse shipment weight string into float."""
    clean = re.sub(r"[^\d.]", "", weight_str.strip())
    if not clean:
        return 0.0
    try:
        return float(clean)
    except ValueError:
        return 0.0


def _parse_edi_pieces(pieces_str: str) -> int:
    """Parse piece count string into integer."""
    clean = re.sub(r"\D", "", pieces_str.strip())
    if not clean:
        return 0
    try:
        return int(clean)
    except ValueError:
        return 0


def parse_edi_204_211(raw_content: str) -> EDI204211ParseResult:
    """
    Parse an EDI 204 (Motor Carrier Load Tender) or EDI 211 (Motor Carrier Bill of Lading) message.
    
    Extracts:
    - ST segment: Validates transaction set (204 or 211)
    - B2 / BOL / B10 / L11 / N9 segments: Shipment reference and Bill of Lading number
    - N1 & N4 loops: Shipper/Consignee names and Origin/Destination city/state
    - L5 / AT5 segments: Commodity description and NMFC code
    - L0 / AT8 / L3 segments: Total weight and Total pieces (piece count)
    - AMT / H3 / L3 segments: Declared shipment valuation in USD
    """
    if not raw_content or not raw_content.strip():
        raise ValueError("EDI payload is empty")

    segments = tokenize_x12(raw_content)
    if not segments:
        raise ValueError("Failed to parse any segments from EDI payload")

    # Validate Transaction Set ST*204 or ST*211
    st_seg = find_first_segment(segments, "ST")
    if not st_seg or not st_seg.get(1):
        raise ValueError("Missing ST transaction set header segment")

    transaction_set = st_seg.get(1).strip()
    if transaction_set not in ("204", "211"):
        raise ValueError(f"Expected EDI transaction set '204' or '211', found '{transaction_set}'")

    shipment_reference: Optional[str] = None
    bol_number: Optional[str] = None

    # Check BOL segment (standard for 211)
    bol_seg = find_first_segment(segments, "BOL")
    if bol_seg and bol_seg.get(1):
        bol_number = bol_seg.get(1)

    # Check B2 segment (common in 204 & 211)
    # Formats:
    # B2*tariff*carrier_scac*shipment_id*...
    # B2**carrier_scac*shipment_id*...
    b2_seg = find_first_segment(segments, "B2")
    if b2_seg:
        # Check standard elements
        b2_1 = b2_seg.get(1)
        b2_2 = b2_seg.get(2)
        b2_3 = b2_seg.get(3)
        b2_4 = b2_seg.get(4)

        if b2_3 and len(b2_3) > 2:
            shipment_reference = b2_3
        elif b2_4 and len(b2_4) > 2:
            shipment_reference = b2_4
        elif b2_2 and len(b2_2) > 4:
            shipment_reference = b2_2
        elif b2_1 and len(b2_1) > 4:
            shipment_reference = b2_1

    # Check B10 segment (if present)
    b10_seg = find_first_segment(segments, "B10")
    if b10_seg:
        if not shipment_reference and b10_seg.get(1):
            shipment_reference = b10_seg.get(1)
        if not bol_number and b10_seg.get(2):
            bol_number = b10_seg.get(2)

    # Reference segments scan: L11 and N9
    ref_segments = find_segments(segments, "L11") + find_segments(segments, "N9")
    for ref in ref_segments:
        ref_val = ref.get(1)
        qualifier = ref.get(2).upper()
        if qualifier in ("BM", "BOL", "BL") and not bol_number:
            bol_number = ref_val
        elif qualifier in ("SI", "SR", "SID", "CN", "OQ", "PO", "RN", "TN", "LO") and not shipment_reference:
            shipment_reference = ref_val

    # If either is still missing, fallback cross-assignment
    if not shipment_reference and bol_number:
        shipment_reference = bol_number
    if not bol_number and shipment_reference:
        # Check if reference looks like BOL
        if "BOL" in shipment_reference.upper():
            bol_number = shipment_reference

    if not shipment_reference:
        raise ValueError("Missing shipment reference in EDI 204/211 message")

    # Sequential scan for N1/N4 loops (Shipper/Consignee and Origin/Destination)
    shipper_name: Optional[str] = None
    consignee_name: Optional[str] = None
    origin_city_state: Optional[str] = None
    destination_city_state: Optional[str] = None

    current_entity_type: Optional[str] = None

    for seg in segments:
        if seg.tag == "N1":
            entity_id = seg.get(1).upper()
            entity_name = seg.get(2)
            if entity_id in ("SH", "SF", "SU", "SE", "OB"):
                current_entity_type = "SH"
                if not shipper_name and entity_name:
                    shipper_name = entity_name
            elif entity_id in ("CN", "ST", "RE", "C1", "IB", "DA"):
                current_entity_type = "CN"
                if not consignee_name and entity_name:
                    consignee_name = entity_name
            else:
                current_entity_type = None

        elif seg.tag == "N4":
            city = seg.get(1)
            state = seg.get(2)
            loc_str = f"{city}, {state}" if (city and state) else (city or state or "")
            if loc_str:
                if current_entity_type == "SH" and not origin_city_state:
                    origin_city_state = loc_str
                elif current_entity_type == "CN" and not destination_city_state:
                    destination_city_state = loc_str
                elif not origin_city_state:
                    origin_city_state = loc_str
                elif not destination_city_state:
                    destination_city_state = loc_str

        elif seg.tag == "MS1":
            city = seg.get(1)
            state = seg.get(2)
            loc_str = f"{city}, {state}" if (city and state) else (city or state or "")
            if loc_str:
                if not origin_city_state:
                    origin_city_state = loc_str
                elif not destination_city_state:
                    destination_city_state = loc_str

    # Extract Commodity & NMFC Code from L5 or AT5
    commodity: Optional[str] = None
    nmfc_code: Optional[str] = None

    l5_segments = find_segments(segments, "L5")
    for l5 in l5_segments:
        if not commodity and l5.get(2):
            commodity = l5.get(2)
        if not nmfc_code:
            l5_3 = l5.get(3)
            l5_4 = l5.get(4)
            if l5_3 and (l5_3.isdigit() or len(l5_3) >= 4):
                nmfc_code = l5_3
            elif l5_4 and (l5_4.isdigit() or len(l5_4) >= 4):
                nmfc_code = l5_4
            elif l5_3:
                nmfc_code = l5_3

    if not commodity:
        at5_seg = find_first_segment(segments, "AT5")
        if at5_seg:
            commodity = at5_seg.get(2) or at5_seg.get(3) or None

    # Extract Weight & Total Pieces from L0, AT8, L3
    weight = 0.0
    total_pieces = 0

    l0_segments = find_segments(segments, "L0")
    for l0 in l0_segments:
        # Elements in L0: L0*Line*BilledWeight*Unit*Weight*Qualifier*Pieces*Packaging...
        # Look for weight in element 2 or 4
        if weight == 0.0:
            if l0.get(4):
                weight = _parse_edi_weight(l0.get(4))
            elif l0.get(2):
                weight = _parse_edi_weight(l0.get(2))

        # Look for piece count
        if total_pieces == 0:
            for idx in (7, 6, 8, 5, 11):
                val = l0.get(idx)
                if val.isdigit() and int(val) > 0:
                    total_pieces = int(val)
                    break

    if weight == 0.0 or total_pieces == 0:
        at8_seg = find_first_segment(segments, "AT8")
        if at8_seg:
            if weight == 0.0 and at8_seg.get(3):
                weight = _parse_edi_weight(at8_seg.get(3))
            if total_pieces == 0 and at8_seg.get(4):
                total_pieces = _parse_edi_pieces(at8_seg.get(4))

    if weight == 0.0 or total_pieces == 0:
        l3_seg = find_first_segment(segments, "L3")
        if l3_seg:
            if weight == 0.0 and l3_seg.get(1):
                weight = _parse_edi_weight(l3_seg.get(1))
            if total_pieces == 0 and l3_seg.get(11):
                total_pieces = _parse_edi_pieces(l3_seg.get(11))

    # Extract Declared Value from AMT, H3, or L3
    declared_value = 0.0
    amt_segments = find_segments(segments, "AMT")
    for amt in amt_segments:
        qualifier = amt.get(1).upper()
        amt_val = _parse_edi_amount(amt.get(2))
        if amt_val > 0:
            if qualifier in ("DV", "EV", "7", "TT", "AV", "IV") or declared_value == 0.0:
                declared_value = amt_val
                if qualifier in ("DV", "EV", "7"):
                    break

    if declared_value == 0.0:
        h3_seg = find_first_segment(segments, "H3")
        if h3_seg and h3_seg.get(2):
            declared_value = _parse_edi_amount(h3_seg.get(2))

    return EDI204211ParseResult(
        transaction_set=transaction_set,
        shipment_reference=shipment_reference,
        bol_number=bol_number,
        shipper_name=shipper_name,
        consignee_name=consignee_name,
        origin_city_state=origin_city_state,
        destination_city_state=destination_city_state,
        commodity=commodity,
        nmfc_code=nmfc_code,
        weight=weight,
        total_pieces=total_pieces,
        declared_value=declared_value,
    )
