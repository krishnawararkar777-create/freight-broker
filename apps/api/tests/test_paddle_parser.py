import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_paddle_pdf_parser_bol_extraction():
    """Verifies PaddlePdfParser extracts BOL attributes and bounding box coordinates."""
    from parsers.paddle_parser import PaddlePdfParser

    parser = PaddlePdfParser()
    sample_text = """
    Apex Freight Brokers BILL OF LADING
    BOL NUMBER: BOL-847293
    PO / REFERENCE NUMBER: PO-55210
    PICKUP DATE: 2026-08-10
    PRO NUMBER: PRO-847293
    SHIPPER (FROM): Meridian Electronics Distributors
    CONSIGNEE (TO): Riverside Retail Store #14
    CARRIER: ABC Trucking
    DECLARED VALUE: $8000
    """

    res = parser.parse_text(sample_text, filename="Bill_of_Lading_847293.pdf", document_type="BOL")

    assert res.parser_version == "PaddleOCR v4"
    assert res.status == "processed"
    assert len(res.fields) >= 7

    field_map = {f.field_name: f.value_json["value"] for f in res.fields}
    assert field_map["carrier_name"] == "ABC Trucking"
    assert field_map["bol_number"] == "BOL-847293"
    assert field_map["pro_number"] == "PRO-847293"
    assert field_map["po_number"] == "PO-55210"
    assert field_map["pickup_date"] == "2026-08-10"
    assert field_map["shipper_name"] == "Meridian Electronics Distributors"
    assert field_map["consignee_name"] == "Riverside Retail Store #14"
    assert field_map["declared_value"] == 8000.0

def test_paddle_pdf_parser_pod_extraction():
    """Verifies PaddlePdfParser extracts POD delivery details, line items, and value."""
    from parsers.paddle_parser import PaddlePdfParser

    parser = PaddlePdfParser()
    sample_text = """
    PROOF OF DELIVERY
    REFERENCE: POD-2026-0817-001
    DELIVERY DATE: AUGUST 17, 2026
    FROM: Premier Office Logistics
    TO: Corporate Suites North
    TOTAL DELIVERED VALUE: $1,040.00
    """

    res = parser.parse_text(sample_text, filename="POD_847293.pdf", document_type="POD")

    assert res.parser_version == "PaddleOCR v4"
    field_map = {f.field_name: f.value_json["value"] for f in res.fields}
    assert field_map["delivery_date"] == "AUGUST 17, 2026"
    assert field_map["declared_value"] == 1040.0
