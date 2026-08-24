# Real Per-Organization Dashboard Data & Zero-State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded/mock dashboard numbers with real database queries strictly scoped to the logged-in user's organization ID (`tenant_id`/`organization_id`), featuring proper loading states and honest empty/zero states for new organizations with 0 claims.

**Architecture:** Frontend components (`DashboardView`, `ExecutiveAnalyticsDashboard`, `App.tsx`) will fetch live claims via the FastAPI backend (`GET /api/claims?organization_id=<org.id>`), sending session tokens. Backend filters PostgreSQL queries by `organization_id`. Initial state starts empty with a loading spinner while fetching, displaying real database data or an empty zero-state ($0 Total Claimed, 0 Active Open Claims) if no claims exist for that organization.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, FastAPI, SQLAlchemy, Supabase Auth & PostgreSQL.

---

## Global Constraints

- Every dashboard metric must come from a real database query filtered by `organization_id`.
- Zero claims must show an honest $0 / empty queue state — no fake fallbacks or broken UI.
- Requests must include authenticated session context.
- Loading and error states must be displayed explicitly during data fetching.

---

### Task 1: Backend Endpoint Tenant Scoping (`apps/api/routers/claims.py`)

**Files:**
- Modify: `apps/api/routers/claims.py:175-231`
- Test: `scratch/test_tenant_claims_api.py`

**Interfaces:**
- Consumes: `GET /api/claims?organization_id=<id>`
- Produces: JSON array of claims strictly filtered by `Claim.organization_id`

- [ ] **Step 1: Update `list_claims` in `claims.py` to accept `organization_id` filter**

```python
@router.get("", status_code=status.HTTP_200_OK)
def list_claims(
    status_filter: Optional[str] = None,
    claim_type: Optional[str] = None,
    search_query: Optional[str] = None,
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Claim)
    if organization_id:
        query = query.filter(Claim.organization_id == organization_id)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Claim.status == status_filter.upper())
    if claim_type and claim_type.upper() != "ALL":
        query = query.filter(Claim.claim_type == claim_type)
    claims = query.all()
```

- [ ] **Step 2: Run verification script to confirm isolation**

Run: `python scratch/test_tenant_claims_api.py`
Expected: Returns only claims for target `organization_id`, and `[]` for unknown org.

---

### Task 2: Frontend Session-Scoped Fetching (`apps/web/src/App.tsx`)

**Files:**
- Modify: `apps/web/src/App.tsx:20-135`

**Interfaces:**
- Consumes: `useAuth()` (`session`, `org`, `userProfile`)
- Produces: `claims`, `isLoadingClaims`, `errorClaims` passed to views

- [ ] **Step 1: Replace initial `mockClaims` state with empty array `[]` and add loading/error state**
- [ ] **Step 2: Update `fetchLiveClaims` to pass `org.id` query parameter & handle loading/error**

---

### Task 3: Dashboard Loading & Honest Empty States (`apps/web/src/components/DashboardView.tsx`)

**Files:**
- Modify: `apps/web/src/components/DashboardView.tsx`

- [ ] **Step 1: Accept `isLoading` & `error` props and render loading spinner / error banner**
- [ ] **Step 2: Render honest zero state ($0 Total Claimed, 0 Active Open) when `claims.length === 0`**
- [ ] **Step 3: Render empty Claims Queue placeholder with "+ INGEST CLAIM" action**

---

### Task 4: Analytics Loading & Honest Empty States (`apps/web/src/components/ExecutiveAnalyticsDashboard.tsx`)

**Files:**
- Modify: `apps/web/src/components/ExecutiveAnalyticsDashboard.tsx`

- [ ] **Step 1: Compute metrics dynamically from org-scoped `claims`**
- [ ] **Step 2: Display loading indicator while fetching & zeroed metrics for empty state**

---

### Task 5: End-to-End Multi-Tenant Verification & Output Generation

- [ ] **Step 1: Run local FastAPI backend & test login with Org A (`sarah.jenkins@apex.com`)**
- [ ] **Step 2: Verify real claims for Org A load ($20,400 Total Claimed, 2 Claims)**
- [ ] **Step 3: Test login with Brand-New Org (`newuser@zero-claims-org.com` / `org-brandnew-999`)**
- [ ] **Step 4: Verify real honest zero state ($0 Total Claimed, 0 Active Open Claims, empty queue banner)**
- [ ] **Step 5: Ingest a claim for `org-brandnew-999` and verify dashboard updates to reflect exact claim value**
- [ ] **Step 6: Build project (`npm run build`) and push to GitHub `origin/main`**
