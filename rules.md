# Algolyra — rules.md

**Purpose of this file:** what to use, what to avoid, and how to handle errors — the rules every piece of code should follow regardless of which phase or feature it belongs to. `architecture.md` says how the system is shaped; this file says how to write the code that fills that shape. When in doubt, this file wins over convenience or "what's trending."

---

## 1. Non-negotiable rules (repeated from implementation_plan.md Section 4 — these override everything else in this file)

1. **No autonomous negotiation** — AI drafts, a human sends, always.
2. **No autonomous action above the per-organization dollar threshold** (`escalation_threshold_usd`).
3. **Nothing that reads as legal advice or a legal conclusion ships without human review** — AI states factual indicators only ("packaging documentation missing"), never conclusions ("carrier is liable").
4. **AI-generated claim content must be grounded exclusively in evidence.** If a fact isn't in a document, the field value is `null / UNKNOWN`, never a plausible guess.
5. **The claim state machine's `submitted` transition can only be triggered by a human-initiated request** — enforce this server-side, in the service layer, not just hidden behind a disabled frontend button.
6. **Every AI call is logged:** model, model version, prompt version, input references, output, confidence, human modification if any.

Any code review, human or AI, that finds a violation of these six treats it as a blocking issue, not a style nitpick.

---

## 2. Backend rules (Python / FastAPI)

● **Routers are thin.** A router function parses the request, calls exactly one service method, and returns the response. No business logic, no direct database queries, no direct calls to a parser or LLM provider inside a router.
● **All business logic lives in `services/`.** Services take a DB session via dependency injection; they don't open their own connections.
● **Every AI input/output boundary is a Pydantic model.** No raw dict passed between the parser layer and the database. If a model's output can't validate against the expected schema, that's an `invalid_extraction` failure state (Section 5 below), not a silent pass-through.
● **Deadlines, fees, and amounts are calculated in plain Python using calendar-month arithmetic, never by asking an LLM to do arithmetic or using hardcoded day counts like 270.** Use `dateutil.relativedelta(months=9)` for Carmack statutory deadlines. The LLM may identify candidate values; a deterministic function does the actual calculation.
● **Type hints everywhere.** Every function signature is fully typed; this is what makes the Pydantic validation boundary meaningful instead of decorative.
● **No raw SQL string concatenation.** Use SQLAlchemy's query builder or parameterized queries exclusively — this isn't a style preference, it's the difference between safe and unsafe against injection.
● **Every schema change is an Alembic migration**, reviewed before running, never a manual `ALTER TABLE`.
● **`organization_id` scoping is enforced at the query layer**, even in Phase 0 with one hardcoded organization — write the query filter now so it's not a retrofit later, and so it can be tested (see Testing, Section 8).

---

## 3. Frontend rules (React / TypeScript)

● **Strict TypeScript** — no `any` except at a well-justified, commented boundary (e.g., a third-party library with poor types).
● **Tailwind for styling** — no inline style objects, no separate CSS-in-JS library added on top.
● **Shared types come from `packages/shared`**, generated from or matching the backend Pydantic schemas — don't hand-maintain a parallel type definition that can drift out of sync.
● **The document viewer and provenance panel communicate through local component state**, not global state management — there's no need for Redux/Zustand/etc. at this scale; don't add one because it's common practice elsewhere. Revisit only if cross-page state genuinely requires it later.
● **Every API call goes through the shared `lib/` client**, not ad hoc `fetch` calls scattered across components — one place to add auth headers, error handling, and retries later.

---

## 4. Library allowlist (add nothing outside this list without updating this file first)

