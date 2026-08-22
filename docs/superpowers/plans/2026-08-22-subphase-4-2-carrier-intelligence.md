# Sub-Phase 4.2: Rejection Reason Taxonomy & Carrier Denial Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a standardized 2-tier freight rejection taxonomy, an automated carrier denial intelligence & profiling service (computing denial tactics, TTIR, and TTS), and an evidence-grounded rebuttal recommendation engine citing verified case law (*Hughes v. United Van Lines*, *Elmore & Stahl*, *49 U.S.C. § 14706*).

**Architecture:** 
- `DenialIntelligenceService`: Ingests carrier response text, classifies rejection into the 2-tier taxonomy (5 categories, 15 sub-codes), detects compound/ambiguous denials, and aggregates historical carrier profiles.
- `RebuttalService`: Extended to recommend and draft formal statutory rebuttals matching the classified denial reason with verified legal citations.
- REST Endpoints: Expose rejection metrics, carrier profiles, and rebuttal recommendation APIs.

**Tech Stack:** Python 3.14 + FastAPI + SQLAlchemy + Pydantic v2 + PostgreSQL + Pytest.

**Spec:** `startup_target_overview.md` (Denial Intelligence) & `phases.md` (Sub-phase 4.2).

## Global Constraints

- **2-Tier Standard Taxonomy:** 5 top-level categories (`PROCEDURAL_TIMING`, `DOCUMENTATION_DEFICIENCY`, `CARMACK_STATUTORY_EXCEPTION`, `SALVAGE_MITIGATION`, `COVERAGE_TARIFF_LIMITATION`) and 15 distinct sub-codes.
- **Ambiguity & Compound Letter Rule:** When multiple categories are present or classification confidence < 0.85, set `requires_human_adjudication = True`.
- **Independently Verified Legal Citations Only:**
  - *Hughes v. United Van Lines, 829 F.2d 1407 (7th Cir. 1987)* (4-part test for released-value rate limitations).
  - *Missouri Pacific R. Co. v. Elmore & Stahl, 377 U.S. 134 (1964)* (burden-shifting under Carmack prima facie rules).
  - *49 U.S.C. § 14706(e)(1)* (9-month minimum claim filing statutory window).
  - *49 CFR § 370.9* (30-day acknowledgment / 120-day resolution).
- **Human-in-the-Loop Rebuttals:** Rebuttals are generated in `draft_status = "DRAFT"` and require human sign-off before transmission.

---

### Task 1: Rejection Taxonomy Schema & Domain Definitions

**Files:**
- Create: `apps/api/app/schemas/rejection_taxonomy.py`
- Test: `apps/api/tests/test_rejection_taxonomy.py`

**Interfaces:**
- Produces: Enums `RejectionCategory`, `RejectionSubCode`, Pydantic models `DenialClassificationResult`, `CarrierBehaviorProfile`, `RebuttalRecommendation`.

- [ ] **Step 1: Write schema verification tests**
Write tests in `apps/api/tests/test_rejection_taxonomy.py` verifying enum values, classification result validation, and compound flag behaviors.

- [ ] **Step 2: Run test to verify failure**
Run: `pytest apps/api/tests/test_rejection_taxonomy.py -v`

- [ ] **Step 3: Implement `rejection_taxonomy.py`**
Create `rejection_taxonomy.py` with all 5 categories, 15 sub-codes, citation mappings, and Pydantic schemas.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/api/tests/test_rejection_taxonomy.py -v`

- [ ] **Step 5: Commit**
`git add apps/api/app/schemas/rejection_taxonomy.py apps/api/tests/test_rejection_taxonomy.py && git commit -m "feat(4.2): define 2-tier rejection taxonomy schemas"`

---

### Task 2: Denial Intelligence & Carrier Profiling Service

**Files:**
- Create: `apps/api/app/services/denial_intelligence_service.py`
- Test: `apps/api/tests/test_denial_classifier.py`

**Interfaces:**
- Produces:
  - `DenialIntelligenceService.classify_denial_letter(text: str) -> DenialClassificationResult`
  - `DenialIntelligenceService.get_rejection_analytics(db: Session, org_id: Optional[str] = None) -> Dict`
  - `DenialIntelligenceService.get_carrier_profile(db: Session, carrier_id: str) -> Dict`
  - `DenialIntelligenceService.get_all_carrier_profiles(db: Session, org_id: Optional[str] = None) -> List[Dict]`

- [ ] **Step 1: Write comprehensive TDD tests for all 5 categories + compound letter**
Write tests in `apps/api/tests/test_denial_classifier.py` with realistic carrier denial letter fixtures:
  - Category 1: Missed Carmack 9-month / 5-day concealed damage letter.
  - Category 2: Clean POD / missing invoice letter.
  - Category 3: Improper packaging / act of shipper letter.
  - Category 4: Discarded cargo before inspection / salvage letter.
  - Category 5: Released value rate cap ($0.50/lb) tariff letter.
  - Compound / Ambiguous Letter: Multi-reason denial testing `requires_human_adjudication`.

- [ ] **Step 2: Run test to verify failure**
Run: `pytest apps/api/tests/test_denial_classifier.py -v`

- [ ] **Step 3: Implement `DenialIntelligenceService`**
Build classification logic, keyword & contextual phrase extractors, carrier response aggregations (TTIR, TTS, settlement ratios, tactic distribution).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/api/tests/test_denial_classifier.py -v`

