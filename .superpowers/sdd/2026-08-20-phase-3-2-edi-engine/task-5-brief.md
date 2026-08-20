# Task 5 Brief: EDI 210 Freight Details & Invoice Parser

**Goal:** Create the EDI 210 freight invoice parser in `apps/api/app/parsers/edi/edi_210_parser.py`.

**Files:**
- Create: `apps/api/app/parsers/edi/edi_210_parser.py`
- Test: `apps/api/tests/test_edi_210_parser.py`
- Report: `.superpowers/sdd/2026-08-20-phase-3-2-edi-engine/task-5-report.md`

**Global Constraints:**
- Dollar amount calculations must be deterministic.
- Ratio valuation math: `claimed_amount = round(invoice_total * (damaged_qty / total_pieces), 2)`.

**Requirements & Output Schema:**
1. `EDI210ParseResult` Pydantic Model:
   - `transaction_set`: str = "210"
   - `invoice_number`: str
   - `bol_number`: str | None = None
   - `pro_number`: str | None = None
   - `invoice_date`: datetime | None = None
   - `invoice_total`: float
   - `weight`: float
   - `total_pieces`: int
   - `consignee_name`: str | None = None
   - `shipper_name`: str | None = None
   - `calculate_damaged_amount(self, damaged_qty: int) -> float` method
2. `parse_edi_210(raw_content: str) -> EDI210ParseResult`:
   - Parses raw EDI 210 X12 text.
   - Extracts B3, N1, and L3 segments.

**Steps to Execute (TDD Workflow):**
1. Write failing unit tests in `apps/api/tests/test_edi_210_parser.py` verifying invoice total extraction and ratio valuation math ($20,000 invoice with 40/100 damaged pieces -> $8,000.00).
2. Run `pytest apps/api/tests/test_edi_210_parser.py -v` using `run_command` (verify FAIL).
3. Implement `edi_210_parser.py`.
4. Run `pytest apps/api/tests/test_edi_210_parser.py -v` using `run_command` (verify PASS).
5. Write task report to `.superpowers/sdd/2026-08-20-phase-3-2-edi-engine/task-5-report.md`.
6. Commit: `git add apps/api/app/parsers/edi/edi_210_parser.py apps/api/tests/test_edi_210_parser.py` and commit with message `feat(edi): add EDI 210 freight invoice parser with damage ratio valuation`.