**Backend:** FastAPI, Pydantic, SQLAlchemy, Alembic, `python-multipart` (file uploads), `boto3` or `minio` client (object storage), `python-dateutil` (calendar-month deadline math), `pytest` + `pytest-asyncio` (testing), DeepEval or Promptfoo (AI eval, once Phase 1's eval suite starts).

**Frontend:** React, Vite, TypeScript, TailwindCSS, a lightweight fetch/query library (e.g. `@tanstack/react-query`) for API state, a PDF-rendering library for the document viewer (e.g. `react-pdf` or `pdf.js` directly).

**Explicitly do not add, even if a tutorial or agent suggests it, without first updating this file:** a second ORM, a second frontend state management library, a vector database beyond `pgvector`, an agent-orchestration framework (LangGraph/similar) before Phase 2 actually needs durable long-running workflows, a dedicated OCR service before the local/LLM-vision parser pair has proven insufficient, any TMS/EDI library before a real pilot customer needs it.

---

## 5. Error handling and failure states

Every failure mode gets an explicit state — **never a silently swallowed exception and never a generic 500 with no context.**

| Failure | State |
| :--- | :--- |
| OCR/vision call fails | `processing_failed` |
| AI call times out | `processing_failed` (with retry, capped — see below) |
| Corrupted/unreadable file | `unsupported_document` |
| Model returns invalid JSON / fails schema validation | `invalid_extraction` |
| Carrier not recognized | `unknown_carrier` |
| Extraction confidence below threshold | `needs_human_review` |
| Duplicate document hash | Reject at upload with **409 Conflict**, don't create a new state |
| Deadline can't be calculated (missing rule) | `unknown_rule` |

● **Retries:** exponential backoff, capped at a small fixed number of attempts (e.g. 3), then the job moves to `processing_failed` and surfaces in the human review queue rather than retrying forever.
● **API error responses follow one consistent JSON shape** (`{"error_code": "...", "message": "...", "details": {...}}`) — don't let different endpoints invent their own error formats.
● **Log every failure with enough context** (`claim_id`, `document_id`, stage) to answer "why did this fail" without reproducing it.

---

## 6. AI-specific engineering rules

● Every AI task (extraction, classification, drafting, readiness scoring) has its **own configurable confidence threshold** — don't use one global cutoff for everything.
● Every AI call writes an audit log entry: model, model version, prompt version, inputs (by reference, not full raw payload if large), output, confidence, and — once a human reviews it — what they changed and why.
● **Prompts are versioned** (`prompt_version` stored alongside every call) so a bad output can be traced back to exactly which prompt produced it.
● **Never let extraction output overwrite a `claim_facts` row that a human already manually verified** — human-verified facts are locked unless the human explicitly re-opens them.

---

## 7. Security rules (apply from Phase 0, not "later")

● **No public object storage URLs, ever** — signed, time-limited URLs only.
● Validate uploaded file type and size before processing; reject anything outside an explicit allowlist of MIME types.
● Sanitize filenames before using them anywhere in a path or displayed string.
● Secrets (DB credentials, API keys) come from environment variables / a `.env` file that is git-ignored — never hardcoded, never committed, even in a "temporary" test.
● Server-side authorization checks on every endpoint that touches claim data, even with a single hardcoded user in Phase 0 — this is the habit that makes Phase 2's real multi-tenancy safe to add later instead of a rewrite.

---

## 8. Testing rules

● **Follow test-driven-development for anything touching money, deadlines, or state transitions** — write the failing test first, then the implementation. This isn't optional for the rules engine, deadline engine, amount engine, or state machine.
● **Unit tests:** deadline calculation (testing exact calendar months via `relativedelta`), fee calculation, state transitions, rules engine lookups, amount calculations.
● **Integration tests:** the full upload → extract → classify → draft flow, end to end, against fixture documents.
● **AI eval tests:** a small golden dataset of sample documents with known-correct expected extraction/classification, run in CI (DeepEval or Promptfoo).
● A pull request that touches the rules engine, deadline engine, or state machine without an accompanying test is not complete, regardless of how simple the change looks.

---

## 9. Git / commit conventions

● **Conventional commit messages** (`feat:`, `fix:`, `test:`, `chore:`, `docs:`).
● One task from `phases.md` per branch/PR where practical — makes it easy to track progress against the phase checklist and easy to review.
● Migrations are reviewed in the same PR as the model change that required them, never added separately after the fact.

---

## 10. Consolidated anti-pattern list

● **No AI-invented carrier rules** — every rule in `carrier_rule_sets` needs a real source reference. Unverified demo carriers must be explicitly flagged with `source_reference = "DEMO DATA — UNVERIFIED"`.
● **No AI-triggered `submitted` transition**, under any circumstance.
● **No silent exception handling** — every failure gets one of the explicit states above.
● **No hardcoded 270-day deadline math** — use `dateutil.relativedelta(months=9)` for Carmack statutory limits.
● **No mischaracterized legal citations** — cite NMFC Item 300105 accurately as minimum filing requirements, not a demand narrative template.
● **No live scope creep past Cargo Damage in Phase 0/1** — seed claims for shortage/lost-cargo are static display-only rows for UI testing.
● **No mobile-specific build in Phase 0/1** — responsive web is sufficient.
● **No multi-party (broker + carrier + shipper) collaboration workspace** before the first pilot.
● **No predictive/intelligence features** before real outcome data exists (Phase 4+ only).
● **No feature added because "it sounds advanced"** — every addition should trace back to a specific line in `implementation_plan.md` or `phases.md`.