- [ ] **Step 5: Commit**
`git add apps/api/app/services/denial_intelligence_service.py apps/api/tests/test_denial_classifier.py && git commit -m "feat(4.2): implement DenialIntelligenceService and carrier profiling"`

---

### Task 3: Grounded Rebuttal Recommendation Engine

**Files:**
- Modify: `apps/api/app/services/rebuttal_service.py`
- Test: `apps/api/tests/test_rebuttal_recommendation.py`

**Interfaces:**
- Produces:
  - `recommend_and_generate_rebuttal(db: Session, claim_id: str, denial_text: Optional[str] = None, category_override: Optional[str] = None) -> Dict[str, Any]`
  - Extends templates to incorporate the 4-part *Hughes v. United Van Lines* test for released-value rate disputes, *Elmore & Stahl* burden-shifting for packaging claims, and *49 U.S.C. § 14706(e)(1)* statutory filing rights.

- [ ] **Step 1: Write rebuttal recommendation tests**
Write tests in `apps/api/tests/test_rebuttal_recommendation.py` verifying citation insertion, template generation, and draft communication creation.

- [ ] **Step 2: Run test to verify failure**
Run: `pytest apps/api/tests/test_rebuttal_recommendation.py -v`

- [ ] **Step 3: Implement extended rebuttal recommendation logic**
Update `rebuttal_service.py` with the Hughes 4-part test and statutory citations.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/api/tests/test_rebuttal_recommendation.py -v`

- [ ] **Step 5: Commit**
`git add apps/api/app/services/rebuttal_service.py apps/api/tests/test_rebuttal_recommendation.py && git commit -m "feat(4.2): extend rebuttal engine with Hughes test and statutory counter-citations"`

---

### Task 4: Rejection & Carrier Intelligence API Endpoints

**Files:**
- Modify: `apps/api/routers/telemetry.py`
- Modify: `apps/api/routers/claims.py`
- Test: `apps/api/tests/test_rejection_endpoints.py`

**Interfaces:**
- Produces:
  - `GET /api/telemetry/rejections` -> Taxonomy breakdown and carrier denial tactic matrix.
  - `GET /api/telemetry/carrier-profiles` -> Carrier performance scorecards.
  - `GET /api/telemetry/carrier-profiles/{carrier_id}` -> Specific carrier profile.
  - `POST /api/claims/{claim_id}/rebuttal/recommend` -> Rebuttal recommendation and draft generation.

- [ ] **Step 1: Write API endpoint tests**
Write tests in `apps/api/tests/test_rejection_endpoints.py` testing the new telemetry and rebuttal endpoints.

- [ ] **Step 2: Run test to verify failure**
Run: `pytest apps/api/tests/test_rejection_endpoints.py -v`

- [ ] **Step 3: Implement and register router endpoints**
Update `routers/telemetry.py` and `routers/claims.py`.

- [ ] **Step 4: Run tests to verify they pass**
Run: `pytest apps/api/tests/test_rejection_endpoints.py -v`

- [ ] **Step 5: Commit**
`git add apps/api/routers/telemetry.py apps/api/routers/claims.py apps/api/tests/test_rejection_endpoints.py && git commit -m "feat(4.2): expose rejection taxonomy and carrier intelligence endpoints"`

---

### Task 5: End-to-End Verification & Master Test Suite Run

**Files:**
- Test: `apps/api/tests/` (full test suite)

- [ ] **Step 1: Run full pytest suite across all tests**
Run: `pytest apps/api/tests`
Verify 100% clean passing with 0 warnings or failures.

- [ ] **Step 2: Update SDD Progress Ledger & Memory File**
Record completion in `.superpowers/sdd/` and `memory.md`.
