import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.parsers.edi.edi_214_parser import parse_edi_214, EDI214ParseResult
from app.parsers.edi.x12_segment_parser import tokenize_x12, X12Segment

# Sample EDI 214 Payload with Damaged Status (AG)
SAMPLE_EDI_214_DAMAGED = """
ISA*00*          *00*          *02*FXFE           *01*RECEIVER       *260820*1430*U*00401*000000001*0*P*:~
GS*QM*FXFE*RECEIVER*20260820*1430*1*X*004010~
ST*214*0001~
B10*PRO-998877*BOL-112233*FXFE~
L11*PO-445566*PO~
AT7*AG*DM***20260820*1430*LT~
MS1*CHICAGO*IL*USA~
SE*6*0001~
GE*1*1~
IEA*1*000000001~
"""

SAMPLE_EDI_214_SHORTAGE = """
ISA*00*          *00*          *02*ODFL           *01*RECEIVER       *260820*0900*U*00401*000000002*0*P*:~
GS*QM*ODFL*RECEIVER*20260820*0900*2*X*004010~
ST*214*0002~
B10*ODFL-771122*BOL-554433*ODFL~
AT7*SD*SH***20260820*0900*LT~
SE*4*0002~
GE*1*2~
IEA*1*000000002~
"""

SAMPLE_EDI_214_REFUSED = """
ST*214*0003~
B10*SAIA-332211*BOL-998811*SAIA~
AT7*A7*RF***260820*1115*LT~
SE*3*0003~
"""

SAMPLE_EDI_214_EXCEPTION = """
ST*214*0004~
B10*ABFS-554433*BOL-332244*ABFS~
AT7*CD*EX***20260820*1600*LT~
SE*3*0004~
"""

SAMPLE_EDI_214_CLEAN_DELIVERY = """
ST*214*0005~
B10*RDFS-123456*BOL-654321*RDFS~
AT7*D1*NS***20260820*1000*LT~
SE*3*0005~
"""

SAMPLE_EDI_214_IN_TRANSIT = """
ST*214*0006~
B10*FXFE-887766*BOL-443322*FXFE~
AT7*X6*NS***20260820*0800*LT~
SE*3*0006~
"""

def test_x12_tokenizer_basic():
    """Verify X12 tokenizer splits segments and elements correctly."""
    segments = tokenize_x12(SAMPLE_EDI_214_DAMAGED)
    assert len(segments) > 0
    st_seg = next(s for s in segments if s.tag == "ST")
    assert st_seg.elements[1] == "214"
    
    b10_seg = next(s for s in segments if s.tag == "B10")
    assert b10_seg.elements[1] == "PRO-998877"
    assert b10_seg.elements[2] == "BOL-112233"
    assert b10_seg.elements[3] == "FXFE"

def test_edi_214_damaged_status_carmack_calculation():
    """
    TDD Test: Verify EDI 214 parser extracts PRO, BOL, SCAC, damage exception status,
    and computes Carmack 9-month statutory deadline and 5-day concealed damage deadline.
    """
    result = parse_edi_214(SAMPLE_EDI_214_DAMAGED)
    
    assert isinstance(result, EDI214ParseResult)
    assert result.transaction_set == "214"
    assert result.pro_number == "PRO-998877"
    assert result.bol_number == "BOL-112233"
    assert result.carrier_scac == "FXFE"
    assert result.status_code == "AG"
    assert "Damage" in result.status_description
    assert result.is_damage_exception is True
    
    # Expected delivery timestamp: 2026-08-20 14:30:00
    expected_delivery = datetime(2026, 8, 20, 14, 30)
    assert result.delivery_at == expected_delivery
    
    # Carmack 9-month statutory deadline: 2026-08-20 + 9 months = 2027-05-20
    expected_carmack = expected_delivery + relativedelta(months=9)
    assert result.carmack_deadline_at == expected_carmack
    assert result.carmack_deadline_at == datetime(2027, 5, 20, 14, 30)
    
    # Concealed damage deadline: 2026-08-20 + 5 days = 2026-08-25
    expected_concealed = expected_delivery + timedelta(days=5)
    assert result.concealed_deadline_at == expected_concealed
    assert result.concealed_deadline_at == datetime(2026, 8, 25, 14, 30)

