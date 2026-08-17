# Phase 1.3 Expanded Carrier Rule Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand carrier rule engine support for 3 carriers (`ABC Trucking` verified; `Swift Line Logistics` and `Midwest Freight Co.` explicitly tagged `DEMO DATA — UNVERIFIED`) and enhance the `CarrierRulesView.tsx` inspector UI.

**Architecture:** 
- `apps/web/src/data/mockClaims.ts`: Populates 3 carrier rule sets matching database seed definitions.
- `apps/web/src/components/CarrierRulesView.tsx`: Renders rule inspector grid with verified vs unverified tariff citation badges.

**Tech Stack:** React 18, TypeScript, TailwindCSS v4.

**Spec:** `phases.md` Section 1.3, `rules.md` Section 4.

---

### Task 1: Update Mock Carrier Data (`apps/web/src/data/mockClaims.ts`)

**Files:**
- Modify: `apps/web/src/data/mockClaims.ts`

- [ ] **Step 1: Ensure 3 carriers are configured with `VERIFIED` and `DEMO DATA — UNVERIFIED` source citations**

---

### Task 2: Enhance Carrier Rule Inspector View (`CarrierRulesView.tsx`)

**Files:**
- Modify: `apps/web/src/components/CarrierRulesView.tsx`

- [ ] **Step 1: Enhance `CarrierRulesView.tsx` with rule set cards, tariff citations, and verification status badges**

---

### Task 3: Verification & Build Check

- [ ] Run `npm run build:web` to verify zero TypeScript/bundle errors.
- [ ] Run `python -m pytest apps/api/tests` to confirm full-stack integrity.
