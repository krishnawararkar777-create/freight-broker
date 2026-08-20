"""
EDI 214 Carrier Shipment Status Parser.
Extracts shipment delivery events, exception codes, and calculates
Carmack Amendment (9-month statutory) and concealed damage (5-day) filing deadlines.
"""
from datetime import datetime, timedelta
import re
from typing import Optional
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field

from app.parsers.edi.x12_segment_parser import (
    tokenize_x12,
    find_segments,
    find_first_segment,
    X12Segment,
)

# Standard EDI 214 Status Code Map
STATUS_CODE_DESCRIPTIONS = {
    "AG": "Damaged - Delivered with Damage",
    "SD": "Shortage - Delivered with Shortage",
    "CD": "Carrier Exception - Delivered with Exception",
    "A7": "Refused Delivery",
    "D1": "Completed Unloading / Delivered",
    "X6": "En Route to Delivery Location",
    "X1": "Arrived at Destination Terminal",
    "X3": "Arrived at Pickup Location",
    "AF": "Departed Carrier Terminal",
    "P1": "Departed Pickup Location",
    "AB": "Delivery Appointment Scheduled",
    "AV": "Available for Delivery",
    "CP": "Completed Loading",
    "NS": "Normal Status / No Exception",
    "NA": "Normal Activity",
    "CL": "Complete",
    "O1": "Out for Delivery",
    "PR": "Preliminary Notification",
    "X4": "Arrived at Terminal",
}

# Status codes indicating damage / shortage / refusal exception
DAMAGE_EXCEPTION_CODES = {"AG", "SD", "CD", "A7"}


class EDI214ParseResult(BaseModel):
    """Structured result from parsing an EDI 214 Shipment Status message."""
    transaction_set: str = Field(default="214", description="EDI transaction set identifier")
    pro_number: str = Field(description="Carrier PRO / tracking reference number")
    bol_number: Optional[str] = Field(default=None, description="Bill of Lading number")
    carrier_scac: Optional[str] = Field(default=None, description="Standard Carrier Alpha Code")
    status_code: str = Field(description="EDI 214 shipment status code (e.g. AG, SD, CD, A7, D1, X6)")
    status_description: str = Field(description="Human readable description of the status code")
    is_damage_exception: bool = Field(description="Whether status indicates damage, shortage, refusal or exception")
    delivery_at: datetime = Field(description="Timestamp of the status/delivery event")
    carmack_deadline_at: datetime = Field(description="Carmack statutory 9-month claim deadline")
    concealed_deadline_at: datetime = Field(description="Concealed damage 5-day claim deadline")


def _parse_edi_date_time(date_str: str, time_str: str = "") -> datetime:
    """
    Parse EDI date (YYYYMMDD or YYMMDD) and time (HHMM or HHMMSS) strings
    into a Python datetime object.
    """
    date_clean = re.sub(r"\D", "", date_str.strip())
    if len(date_clean) == 8:
        base_dt = datetime.strptime(date_clean, "%Y%m%d")
    elif len(date_clean) == 6:
        base_dt = datetime.strptime(date_clean, "%y%m%d")
    else:
        raise ValueError(f"Invalid EDI date format '{date_str}'. Expected YYYYMMDD or YYMMDD.")

    time_clean = re.sub(r"\D", "", time_str.strip()) if time_str else ""
    hour, minute, second = 0, 0, 0
    if len(time_clean) >= 4:
        hour = int(time_clean[0:2])
        minute = int(time_clean[2:4])
        if len(time_clean) >= 6:
            second = int(time_clean[4:6])

    return datetime(base_dt.year, base_dt.month, base_dt.day, hour, minute, second)


