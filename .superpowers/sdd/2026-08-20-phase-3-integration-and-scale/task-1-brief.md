# Task 1 Brief: Core TMSAdapter Abstract Interface & Normalized Pydantic Schemas

**Goal:** Create the abstract `TMSAdapter` base class and Pydantic normalization schemas in `apps/api/app/integrations/tms/base.py`.

**Files:**
- Create: `apps/api/app/integrations/tms/base.py`
- Test: `apps/api/tests/test_tms_adapter_base.py`
- Report: `.superpowers/sdd/2026-08-20-phase-3-integration-and-scale/task-1-report.md`

**Global Constraints:**
- Strict Pydantic v2 validation.
- Every extraction/normalization model must maintain provenance and type hints.

**Requirements & Interface Definitions:**
1. `NormalizedShipmentData` Pydantic model:
   - `external_reference`: str
   - `bol_number`: str
   - `pro_number`: str | None = None
   - `carrier_canonical_name`: str
   - `shipper_name`: str
   - `consignee_name`: str
   - `origin`: str
   - `destination`: str
   - `pickup_at`: str | None = None
   - `delivery_at`: str | None = None
   - `declared_value`: float
   - `currency`: str = "USD"
   - `commodity`: str
   - `quantity`: int
   - `weight`: float
   - `raw_status`: str
2. `NormalizedDocumentRef` Pydantic model:
   - `document_type`: str (e.g. "BOL", "POD", "COMMERCIAL_INVOICE")
   - `filename`: str
   - `download_url`: str
   - `mime_type`: str = "application/pdf"
3. `TMSAdapter` Abstract Base Class (inherits from `abc.ABC`):
   - `@abstractmethod verify_webhook_signature(self, payload_bytes: bytes, headers: dict) -> bool`
   - `@abstractmethod parse_webhook_shipment(self, raw_payload: dict) -> NormalizedShipmentData`
   - `@abstractmethod extract_document_references(self, raw_payload: dict) -> list[NormalizedDocumentRef]`
   - `@abstractmethod is_claim_trigger_event(self, raw_payload: dict) -> tuple[bool, str | None]`
   - `@abstractmethod async fetch_document_bytes(self, doc_ref: NormalizedDocumentRef) -> bytes`

**Steps to Execute (TDD Workflow):**
1. Write failing test in `apps/api/tests/test_tms_adapter_base.py` verifying schema instantiation and default fields.
2. Run test: `pytest apps/api/tests/test_tms_adapter_base.py -v` (verify FAIL).
3. Implement `apps/api/app/integrations/tms/base.py`.
4. Run test: `pytest apps/api/tests/test_tms_adapter_base.py -v` (verify PASS).
5. Write task report to `.superpowers/sdd/2026-08-20-phase-3-integration-and-scale/task-1-report.md`.
6. Commit: `git add apps/api/app/integrations/tms/base.py apps/api/tests/test_tms_adapter_base.py` and commit with message `feat(tms): add base TMSAdapter interface and normalized schemas`.
