# Phase 1.1 Claims Operational Dashboard & Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the multi-claim operational dashboard with status tabs, real-time search, claim type filtering, KPI metric cards, and backend API integration.

**Architecture:** 
- `apps/web/src/lib/dashboard-filters.ts`: Pure search and status filter utility.
- `apps/web/src/components/DashboardView.tsx`: Operational claims dashboard component.
- `apps/api/routers/claims.py`: `GET /api/claims` endpoint supporting `status_filter`, `claim_type_filter`, and `search_query` parameters.

**Tech Stack:** React 18, TypeScript, TailwindCSS v4, Python 3.11, FastAPI, Pytest.

**Spec:** `phases.md` Section 1.1, `architecture.md` Section 4.1.

---

### Task 1: TDD — Implement Search & Filter Utility & Unit Test (RED Stage)

**Files:**
- Create: `apps/web/src/lib/dashboard-filters.ts`

- [ ] **Step 1: Write `filterClaims` utility in `apps/web/src/lib/dashboard-filters.ts`**
  Supports filtering by status (`ALL`, `UNDER_REVIEW`, `SUBMITTED`, `RECOVERED`, `CLOSED`), claim type, and search text (matching claim number, pro number, carrier name, or shipper).

- [ ] **Step 2: Add self-contained `verifyDashboardFilters` test helper**

---

### Task 2: Enhance Backend `GET /api/claims` Endpoint & Pytest (GREEN Stage)

**Files:**
- Modify: `apps/api/routers/claims.py`
- Modify: `apps/api/tests/test_submission_guard.py` (or add test in `test_claims.py`)

- [ ] **Step 1: Update `GET /api/claims` in `apps/api/routers/claims.py`**
  Accepts optional `status_filter`, `claim_type`, and `query` parameters.

- [ ] **Step 2: Run pytest to verify backend endpoint filters**

---

### Task 3: Enhance React Dashboard Component (`DashboardView.tsx`) (GREEN Stage)

**Files:**
- Modify: `apps/web/src/components/DashboardView.tsx`

- [ ] **Step 1: Connect status tabs, search bar, and KPI math in `DashboardView.tsx`**

---

### Task 4: Verification & Build Check

- [ ] Run `npm run build:web` to verify zero TypeScript/bundle errors.
- [ ] Run `python -m pytest apps/api/tests` to verify 100% test pass.
