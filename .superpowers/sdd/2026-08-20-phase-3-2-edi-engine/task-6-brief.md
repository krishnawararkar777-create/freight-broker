# Task 6 Brief: EDI 204/211 Parser & Unified EDIService Integration

**Goal:** Create EDI 204/211 load tender parser and the unified `EDIService` in `apps/api/app/services/edi_service.py`.

**Files:**
- Create: `apps/api/app/parsers/edi/edi_204_211_parser.py`
- Create: `apps/api/app/services/edi_service.py`
- Test: `apps/api/tests/test_edi_service.py`
- Report: `.superpowers/sdd/2026-08-20-phase-3-2-edi-engine/task-6-report.md`

**Global Constraints:**
- Auto-created claims triggered by EDI 214 delivery damage exceptions MUST be in `DRAFT` status (`is_approved_by_human = False`).
- Transaction set auto-detection reads the `ST` header (`ST*214*`, `ST*210*`, `ST*204*`, `ST*211*`).

**Requirements & Output Schema:**
1. `EDI204211ParseResult` Pydantic Model:
   - `transaction_set`: str  # "204" or "211"
   - `shipment_reference`: str
   - `bol_number`: str | None = None
   - `shipper_name`: str | None = None
   - `consignee_name`: str | None = None
   - `origin_city_state`: str | None = None
   - `destination_city_state`: str | None = None
   - `commodity`: str | None = None
   - `nmfc_code`: str | None = None
   - `weight`: float = 0.0
   - `total_pieces`: int = 0
   - `declared_value`: float = 0.0
2. `EDIService.process_edi_payload(raw_content: str, db: Session | None = None)`:
   - Inspects `ST` header segment to identify transaction type.
   - Routes payload to `parse_edi_214`, `parse_edi_210`, or `parse_edi_204_211`.
   - On EDI 214 damage exception (`AG`, `SD`), if DB session is provided, updates shipment, logs Carmack deadline, and creates `DRAFT` claim if not already present.

**Steps to Execute (TDD Workflow):**
1. Write failing unit & integration tests in `apps/api/tests/test_edi_service.py`.
2. Run `pytest apps/api/tests/test_edi_service.py -v` using `run_command` (verify FAIL).
3. Implement `edi_204_211_parser.py` and `edi_service.py`.
4. Run `pytest apps/api/tests/test_edi_service.py -v` using `run_command` (verify PASS).
5. Run full test suite `pytest apps/api/tests -v` to ensure 0 regressions.
6. Write task report to `.superpowers/sdd/2026-08-20-phase-3-2-edi-engine/task-6-report.md`.
7. Commit: `git add apps/api/app/parsers/edi/apps/api/app/services/edi_service.py apps/api/tests/test_edi_service.py` and commit with message `feat(edi): add EDI 204/211 load tender parser and unified EDIService engine`.
