import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

GOLDEN_CLAIM_FIXTURES = [
    {
        "fixture_id": "gold-01",
        "document_type": "BOL",
        "raw_text": "BILL OF LADING\nBOL Number: BOL-847293\nCarrier: ABC Trucking\nPickup Date: 2025-12-10\nDeclared Value: $20,000.00\n",
        "expected_fields": {
            "carrier_name": "ABC Trucking",
            "bol_number": "BOL-847293",
            "pickup_date": "2025-12-10",
            "declared_value": 20000.00
        }
    },
    {
        "fixture_id": "gold-02",
        "document_type": "POD",
        "raw_text": "PROOF OF DELIVERY\nPRO Number: PRO-847293\nDelivery Date: 2025-12-15\nDamaged Qty: 2\nDamage Notes: 2 cartons crushed at rear door\n",
        "expected_fields": {
            "pro_number": "PRO-847293",
            "delivery_date": "2025-12-15",
            "damaged_quantity": 2,
            "damage_description": "2 cartons crushed at rear door"
        }
    }
]

def test_golden_dataset_extraction_accuracy():
    """
    CI Evaluation Suite: Evaluates extraction accuracy and grounding against reference golden fixtures.
    Pass criterion: 100% field precision on reference dataset.
    """
    from parsers.paddle_parser import PaddlePdfParser

    parser = PaddlePdfParser()
    total_expected = 0
    total_correct = 0

    for fixture in GOLDEN_CLAIM_FIXTURES:
        res = parser.parse_text(fixture["raw_text"], filename=f"{fixture['fixture_id']}.pdf", document_type=fixture["document_type"])
        field_map = {f.field_name: f.value_json["value"] for f in res.fields if f.value_json}

        for field_name, expected_val in fixture["expected_fields"].items():
            total_expected += 1
            if field_name in field_map and field_map[field_name] == expected_val:
                total_correct += 1

    accuracy = (total_correct / total_expected) * 100
    assert accuracy == 100.0, f"Golden eval accuracy was {accuracy}%, expected 100%"
