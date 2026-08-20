import pytest
from datetime import datetime
from app.parsers.edi.edi_210_parser import parse_edi_210, EDI210ParseResult

SAMPLE_EDI_210 = """ISA*00*          *00*          *ZZ*CARRIER        *ZZ*BROKER         *260820*1120*U*00401*000000002*0*P*>~
GS*IM*CARRIER*BROKER*20260820*1120*2*X*004010~
ST*210*0002~
B3*210123*BOL98765**PP*20260820*2000000**20260820*035~
N1*CN*CONSIGNEE NAME~
L3*4000*G***2000000*****100~
SE*6*0002~
GE*1*2~
IEA*1*000000002~"""

SAMPLE_EDI_210_FULL = """ISA*00*          *00*          *ZZ*EXPRESSLINE    *ZZ*BROKERHUB      *260820*1530*U*00401*000000101*0*P*>~
GS*IM*EXPRESSLINE*BROKERHUB*20260820*1530*101*X*004010~
ST*210*0101~
B3*INV-889900*BOL-445566**PP*20260820*1500000**20260820*035~
N1*SH*APEX MANUFACTURING LLC~
N1*CN*WESTERN DISTRIBUTION INC~
L11*PRO-778899*CN~
L3*25000*G***1500000*****250~
SE*7*0101~
GE*1*101~
IEA*1*000000101~"""

SAMPLE_EDI_210_DECIMAL_AMOUNT = """ST*210*0202~
B3*INV-3344*BOL-1122**PP*20260820*12500.50~
N1*SH*SUPPLIER CO~
N1*CN*BUYER CO~
L3*1200*G***12500.50*****50~
SE*5*0202~"""


def test_parse_edi_210_invoice():
    """Verify EDI 210 parser extracts invoice fields and damage valuation math."""
    result = parse_edi_210(SAMPLE_EDI_210)
    
    assert isinstance(result, EDI210ParseResult)
    assert result.transaction_set == "210"
    assert result.invoice_number == "210123"
    assert result.bol_number == "BOL98765"
    assert result.invoice_total == 20000.00
    assert result.weight == 4000.0
    assert result.total_pieces == 100
    assert result.consignee_name == "CONSIGNEE NAME"
    assert result.invoice_date == datetime(2026, 8, 20, 0, 0)
    
    # Ratio math test: 40 damaged out of 100 pieces on $20,000 invoice = $8,000.00
    claimed = result.calculate_damaged_amount(damaged_qty=40)
    assert claimed == 8000.00


def test_parse_edi_210_full_shipper_consignee_pro():
    """Verify extraction of shipper, consignee, and PRO reference numbers."""
    result = parse_edi_210(SAMPLE_EDI_210_FULL)
    
    assert result.invoice_number == "INV-889900"
    assert result.bol_number == "BOL-445566"
    assert result.pro_number == "PRO-778899"
    assert result.shipper_name == "APEX MANUFACTURING LLC"
    assert result.consignee_name == "WESTERN DISTRIBUTION INC"
    assert result.invoice_total == 15000.00
    assert result.weight == 25000.0
    assert result.total_pieces == 250
    
    # 50 damaged out of 250 pieces on $15,000 invoice = $3,000.00
    claimed = result.calculate_damaged_amount(damaged_qty=50)
    assert claimed == 3000.00


def test_parse_edi_210_decimal_amount_handling():
    """Verify explicit decimal strings in B3/L3 are parsed correctly."""
    result = parse_edi_210(SAMPLE_EDI_210_DECIMAL_AMOUNT)
    assert result.invoice_number == "INV-3344"
    assert result.bol_number == "BOL-1122"
    assert result.invoice_total == 12500.50
    assert result.weight == 1200.0
    assert result.total_pieces == 50
    assert result.shipper_name == "SUPPLIER CO"
    assert result.consignee_name == "BUYER CO"


def test_calculate_damaged_amount_boundaries():
    """Verify damage ratio valuation edge cases and rounding."""
    result = EDI210ParseResult(
        transaction_set="210",
        invoice_number="INV-TEST",
        invoice_total=10000.00,
        weight=500.0,
        total_pieces=3,
    )
    
    # 1 out of 3 damaged -> 10000 / 3 = 3333.333... -> 3333.33
    assert result.calculate_damaged_amount(1) == 3333.33
    # 0 damaged -> 0.00
    assert result.calculate_damaged_amount(0) == 0.00
    # Negative damaged -> 0.00
    assert result.calculate_damaged_amount(-5) == 0.00
    # All damaged -> 10000.00
    assert result.calculate_damaged_amount(3) == 10000.00
    # More damaged than total -> capped at invoice total 10000.00
    assert result.calculate_damaged_amount(10) == 10000.00


def test_calculate_damaged_amount_zero_pieces():
    """Verify fallback when total pieces is zero."""
    result = EDI210ParseResult(
        transaction_set="210",
        invoice_number="INV-ZERO",
        invoice_total=5000.00,
        weight=0.0,
        total_pieces=0,
    )
    # When total_pieces is 0, full invoice fallback if damaged_qty > 0
    assert result.calculate_damaged_amount(1) == 5000.00
    assert result.calculate_damaged_amount(0) == 0.00


def test_parse_edi_210_empty_payload_raises():
    """Verify ValueError when payload is empty."""
    with pytest.raises(ValueError, match="empty"):
        parse_edi_210("")


def test_parse_edi_210_missing_b3_raises():
    """Verify ValueError when B3 segment is missing."""
    invalid_edi = """ST*210*0001~
    N1*CN*TEST~
    SE*2*0001~"""
    with pytest.raises(ValueError, match="B3"):
        parse_edi_210(invalid_edi)


def test_parse_edi_210_wrong_transaction_set_raises():
    """Verify ValueError when transaction set is not 210."""
    invalid_edi = """ST*214*0001~
    B3*210123*BOL98765**PP*20260820*2000000~
    SE*2*0001~"""
    with pytest.raises(ValueError, match="210"):
        parse_edi_210(invalid_edi)
