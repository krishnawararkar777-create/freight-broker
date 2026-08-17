# Phase 2 — Skill Mapping & Sub-Phase Execution Rules

This document specifies the exact mapping of Antigravity skills to Phase 2 sub-phases (2.1 through 2.5) and cross-cutting workflows. These skill rules are MANDATORY for all Phase 2 development.

---

## 1. Core Meta-Loop (Sub-Phase Iteration)

For EVERY sub-phase (2.1 through 2.5), the mandatory core loop is:
```
brainstorming → writing-plans → test-driven-development (TDD) → verification-before-completion → requesting-code-review → finishing-a-development-branch
```

---

## 2. Sub-Phase Skill Assignments

### Sub-Phase 2.1 — Multi-Tenancy, Supabase DB & RBAC Enforcement (Security-Critical)

* `brainstorming`: Before writing any RLS policy, work through the isolation model: determine whether every table requires direct `organization_id` or inherits isolation via a parent join. Prevent silent data leaks.
* `writing-plans`: Enumerate all 19 database tables with their specific isolation strategy as a checklist before writing any code.
* `test-driven-development` (TDD): **Mandatory & strict**. Write the cross-tenant isolation test (`Broker A cannot view Broker B's data`) BEFORE the RLS policy exists.
* `requesting-code-review`: **Mandatory**. Review all RLS policies and RBAC roles before merging.
* `subagent-driven-development`: Use subagents to parallelize work within 2.1 (e.g. Subagent 1 on Supabase infra/auth, Subagent 2 on RLS policies, Subagent 3 on RBAC roles). *Note:* Do NOT parallelize testing of cross-tenant isolation; test against the complete system.
* `verification-before-completion`: Run `supashield audit` and `supashield test --as-user` against the Supabase schema and `supashield test-storage` against the S3 document bucket. Verify 100% coverage and zero policy leaks across all 19 tables.
* `finishing-a-development-branch`: Close out 2.1 cleanly before beginning 2.2.

---

### Sub-Phase 2.2 — Follow-Up Automation & Carrier SLA Tracking

* `brainstorming`: Precisely define "overdue" (calendar days vs. business days for 30-day acknowledgment and 120-day resolution windows under 49 CFR § 370.9) before building alerting logic.
* `writing-plans`: Explicitly plan the `follow-up draft` → `human approval` → `dispatch` state machine.
* `test-driven-development` (TDD): Moderate-heavy. Write tests for 30-day and 120-day boundary conditions and timezone edge cases.
* `systematic-debugging`: Proactively use if SLA clock calculations produce off-by-one errors or timezone drift.
* `requesting-code-review`: Review follow-up gating logic to ensure no follow-up is sent without explicit human sign-off.

---

### Sub-Phase 2.3 — Carrier Response Intelligence & Settlement Extraction

* `brainstorming`: Design the `carrier_responses` schema and visual confidence indicators before trusting extracted dollar amounts.
* `writing-plans`: Plan as an extension of the existing `DocumentParser` base interface (`apps/api/parsers/base.py`).
* `test-driven-development` (TDD): **Heavy & money-critical**. Write TDD tests for offer amount vs. claimed amount parsing and discrepancy math.
* `requesting-code-review`: **Mandatory code review** (touches real dollars and settlement terms).
* `verification-before-completion`: Test with realistic carrier denial letters and partial settlement offer fixtures, verifying accurate extraction.

---

### Sub-Phase 2.4 — Denial, Rebuttal & Legal Appeal Loop

* `brainstorming`: Map every carrier denial pretext (concealed damage 5-day window, salvage duty, packaging negligence) before drafting rebuttal logic.
* `writing-plans`: Plan rebuttal state machine and Carmack lawsuit clock tracker (`lawsuit_deadline_at`).
* `test-driven-development` (TDD): **Mandatory & strict**. The `2 years + 1 day from date of written disallowance` Carmack clock is a hard legal deadline. Write comprehensive TDD unit tests for date math.
* `systematic-debugging`: Proactively test leap-year and month-boundary edge cases for the 2-year + 1-day deadline calculator.
* `requesting-code-review`: **Mandatory**.
* `verification-before-completion`: Hand-calculate statutory lawsuit deadlines for multiple test dates and verify system outputs match down to the exact day.

---

### Sub-Phase 2.5 — Event-Based Recovery & Contingency Fee Ledger

* `brainstorming`: Design `recovery_events` and `fee_events` as an **immutable, append-only ledger** (financial audit record).
* `writing-plans`: Plan the `recovery-event` → `fee-calculation` → `invoice` pipeline as discrete, auditable steps.
* `test-driven-development` (TDD): **Mandatory & highest rigor**. Test Marajet's business model fee calculation:
  $$\text{Fee} = \text{Eligible Recovered} \times 0.20 \quad (\$0 \text{ fee on } \$0 \text{ recovered})$$
  Explicitly test the $0 recovery case.
* `requesting-code-review`: **Mandatory**.
* `verification-before-completion`: Manually compute fees for multiple recovery test fixtures and verify exact match with invoice calculations.

---

## 3. Cross-Cutting Meta-Skills Rules

* `using-superpowers`: Meta-skill running continuously across all Phase 2 development.
* `dispatching-parallel-agents`: Use **ONLY within a sub-phase** (e.g. splitting 2.1 tasks). **NEVER parallelize across sub-phases** (Sub-phases 2.2 through 2.5 depend strictly on 2.1's verified multi-tenant foundation).
* `writing-skills`: Create new skills if repeated patterns emerge across sub-phases (e.g. extraction with confidence scoring).
* `finishing-a-development-branch`: Execute branch closeout at the completion of **each individual sub-phase**, maintaining strict progress checkpoints.
