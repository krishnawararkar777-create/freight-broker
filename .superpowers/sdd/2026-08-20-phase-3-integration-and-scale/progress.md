# SDD ledger — plan: docs/superpowers/plans/2026-08-20-phase-3-integration-and-scale.md

## Pre-flight Conflict Scan Table
| Shared File / Interface | Task Producing | Task Consuming | Status / Scan Finding |
| :--- | :--- | :--- | :--- |
| `apps/api/app/integrations/tms/base.py` (`TMSAdapter`, `NormalizedShipmentData`, `NormalizedDocumentRef`) | Task 1 | Task 2, Task 3 | Clean — Standardized Pydantic schemas and ABC contract |
| `apps/api/app/integrations/tms/mcleod_mock_adapter.py` (`McLeodMockAdapter`) | Task 2 | Task 3 | Clean — Subclasses `TMSAdapter`, implements McLeod format |
| `apps/api/routers/tms.py` (`POST /api/integrations/tms/{provider}/webhook`) | Task 3 | Endpoints | Clean — Integrates with FastAPI app in `main.py` |

---
