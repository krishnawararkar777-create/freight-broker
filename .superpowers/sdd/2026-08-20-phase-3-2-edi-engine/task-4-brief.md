# Task 4 Brief: EDI 214 Carrier Shipment Status Parser

**Goal:** Create the EDI 214 status message parser in `apps/api/app/parsers/edi/edi_214_parser.py`.

**Files:**
- Create: `apps/api/app/parsers/edi/edi_214_parser.py` (and `apps/api/app/parsers/edi/x12_segment_parser.py` if needed for structural X12 tokenizing)
- Test: `apps/api/tests/test_edi_214_parser.py`
- Report: `.superpowers/sdd/2026-08-20-phase-3-2-edi-engine/task-4-report.md`

**Global Constraints:**
- Must use `dateutil.relativedelta(months=9)` for Carmack statutory filing date calculation — NEVER 270-day approximations or LLM math.
- Must handle standard X12 segment terminators (`~` or `\n`) and element delimiters (`*`).
- Must handle both 8-digit (`YYYYMMDD`) and 6-digit (`YYMMDD`) date formats in AT7 segments.

**Requirements & Output Schema:**
1. `EDI214ParseResult` Pydantic Model:
   - `transaction_set`: str = "214"
   - `pro_number`: str
   - `bol_number`: str | None = None
   - `carrier_scac`: str | None = None
   - `status_code`: str  # e.g. "AG", "SD", "CD", "A7", "X6"
   - `status_description`: str  # Human readable description
   - `is_damage_exception`: bool  # True if code in ("AG", "SD", "CD", "A7")
   - `delivery_at`: datetime
   - `carmack_deadline_at`: datetime  # delivery_at + relativedelta(months=9)
   - `concealed_deadline_at`: datetime  # delivery_at + timedelta(days=5)
2. `parse_edi_214(raw_content: str) -> EDI214ParseResult`:
   - Parses raw X12 EDI text.
   - Extracts B10 (PRO/BOL/Carrier) and AT7 (Status/Date/Time) segments.
   - Computes delivery timestamp and deadline dates.

**Steps to Execute (TDD Workflow):**
1. Write failing unit tests in `apps/api/tests/test_edi_214_parser.py` verifying status extraction and date math (e.g. Aug 20, 2026 delivery -> May 20, 2027 Carmack deadline).
2. Run `pytest apps/api/tests/test_edi_214_parser.py -v` using `run_command` (verify FAIL).
3. Implement `edi_214_parser.py` and `x12_segment_parser.py`.
4. Run `pytest apps/api/tests/test_edi_214_parser.py -v` using `run_command` (verify PASS).
5. Write task report to `.superpowers/sdd/2026-08-20-phase-3-2-edi-engine/task-4-report.md`.
6. Commit: `git add apps/api/app/parsers/edi/ apps/api/tests/test_edi_214_parser.py` and commit with message `feat(edi): add EDI 214 shipment status parser with Carmack date triggers`.
