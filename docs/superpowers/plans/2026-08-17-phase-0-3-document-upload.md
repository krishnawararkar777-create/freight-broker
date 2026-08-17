# Phase 0.3 Document Upload & Idempotency Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement file upload streaming, MinIO object storage integration, SHA-256 fingerprinting, and duplicate document `409 Conflict` idempotency guards for `POST /api/claims/{claim_id}/documents/upload`.

**Architecture:** Router `apps/api/routers/documents.py` delegates to `apps/api/services/document_service.py` and `apps/api/services/storage_service.py` (MinIO boto3 wrapper). No raw local `/uploads` directory allowed.

**Tech Stack:** Python 3.11, FastAPI (`UploadFile`), MinIO / boto3 S3 client, hashlib SHA-256, SQLAlchemy, Pytest.

**Spec:** `phases.md` Section 0.3, `architecture.md` Section 4.1 & 6, `rules.md` Section 5 & 7.

## Global Constraints

- **Storage:** MinIO bucket `algolyra-documents` via signed URLs (no public bucket, no local `/uploads` folder).
- **Idempotency:** Re-uploading identical file payload (matching SHA-256) to the same claim returns `HTTP 409 Conflict`.
- **Error Response Format:** Standardized JSON (`{"error_code": "...", "message": "...", "details": {...}}`).

---

### Task 1: Write TDD Test Suite (RED Stage)

**Files:**
- Create: `apps/api/tests/test_document_upload.py`

- [ ] **Step 1: Write test cases for document upload and duplicate detection**

```python
def test_upload_document_success(): ...
def test_upload_duplicate_document_returns_409(): ...
def test_get_document_signed_url(): ...
```

- [ ] **Step 2: Run pytest to verify RED failure**
  Run `pytest apps/api/tests/test_document_upload.py` and confirm failure (`404 Not Found` / missing endpoint).

---

### Task 2: Implement Storage & Document Service (GREEN Stage)

**Files:**
- Create: `apps/api/services/storage_service.py`
- Create: `apps/api/services/document_service.py`
- Create: `apps/api/routers/documents.py`
- Modify: `apps/api/main.py`

- [ ] **Step 1: Implement `storage_service.py`**
  MinIO S3 streaming wrapper generating object keys `{organization_id}/{claim_id}/{document_id}/{filename}` and generating short-lived presigned URLs.

- [ ] **Step 2: Implement `document_service.py`**
  Computes SHA-256 while streaming bytes, checks duplicate `sha256` per claim, inserts `documents` row, returns document model.

- [ ] **Step 3: Implement `routers/documents.py`**
  Expose `POST /api/claims/{claim_id}/documents/upload` and `GET /api/claims/{claim_id}/documents/{document_id}/url`.

- [ ] **Step 4: Re-run Pytest to verify GREEN state**
  Run `pytest apps/api/tests/test_document_upload.py` and confirm all tests pass.

---

### Task 3: Security & Code Review Check

- [ ] Verify filename sanitization, MIME-type checks, and signed URL expiration.

---

### Task 4: Empirical Verification Evidence

- [ ] Execute `pytest apps/api/tests` and capture results.
