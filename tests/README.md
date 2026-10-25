# tests/

Run: `.venv/bin/python -m pytest -q`. All tests run offline in under a second.

| File | Covers |
|---|---|
| `test_core.py` | Record rules (NG232 aspirin exclusion, stopped-med distractor, exclusions), harness authority, the urgent-slot ban, wrong patient, the ledger, both fault types, end-state labels, simulator timing, stage attribution 1 to 4, read-back finding a lost booking, matched-negative completion, policy vs strict disagreement, episode counts. |
| `test_agents.py` | NOTE parsing, that every LLM condition can be built, and a full RECHECK episode with a scripted fake chat client. That episode includes dropped tool arguments and NOTE stripping. |

When you fix a grading or simulator bug, add a test that would have caught it.