def test_edi_214_shortage_exception():
    """Verify shortage status code (SD) flags damage exception."""
    result = parse_edi_214(SAMPLE_EDI_214_SHORTAGE)
    assert result.status_code == "SD"
    assert result.is_damage_exception is True
    assert "Shortage" in result.status_description
    assert result.pro_number == "ODFL-771122"
    assert result.bol_number == "BOL-554433"
    assert result.carrier_scac == "ODFL"

def test_edi_214_refused_exception_6digit_date():
    """Verify refused status code (A7) and 6-digit date (YYMMDD) handling."""
    result = parse_edi_214(SAMPLE_EDI_214_REFUSED)
    assert result.status_code == "A7"
    assert result.is_damage_exception is True
    assert "Refused" in result.status_description
    assert result.delivery_at == datetime(2026, 8, 20, 11, 15)
    assert result.carmack_deadline_at == datetime(2027, 5, 20, 11, 15)
    assert result.concealed_deadline_at == datetime(2026, 8, 25, 11, 15)

def test_edi_214_carrier_exception():
    """Verify carrier exception status code (CD) flags damage exception."""
    result = parse_edi_214(SAMPLE_EDI_214_EXCEPTION)
    assert result.status_code == "CD"
    assert result.is_damage_exception is True
    assert "Exception" in result.status_description

def test_edi_214_clean_delivery_not_exception():
    """Verify clean delivery (D1) does NOT flag damage exception."""
    result = parse_edi_214(SAMPLE_EDI_214_CLEAN_DELIVERY)
    assert result.status_code == "D1"
    assert result.is_damage_exception is False
    assert "Delivered" in result.status_description
    assert result.delivery_at == datetime(2026, 8, 20, 10, 0)
    assert result.carmack_deadline_at == datetime(2027, 5, 20, 10, 0)

def test_edi_214_in_transit_not_exception():
    """Verify in-transit status (X6) does NOT flag damage exception."""
    result = parse_edi_214(SAMPLE_EDI_214_IN_TRANSIT)
    assert result.status_code == "X6"
    assert result.is_damage_exception is False
    assert "En Route" in result.status_description or "Transit" in result.status_description

def test_carmack_month_end_relativedelta_precision():
    """
    Verify Carmack statutory calculation uses dateutil.relativedelta(months=9)
    which accurately handles month end rollovers (e.g. May 31 -> Feb 28)
    unlike inaccurate 270-day approximations.
    """
    raw_payload = """
    ST*214*0099~
    B10*PRO-MONTH-END*BOL-999*FXFE~
    AT7*AG*DM***20260531*1200*LT~
    SE*3*0099~
    """
    result = parse_edi_214(raw_payload)
    assert result.delivery_at == datetime(2026, 5, 31, 12, 0)
    # May 31, 2026 + 9 months = Feb 28, 2027
    assert result.carmack_deadline_at == datetime(2027, 2, 28, 12, 0)
    # A naive 270-day math would yield Feb 25, 2027 — verify exact relativedelta month precision
    naive_270_days = datetime(2026, 5, 31, 12, 0) + timedelta(days=270)
    assert result.carmack_deadline_at != naive_270_days

def test_edi_214_missing_b10_raises_error():
    """Verify ValueError when B10 segment is missing."""
    invalid_payload = """
    ST*214*0001~
    AT7*AG*DM***20260820*1430*LT~
    SE*2*0001~
    """
    with pytest.raises(ValueError, match="B10"):
        parse_edi_214(invalid_payload)

def test_edi_214_missing_at7_raises_error():
    """Verify ValueError when AT7 segment is missing."""
    invalid_payload = """
    ST*214*0001~
    B10*PRO-998877*BOL-112233*FXFE~
    SE*2*0001~
    """
    with pytest.raises(ValueError, match="AT7"):
        parse_edi_214(invalid_payload)
