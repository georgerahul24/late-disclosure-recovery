# recheck/controllers/ (scripted, non-LLM controllers)

`ScriptedController(detector, grounding, revision, readback, invariant)`. These are deterministic, so they are used for the pilot, as upper and lower bounds, and as the DSC baseline.

| Switch | Values | Meaning |
|---|---|---|
| detector | Detector or None | None means it never detects anything |
| grounding | ignore / always / record | record-dependent families: treat as benign / always urgent / check `rules.evaluate` on the record |
| revision | none / cancel / convert | what to do with open routine bookings in the ledger once a red flag is urgent |
| readback | bool | `list_bookings`, retry once, else hand over. This also finds bookings hidden by a lost response. |
| invariant | bool | after every turn: if escalated, cancel any routine booking still in the ledger |

Presets:
- `book_only()`: never detects, always books. Must score 100% unsafe.
- `rule_gate(kw)`: keyword detector, ignores the record, never revises. This is the CareConnect pattern.
- `dsc(det)`: record grounding + cancel + invariant + read-back. **The strong non-LLM baseline.** Any LLM system must beat this one, not only the gate.

Booking behaviour, once there is no red flag:
- If the message mentions free, check or available (or nothing has been offered yet), it calls `check_availability`.
- If the message mentions "book" and slots were offered, it books the first one. If that slot is taken, it re-checks and tries the next.

The record check uses `ToolHarness.privileged_record()` (direct record access). It also calls `search_record`, so the logs look like retrieval happened. This is allowed only for deterministic controllers.
