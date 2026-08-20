"""
EDI 210 Freight Details and Invoice Parser.
Extracts freight invoice numbers, linehaul/fuel charges, total weights,
piece counts, shipper/consignee entities, and computes damage ratio valuations.
"""
from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, Field

from app.parsers.edi.x12_segment_parser import (
    tokenize_x12,
    find_segments,
    find_first_segment,
    X12Segment,
)


class EDI210ParseResult(BaseModel):
    """Structured result from parsing an EDI 210 Freight Details and Invoice message."""
    transaction_set: str = Field(default="210", description="EDI transaction set identifier")
    invoice_number: str = Field(description="Carrier freight invoice number")
    bol_number: Optional[str] = Field(default=None, description="Bill of Lading number")
    pro_number: Optional[str] = Field(default=None, description="Carrier PRO / tracking reference number")
    invoice_date: Optional[datetime] = Field(default=None, description="Invoice issue date")
    invoice_total: float = Field(default=0.0, description="Total invoice amount in USD")
    weight: float = Field(default=0.0, description="Billed/gross shipment weight in lbs")
    total_pieces: int = Field(default=0, description="Total piece or carton count")
    consignee_name: Optional[str] = Field(default=None, description="Consignee / delivery destination name")
    shipper_name: Optional[str] = Field(default=None, description="Shipper / origin facility name")

    def calculate_damaged_amount(self, damaged_qty: int) -> float:
        """
        Deterministic ratio valuation math:
        claimed_amount = round(invoice_total * (damaged_qty / total_pieces), 2)
        """
        if damaged_qty <= 0:
            return 0.0
        if self.total_pieces <= 0:
            return round(self.invoice_total, 2)
        
        ratio = min(1.0, float(damaged_qty) / float(self.total_pieces))
        return round(self.invoice_total * ratio, 2)


def _parse_edi_date(date_str: str) -> Optional[datetime]:
    """Parse EDI date (YYYYMMDD or YYMMDD) string into a Python datetime object."""
    date_clean = re.sub(r"\D", "", date_str.strip())
    if len(date_clean) == 8:
        return datetime.strptime(date_clean, "%Y%m%d")
    elif len(date_clean) == 6:
        return datetime.strptime(date_clean, "%y%m%d")
    return None


def _parse_edi_amount(amt_str: str) -> float:
    """
    Parse EDI monetary amount string into a float.
    Handles explicit decimal strings (e.g. '12500.50') as well as standard
    X12 N2 implied cents representations (e.g. '2000000' -> 20000.00).
    """
    clean = amt_str.strip().replace("$", "").replace(",", "")
    if not clean:
        return 0.0
    if "." in clean:
        try:
            return round(float(clean), 2)
        except ValueError:
            return 0.0
    try:
        int_val = int(clean)
        return round(int_val / 100.0, 2)
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


