# Phase 1.2 Visual Deadline Urgency Alerts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement visual color-coded Carmack deadline countdown urgency badges (`CRITICAL`, `WARNING`, `SAFE`, `EXPIRED`) driven by exact calendar-month arithmetic.

**Architecture:** 
- `apps/web/src/lib/deadline-urgency.ts`: Pure urgency calculation helper.
- `apps/web/src/components/DeadlineUrgencyBadge.tsx`: Reusable countdown badge component.
- `apps/web/src/components/DashboardView.tsx` & `HumanReviewWorkspace.tsx`: Render dynamic deadline urgency badges.

**Tech Stack:** React 18, TypeScript, TailwindCSS v4.

**Spec:** `phases.md` Section 1.2, `rules.md` Section 5.

---

### Task 1: Implement Urgency Helper Logic (`apps/web/src/lib/deadline-urgency.ts`)

**Files:**
- Create: `apps/web/src/lib/deadline-urgency.ts`

- [ ] **Step 1: Implement `calculateDeadlineDaysRemaining` and `getDeadlineUrgencyLevel`**
  - `< 30 days` $\rightarrow$ `CRITICAL` (🔴 Urgent)
  - `30-60 days` $\rightarrow$ `WARNING` (🟡 Warning)
  - `> 60 days` $\rightarrow$ `SAFE` (🟢 Safe)
  - `< 0 days` $\rightarrow$ `EXPIRED` (❌ Expired)

---

### Task 2: Create `DeadlineUrgencyBadge.tsx` Component

**Files:**
- Create: `apps/web/src/components/DeadlineUrgencyBadge.tsx`

- [ ] **Step 1: Implement reusable badge component with Lucide icons**

---

### Task 3: Integrate Urgency Badges into Dashboard & Review Workspace

**Files:**
- Modify: `apps/web/src/components/DashboardView.tsx`
- Modify: `apps/web/src/components/HumanReviewWorkspace.tsx`

- [ ] **Step 1: Update deadline column in `DashboardView.tsx` to render `DeadlineUrgencyBadge`**

---

### Task 4: Verification & Build Check

- [ ] Run `npm run build:web` to verify zero TypeScript/bundle errors.
- [ ] Run `python -m pytest apps/api/tests` to confirm full-stack integrity.
