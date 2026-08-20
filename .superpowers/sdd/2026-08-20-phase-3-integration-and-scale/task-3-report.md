# Task 3 Completion Report: TMS Webhook Service & Router Endpoint

**Date:** 2026-08-20  
**Status:** COMPLETED  
**Scope:** Phase 3.1 — TMS Ingestion Engine (Task 3)

---

## 1. Overview & Objectives
The goal of Task 3 was to implement the universal `TMSService` business logic service, `TMSAdapterFactory`, and the FastAPI router endpoint `POST /api/integrations/tms/{provider}/webhook`.

Key requirements enforced:
1. **Server-Side Human Approval Guard**: Any claim auto-created through a TMS webhook event is strictly initialized in `status = "DRAFT"` and `is_approved_by_human = False`. It cannot bypass human operator review.
2. **Provider Resolution**: Dynamic adapter dispatch via `TMSAdapterFactory` with support for `mcleod` (and extensible registration).
3. **Cryptographic Verification**: Webhook HMAC signature verification returning `401 Unauthorized` on mismatch.
4. **Shipment & Carrier Upserting**: Automatic carrier matching/creation and idempotent shipment record upsert matching on `external_reference` or `bol_number`.
5. **Carmack Deadline Calculation**: Automatic calculation of 9-calendar-month Carmack statutory filing deadlines and 5-business-day concealed damage notice deadlines upon claim creation.
6. **Document Stream & Extraction**: Auto-fetching binary payload for document references attached to the webhook, storing them via `DocumentService` / `StorageService`, and passing them to `ExtractionService` for fact & evidence extraction.

---

## 2. Changes Implemented

### A. TMS Service & Adapter Factory (`apps/api/app/services/tms_service.py`)
- Implemented `TMSAdapterFactory` supporting adapter registration and lookup with case-insensitive provider names.
- Implemented `TMSService.process_webhook(provider, raw_payload, headers, payload_bytes, db, org_id)`:
  - Validates webhook signature against the resolved adapter.
  - Normalizes shipment data and upserts `shipments` table.
  - Evaluates `is_claim_trigger_event(raw_payload)`. If true and no claim exists for shipment, creates a new `Claim` with:
    - `status = "DRAFT"`
    - `is_approved_by_human = False`
    - `claimed_amount = shipment.declared_value`
    - `human_threshold_triggered = (claimed_amount >= customer_policy.high_value_threshold)`
    - `deadline_at` computed using Carmack 9 calendar months (`relativedelta(months=9)`).
    - `concealed_deadline_at` computed using 5 business days.
  - Ingests all attached documents into `documents` table and runs `extraction_service.extract_and_persist(...)`.
  - Records immutable `AuditEvent` entries for shipment ingestion and claim creation.

### B. FastAPI Router (`apps/api/routers/tms.py`)
- Created `POST /api/integrations/tms/{provider}/webhook` endpoint.
- Parses request body and headers, passing execution to `tms_service.process_webhook`.
- Returns standard response shape:
  ```json
  {
    "status": "processed",
    "shipment_id": "shp-...",
    "claim_id": "clm-...",
    "claim_created": true,
    "documents_ingested": 2
  }
  ```

### C. Application Root (`apps/api/main.py`)
- Registered `tms_router` into the FastAPI application.

### D. Mock Adapter Enhancement (`apps/api/app/integrations/tms/mcleod_mock_adapter.py`)
- Enhanced `fetch_document_bytes` to supply extractable text fields (BOL, Carrier, Declared Value) for end-to-end extraction pipeline verification.

### E. Integration Tests (`apps/api/tests/test_tms_ingestion.py`)
- Implemented 12 comprehensive integration tests covering:
  - Adapter factory retrieval and custom registration
  - Webhook HMAC signature verification failure (401 Unauthorized)
  - Non-trigger event (shipment upsert only, no claim created)
  - Claim trigger event (auto-creates claim in `DRAFT` status with `is_approved_by_human = False`)
  - Webhook claim creation idempotency (no duplicate claim creation)
  - Attached document ingestion and automated fact/evidence extraction
  - Router HTTP endpoints (200 OK success, 401 Unauthorized, 400 Bad Request on unknown provider)

---

## 3. Test Verification Results

### Unit & Integration Suite (`apps/api/tests/test_tms_ingestion.py`)
```
collected 12 items
apps/api/tests/test_tms_ingestion.py::test_adapter_factory_returns_mcleod_adapter PASSED
apps/api/tests/test_tms_ingestion.py::test_adapter_factory_unsupported_provider PASSED
apps/api/tests/test_tms_ingestion.py::test_adapter_factory_custom_registration PASSED
apps/api/tests/test_tms_ingestion.py::test_tms_service_signature_verification_failure PASSED
apps/api/tests/test_tms_ingestion.py::test_tms_service_non_trigger_event_upserts_shipment_only PASSED
apps/api/tests/test_tms_ingestion.py::test_tms_service_claim_trigger_auto_creates_draft_claim PASSED
apps/api/tests/test_tms_ingestion.py::test_tms_service_idempotency_claim_creation PASSED
apps/api/tests/test_tms_ingestion.py::test_tms_service_document_auto_ingestion_and_extraction PASSED
apps/api/tests/test_router_tms_webhook_endpoint_success PASSED
apps/api/tests/test_router_tms_webhook_endpoint_invalid_signature PASSED
apps/api/tests/test_router_tms_webhook_endpoint_unsupported_provider PASSED
apps/api/tests/test_router_tms_webhook_endpoint_non_trigger PASSED
============================= 12 passed in 6.50s ==============================
```

### Full Test Suite Run (`pytest apps/api/tests -v`)
```
======================== 73 passed in 70.94s (0:01:10) ========================
```
- **Total Tests Passing**: 73 / 73 (100%)
- **Regressions**: 0
