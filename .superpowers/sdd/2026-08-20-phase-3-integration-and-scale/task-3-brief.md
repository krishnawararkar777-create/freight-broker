# Task 3 Brief: TMS Webhook Service & Router Endpoint

**Goal:** Create the business logic service `TMSService` and router `POST /api/integrations/tms/{provider}/webhook` in `apps/api/routers/tms.py`.

**Files:**
- Create: `apps/api/app/services/tms_service.py`
- Create: `apps/api/routers/tms.py`
- Modify: `apps/api/main.py`
- Test: `apps/api/tests/test_tms_ingestion.py`
- Report: `.superpowers/sdd/2026-08-20-phase-3-integration-and-scale/task-3-report.md`

**Global Constraints:**
- Server-side human approval guard MUST NOT be bypassed. Any claim auto-created via webhook MUST be in `DRAFT` status (`status = "DRAFT"`, `is_approved_by_human = False`).
- Ingested documents must stream to Supabase S3 bucket `claim-documents` via `storage_service` / `document_service`.

**Requirements & Logic:**
1. `TMSService.process_webhook(provider: str, raw_payload: dict, headers: dict, db: Session)`:
   - Resolves provider adapter via `TMSAdapterFactory` (e.g. `mcleod` -> `McLeodMockAdapter`).
   - Verifies webhook signature (`401 Unauthorized` if invalid).
   - Parses normalized shipment. Upserts into `shipments` table (matching on `external_reference` or `bol_number`).
   - Checks `is_claim_trigger_event(raw_payload)`:
     - If `is_trigger` is True, checks if a claim already exists for this `shipment_id`.
     - If no claim exists, creates a new `claims` record in **`DRAFT` status** (`claimed_amount = shipment.declared_value`, `claim_type = "CARGO_DAMAGE"`).
   - Auto-fetches attached documents via `adapter.fetch_document_bytes()`, streams them to storage, creates `documents` DB records, and calls `extraction_service.extract()`.
2. Router `POST /api/integrations/tms/{provider}/webhook`:
   - Fast API router receiving raw JSON payload & headers. Calls `TMSService.process_webhook`.
   - Returns `{"status": "processed", "shipment_id": "...", "claim_id": "...", "claim_created": True}`.

**Steps to Execute (TDD Workflow):**
1. Write failing integration tests in `apps/api/tests/test_tms_ingestion.py`.
2. Run `pytest apps/api/tests/test_tms_ingestion.py -v` using `run_command` (verify FAIL).
3. Implement `apps/api/app/services/tms_service.py`, `apps/api/routers/tms.py`, and update `apps/api/main.py`.
4. Run `pytest apps/api/tests/test_tms_ingestion.py -v` using `run_command` (verify PASS).
5. Write task report to `.superpowers/sdd/2026-08-20-phase-3-integration-and-scale/task-3-report.md`.
6. Commit: `git add apps/api/app/services/tms_service.py apps/api/routers/tms.py apps/api/main.py apps/api/tests/test_tms_ingestion.py` and commit with message `feat(tms): add universal TMS webhook router and ingestion service`.