def parse_edi_210(raw_content: str) -> EDI210ParseResult:
    """
    Parse an EDI 210 Motor Carrier Freight Details and Invoice message.
    
    Extracts:
    - B3 segment: Invoice number, BOL reference, Invoice date, Net invoice total
    - N1 segments: Shipper and Consignee entity names
    - L3 segment: Total weight, Total pieces (lading quantity), Invoice total fallback
    - L11 / N9 segments: PRO and BOL fallback references
    """
    if not raw_content or not raw_content.strip():
        raise ValueError("EDI 210 payload is empty")

    segments = tokenize_x12(raw_content)
    if not segments:
        raise ValueError("Failed to parse any segments from EDI 210 payload")

    # Validate Transaction Set ST*210
    st_seg = find_first_segment(segments, "ST")
    if st_seg and st_seg.get(1) and st_seg.get(1) != "210":
        raise ValueError(f"Expected EDI transaction set '210', found '{st_seg.get(1)}'")

    # Extract B3 segment (Mandatory for 210)
    b3_seg = find_first_segment(segments, "B3")
    if not b3_seg:
        raise ValueError("Missing required B3 segment in EDI 210 message")

    # Extract invoice number & BOL from B3
    # Standard formats:
    # 1. B3*<InvoiceNo>*<BOLNo>**<PayMethod>*<Date>*<Amount>*...
    # 2. B3*<ShipmentQualifier>*<InvoiceNo>*<BOLNo>*<PayMethod>**<Date>*<Amount>*...
    invoice_number = ""
    bol_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    invoice_total = 0.0

    b3_1 = b3_seg.get(1)
    b3_2 = b3_seg.get(2)
    b3_3 = b3_seg.get(3)

    if len(b3_1) > 2 or not b3_2:
        invoice_number = b3_1
        if b3_2:
            bol_number = b3_2
    else:
        # b3_1 was a single-char qualifier like "B" or "O"
        invoice_number = b3_2
        if b3_3:
            bol_number = b3_3

    # Scan B3 elements for date and amount
    # In B3: Date is typically element 5 or 6; Net Amount is typically element 6 or 7
    for idx in range(3, len(b3_seg.elements)):
        elem = b3_seg.get(idx)
        if not elem:
            continue
        digits_only = re.sub(r"\D", "", elem)
        # Check for 8-digit or 6-digit date candidate
        if not invoice_date and len(digits_only) in (6, 8) and (digits_only.startswith("20") or digits_only.startswith("19") or len(digits_only) == 6):
            dt_cand = _parse_edi_date(elem)
            if dt_cand:
                invoice_date = dt_cand
                continue
        # Check for amount candidate
        if invoice_total == 0.0 and (re.match(r"^\d+\.\d+$", elem) or (elem.isdigit() and len(elem) >= 3)):
            invoice_total = _parse_edi_amount(elem)

    # Reference segments fallback (L11, N9)
    pro_number: Optional[str] = None
    ref_segments = find_segments(segments, "L11") + find_segments(segments, "N9")
    for ref in ref_segments:
        ref_val = ref.get(1)
        qualifier = ref.get(2).upper()
        if qualifier in ("CN", "PR", "PRO") and not pro_number:
            pro_number = ref_val
        elif qualifier in ("BM", "BOL", "BL") and not bol_number:
            bol_number = ref_val
        elif qualifier in ("IV", "IN", "OI") and not invoice_number:
            invoice_number = ref_val

    # B10 segment fallback if present
    b10_seg = find_first_segment(segments, "B10")
    if b10_seg:
        if not pro_number and b10_seg.get(1):
            pro_number = b10_seg.get(1)
        if not bol_number and b10_seg.get(2):
            bol_number = b10_seg.get(2)

    # N1 segments: Shipper & Consignee
    shipper_name: Optional[str] = None
    consignee_name: Optional[str] = None
    n1_segments = find_segments(segments, "N1")
    for n1 in n1_segments:
        entity_id = n1.get(1).upper()
        entity_name = n1.get(2)
        if entity_id in ("SH", "SF", "SU") and not shipper_name:
            shipper_name = entity_name
        elif entity_id in ("CN", "ST", "RE", "C1") and not consignee_name:
            consignee_name = entity_name

    # L3 segment: Weight, Total Pieces, Total Amount fallback
    weight = 0.0
    total_pieces = 0
    l3_seg = find_first_segment(segments, "L3")
    if l3_seg:
        if l3_seg.get(1):
            weight = _parse_edi_weight(l3_seg.get(1))
        # L3-05 is charge / total amount
        if invoice_total == 0.0 and l3_seg.get(5):
            invoice_total = _parse_edi_amount(l3_seg.get(5))
        # L3-11 is lading quantity / total pieces
        if l3_seg.get(11):
            total_pieces = _parse_edi_pieces(l3_seg.get(11))
        else:
            # Check other elements in L3 for integer piece count
            for idx in range(8, len(l3_seg.elements)):
                val = l3_seg.get(idx)
                if val.isdigit() and int(val) > 0:
                    total_pieces = int(val)
                    break

    if not invoice_number:
        raise ValueError("Missing required invoice number in B3 segment of EDI 210 message")

    return EDI210ParseResult(
        transaction_set="210",
        invoice_number=invoice_number,
        bol_number=bol_number,
        pro_number=pro_number,
        invoice_date=invoice_date,
        invoice_total=invoice_total,
        weight=weight,
        total_pieces=total_pieces,
        consignee_name=consignee_name,
        shipper_name=shipper_name,
    )
