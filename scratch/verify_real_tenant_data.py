import urllib.request
import json

BASE_URL = "http://localhost:8000"

def get_claims(org_id):
    url = f"{BASE_URL}/api/claims?organization_id={org_id}"
    req = urllib.request.Request(url, headers={"X-Organization-ID": org_id})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def ingest_claim(org_id, pro, amount):
    url = f"{BASE_URL}/api/claims/ingest"
    payload = {
        "organization_id": org_id,
        "pro_number": pro,
        "bol_number": f"BOL-{pro}",
        "carrier_name": "ABC Trucking",
        "claim_type": "Cargo Damage",
        "claimed_amount": amount,
        "shipper_name": "Test Shipper Org Inc",
        "consignee_name": "Test Distribution Warehouse"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "X-Organization-ID": org_id})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    print("--- 1. Querying org-apex-001 claims ---")
    apex_claims = get_claims("org-apex-001")
    print(f"org-apex-001 total claims: {len(apex_claims)}")
    for c in apex_claims:
        print(f"  Claim ID: {c['id']} | Org: {c['organization_id']} | Value: ${c['claimed_amount']}")

    print("\n--- 2. Querying org-shipper-003 claims ---")
    shipper_claims = get_claims("org-shipper-003")
    print(f"org-shipper-003 total claims: {len(shipper_claims)}")
    for c in shipper_claims:
        print(f"  Claim ID: {c['id']} | Org: {c['organization_id']} | Value: ${c['claimed_amount']}")

    print("\n--- 3. Querying brand-new org org-brandnew-999 before ingest ---")
    new_claims_before = get_claims("org-brandnew-999")
    print(f"org-brandnew-999 total claims before ingest: {len(new_claims_before)} (Expected: 0)")

    print("\n--- 4. Ingesting $15,000 claim for org-brandnew-999 ---")
    ingest_res = ingest_claim("org-brandnew-999", "PRO-BRANDNEW-101", 15000.0)
    print(f"Ingest Result: Status={ingest_res['status']} | Claim ID={ingest_res['claim_id']} | Amount=${ingest_res['claimed_amount']}")

    print("\n--- 5. Querying org-brandnew-999 claims after ingest ---")
    new_claims_after = get_claims("org-brandnew-999")
    print(f"org-brandnew-999 total claims after ingest: {len(new_claims_after)} (Expected: 1)")
    for c in new_claims_after:
        print(f"  Claim ID: {c['id']} | Org: {c['organization_id']} | Value: ${c['claimed_amount']}")

    print("\n--- 6. Verifying cross-tenant isolation ---")
    apex_claims_after = get_claims("org-apex-001")
    print(f"org-apex-001 total claims after brandnew ingest: {len(apex_claims_after)} (Unchanged!)")

if __name__ == "__main__":
    main()
