# Phase 0.5 Split-Screen Human Review Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the split-screen human review workspace in React with bidirectional click-to-highlight sync between structured facts and bounding box document overlays, inline fact editing with audit diffs, and readiness/approval controls.

**Architecture:** 
- `apps/web/src/lib/sync-logic.ts`: Pure matching utility finding bounding box overlays for selected claim facts.
- `apps/web/src/components/HumanReviewWorkspace.tsx`: 3-pane split-screen container.
- `apps/web/src/components/document-viewer/DocumentViewer.tsx`: Document canvas rendering and bounding box overlay canvas.
- `apps/web/src/components/provenance-panel/FactTable.tsx`: Center pane structured facts table with inline edit dialog logging audit diffs.

**Tech Stack:** React 18, TypeScript, TailwindCSS v4, Vitest / Jest (for frontend sync logic test), Lucide React icons.

**Spec:** `phases.md` Section 0.5, `architecture.md` Section 4.2 & 3, `rules.md` Section 3.

## Global Constraints

- **Karpathy Simplicity Rule:** Keep changes surgical and avoid over-engineering—focus tests specifically on the click-to-highlight sync logic, not visual pixel layouts.
- **State Management:** Pure local component state (`useState`)—no external state management libraries added.
- **Audit diffs:** Inline fact editing MUST record `original_value`, `edited_value`, `actor=usr-1`, and `edit_reason`, marking `verification_status = "edited_by_human"`.

---

### Task 1: TDD — Implement Bidirectional Sync Logic & Unit Test (RED Stage)

**Files:**
- Create: `apps/web/src/lib/sync-logic.ts`
- Create: `apps/web/src/lib/sync-logic.test.ts`

- [ ] **Step 1: Write test for `findMatchingEvidence` matching fact to bbox**

```typescript
// apps/web/src/lib/sync-logic.test.ts
import { findMatchingEvidence } from './sync-logic';

test('findMatchingEvidence returns matching evidence for selected field_name', () => {
  const evidenceList = [
    { id: 'evd-1', field_name: 'carrier_name', page_number: 1, bbox_json: { x_min: 0.1, y_min: 0.1, x_max: 0.4, y_max: 0.15 } },
    { id: 'evd-2', field_name: 'declared_value', page_number: 1, bbox_json: { x_min: 0.5, y_min: 0.3, x_max: 0.8, y_max: 0.35 } }
  ];
  const matched = findMatchingEvidence('carrier_name', evidenceList);
  assert(matched?.id === 'evd-1');
});
```

- [ ] **Step 2: Implement minimal `sync-logic.ts` and verify test passes**

---

### Task 2: Implement 3-Pane Split-Screen Review Workspace Components (GREEN Stage)

**Files:**
- Create: `apps/web/src/components/document-viewer/DocumentViewer.tsx`
- Create: `apps/web/src/components/provenance-panel/FactTable.tsx`
- Modify: `apps/web/src/components/HumanReviewWorkspace.tsx`

- [ ] **Step 1: Implement `DocumentViewer.tsx`**
  Renders document canvas, page navigation controls, zoom (+/-), and interactive bounding box overlay canvas. Clicking a bounding box triggers `onSelectFact(fieldName)`.

- [ ] **Step 2: Implement `FactTable.tsx`**
  Renders center pane table of `claim_facts` with confidence badges, source citations (`[BOL p.1]`), and inline edit modal updating `original_value`, `new_value`, and `edit_reason`. Clicking a row triggers `onSelectFact(fieldName)`.

- [ ] **Step 3: Connect `HumanReviewWorkspace.tsx` with bidirectional selection state**
  Wire local `selectedFieldName` state connecting `DocumentViewer` and `FactTable`.

---

### Task 3: Verification & Build Check

- [ ] Run `npm run build:web` to verify zero TypeScript or bundle errors.
- [ ] Run backend `python -m pytest apps/api/tests` to verify complete system integrity.
