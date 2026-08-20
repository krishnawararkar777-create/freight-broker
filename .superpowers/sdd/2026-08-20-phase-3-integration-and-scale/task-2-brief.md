# Task 2 Brief: McLeod Mock Adapter Implementation (`McLeodMockAdapter`)

**Goal:** Implement `McLeodMockAdapter` in `apps/api/app/integrations/tms/mcleod_mock_adapter.py` conforming to `TMSAdapter`.

**Files:**
- Create: `apps/api/app/integrations/tms/mcleod_mock_adapter.py`
- Test: `apps/api/tests/test_mcleod_mock_adapter.py`
- Report: `.superpowers/sdd/2026-08-20-phase-3-integration-and-scale/task-2-report.md`

**Global Constraints:**
- Inherit from `TMSAdapter` (`apps/api/app/integrations/tms/base.py`).
- Implement signature verification (HMAC SHA-256 validation if secret present, or simple token check).
- Parse McLeod LoadMaster payload JSON structure:
  - `order_number` / `bol_number` / `pro_number`
  - `carrier_name`, `shipper`, `consignee`, `origin`, `destination`
  - `declared_value`, `commodity`, `quantity`, `weight`
  - `status`: map `DELIVERED_DAMAGED`, `SHORTAGE_REPORTED`, `CLAIM_PENDING` as claim trigger events returning `(True, status)`.
  - `documents` list: extract download URLs into `NormalizedDocumentRef`.
  - `fetch_document_bytes`: mock binary fetch returning synthetic PDF bytes if URL is mock.

**Steps to Execute (TDD Workflow):**
1. Write failing unit tests in `apps/api/tests/test_mcleod_mock_adapter.py`.
2. Run `pytest apps/api/tests/test_mcleod_mock_adapter.py -v` using `run_command` (verify FAIL).
3. Implement `apps/api/app/integrations/tms/mcleod_mock_adapter.py`.
4. Run `pytest apps/api/tests/test_mcleod_mock_adapter.py -v` using `run_command` (verify PASS).
5. Write task report to `.superpowers/sdd/2026-08-20-phase-3-integration-and-scale/task-2-report.md`.
6. Commit: `git add apps/api/app/integrations/tms/mcleod_mock_adapter.py apps/api/tests/test_mcleod_mock_adapter.py` and commit with message `feat(tms): implement McLeodMockAdapter for McLeod LoadMaster JSON webhooks`.
