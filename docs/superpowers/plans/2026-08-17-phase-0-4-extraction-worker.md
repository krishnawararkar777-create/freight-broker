# Phase 0.4 Provider-Abstracted Extraction Schema & Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Pydantic extraction I/O schemas, abstract `BaseDocumentParser` interface, `LocalPdfParser` default implementation, `LlmVisionParser` swappable stub, and `ExtractionService` to extract facts, bounding boxes, and provenance into `document_evidence` and `claim_facts` tables.

**Architecture:** 
- `apps/api/schemas/extraction.py`: `BoundingBox`, `ExtractedField`, `ExtractionResult`.
- `apps/api/parsers/base.py`: Abstract base class `BaseDocumentParser`.
- `apps/api/parsers/local_parser.py`: Phase 0 default implementation for text-layer PDFs.
- `apps/api/parsers/llm_vision_parser.py`: Swappable VLM provider stub.
- `apps/api/services/extraction_service.py`: Orchestrates parsing, groundings, and DB persistence into `document_evidence` & `claim_facts`.

**Tech Stack:** Python 3.11, Pydantic v2, SQLAlchemy ORM, Pytest.

**Spec:** `phases.md` Section 0.4, `architecture.md` Section 7, `rules.md` Section 2 & 6.

## Global Constraints

- **Evidence Grounding:** Every fact must trace to source document evidence (`document_evidence` row). Missing facts default to `null / UNKNOWN` with `verification_status = "needs_review"`—never a plausible guess.
- **Provider Abstraction:** Swapping `LocalPdfParser` for `LlmVisionParser` in config must require zero changes to `extraction_service.py`.
- **Confidence Cutoff:** Fields below confidence threshold default to `verification_status = "needs_review"`.

---

### Task 1: TDD Test Suite — Extraction & Provenance (RED Stage)

**Files:**
- Create: `apps/api/tests/test_extraction_service.py`

- [ ] **Step 1: Write test cases for extraction pipeline and grounding**
  - Test `LocalPdfParser` extracts carrier, shipment reference, pickup date, declared value, and damage notes with page numbers and bounding boxes.
  - Test missing facts are set to `null / UNKNOWN` with `verification_status = "needs_review"`.
  - Test swapping parser implementation requires zero changes to `extraction_service.py`.

- [ ] **Step 2: Run pytest to verify RED state**
  Run `pytest apps/api/tests/test_extraction_service.py` and confirm failure (`ModuleNotFoundError` / missing schemas).

---

### Task 2: Implement Extraction Schemas & Abstract Parser Interface (GREEN Stage)

**Files:**
- Create: `apps/api/schemas/__init__.py`
- Create: `apps/api/schemas/extraction.py`
- Create: `apps/api/parsers/__init__.py`
- Create: `apps/api/parsers/base.py`

- [ ] **Step 1: Create Pydantic schemas in `schemas/extraction.py`**
  `BoundingBox`, `ExtractedField`, `ExtractionResult`.

- [ ] **Step 2: Create abstract `BaseDocumentParser` in `parsers/base.py`**

---

### Task 3: Implement `LocalPdfParser` & `LlmVisionParser` (GREEN Stage)

**Files:**
- Create: `apps/api/parsers/local_parser.py`
- Create: `apps/api/parsers/llm_vision_parser.py`

- [ ] **Step 1: Implement `LocalPdfParser`**
  Extracts text, structured fields (carrier, BOL number, pickup date, delivery date, claimed amount, damaged quantity, damage description), page numbers, and bounding box coordinates.

- [ ] **Step 2: Implement `LlmVisionParser` stub**
  Swappable VLM parser implementing `BaseDocumentParser`.

---

### Task 4: Implement `ExtractionService` & Router Trigger (GREEN Stage)

**Files:**
- Create: `apps/api/services/extraction_service.py`
- Modify: `apps/api/routers/documents.py` (auto-trigger extraction upon upload)

- [ ] **Step 1: Implement `ExtractionService.extract_and_persist()`**
  Loads file from MinIO/storage, invokes parser, validates Pydantic schema, inserts `document_evidence` rows and updates `claim_facts` rows with confidence & verification status.

- [ ] **Step 2: Re-run Pytest suite to verify GREEN state**
  Run `pytest apps/api/tests/test_extraction_service.py` and confirm 100% PASS.

---

### Task 5: Verification & Evidence Gathering

- [ ] Execute `python -m pytest apps/api/tests` and capture results.