def _extract_at7_datetime(at7: X12Segment) -> tuple[str, str]:
    """
    Extract date string and time string from AT7 segment.
    Standard AT7: AT7*<Status>*<Reason>*<ApptStatus>*<ApptReason>*<Date>*<Time>*<TimeCode>
    """
    # Check standard AT7-05 and AT7-06 first
    date_cand = at7.get(5)
    time_cand = at7.get(6)

    if date_cand and len(re.sub(r"\D", "", date_cand)) in (6, 8):
        return date_cand, time_cand

    # Fallback: scan all elements for 6 or 8 digit numeric string
    for idx, elem in enumerate(at7.elements[1:], start=1):
        clean_elem = re.sub(r"\D", "", elem)
        if len(clean_elem) in (6, 8) and idx >= 3:
            date_cand = elem
            time_cand = at7.get(idx + 1)
            return date_cand, time_cand

    raise ValueError(f"Unable to locate valid date in AT7 segment: {at7}")


def parse_edi_214(raw_content: str) -> EDI214ParseResult:
    """
    Parse an EDI 214 Transportation Carrier Shipment Status Message.
    
    Extracts:
    - B10 segment: PRO number, BOL number, Carrier SCAC
    - AT7 segment: Status code, Event Date & Time
    - Computes Carmack statutory deadline using dateutil.relativedelta(months=9)
    - Computes concealed damage deadline using timedelta(days=5)
    """
    if not raw_content or not raw_content.strip():
        raise ValueError("EDI 214 payload is empty")

    segments = tokenize_x12(raw_content)
    if not segments:
        raise ValueError("Failed to parse any segments from EDI 214 payload")

    # Validate Transaction Set ST*214
    st_seg = find_first_segment(segments, "ST")
    if st_seg and st_seg.get(1) and st_seg.get(1) != "214":
        raise ValueError(f"Expected EDI transaction set '214', found '{st_seg.get(1)}'")

    # Extract B10 segment (Mandatory for 214)
    b10_seg = find_first_segment(segments, "B10")
    if not b10_seg:
        raise ValueError("Missing required B10 segment in EDI 214 message")

    pro_number = b10_seg.get(1)
    bol_number = b10_seg.get(2) or None
    carrier_scac = b10_seg.get(3) or None

    # Fallback for references if missing from B10
    l11_segments = find_segments(segments, "L11")
    for l11 in l11_segments:
        ref_val = l11.get(1)
        qualifier = l11.get(2).upper()
        if not pro_number and qualifier in ("CN", "PR", "PRO"):
            pro_number = ref_val
        elif not bol_number and qualifier in ("BM", "BOL", "BL"):
            bol_number = ref_val

    # Fallback for carrier SCAC from ISA/GS if not in B10
    if not carrier_scac:
        isa_seg = find_first_segment(segments, "ISA")
        if isa_seg and isa_seg.get(6):
            carrier_scac = isa_seg.get(6)
        else:
            gs_seg = find_first_segment(segments, "GS")
            if gs_seg and gs_seg.get(2):
                carrier_scac = gs_seg.get(2)

    if not pro_number:
        raise ValueError("Missing PRO number in B10 segment of EDI 214 message")

    # Extract AT7 segment (Mandatory for status)
    at7_seg = find_first_segment(segments, "AT7")
    if not at7_seg:
        raise ValueError("Missing required AT7 segment in EDI 214 message")

    status_code = at7_seg.get(1).upper()
    if not status_code:
        raise ValueError("Missing shipment status code in AT7 segment")

    # Status description and damage exception flag
    status_description = STATUS_CODE_DESCRIPTIONS.get(status_code, f"Shipment Status: {status_code}")
    is_damage_exception = status_code in DAMAGE_EXCEPTION_CODES

    # Date and Time Extraction
    date_str, time_str = _extract_at7_datetime(at7_seg)
    delivery_at = _parse_edi_date_time(date_str, time_str)

    # Statutory Carmack & Concealed Damage Deadlines
    carmack_deadline_at = delivery_at + relativedelta(months=9)
    concealed_deadline_at = delivery_at + timedelta(days=5)

    return EDI214ParseResult(
        transaction_set="214",
        pro_number=pro_number,
        bol_number=bol_number,
        carrier_scac=carrier_scac,
        status_code=status_code,
        status_description=status_description,
        is_damage_exception=is_damage_exception,
        delivery_at=delivery_at,
        carmack_deadline_at=carmack_deadline_at,
        concealed_deadline_at=concealed_deadline_at,
    )
