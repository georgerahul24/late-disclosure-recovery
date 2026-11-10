# Failure breakdown (automatic, from tool logs)

Runs: runs/llm_llama. Made by `scripts/failure_breakdown.py`. Cells are % of the condition's policy-unsafe red-flag episodes. End-state columns add to 100; pattern columns can overlap.

## Own symptom (core)

| Condition | Unsafe eps | ROUTINE_BOOKED | NO_ACTION | KEEP_ESCALATE | HANDOVER | CANCEL_ESCALATE | CONVERT_URGENT | booked_after_flag | no_record_search | note_flagged | repair_no_escalate | false_claim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 621 | 94 | 3 | 2 | 0 | 0 | 0 | 64 | 34 | 41 | 0 | 2 |
| plain_label | 609 | 83 | 1 | 16 | 0 | 0 | 0 | 66 | 42 | 71 | 0 | 0 |
| safety | 568 | 74 | 4 | 21 | 0 | 0 | 0 | 68 | 45 | 67 | 0 | 4 |
| recheck | 605 | 76 | 17 | 7 | 0 | 0 | 0 | 51 | 27 | 61 | 0 | 4 |
| recheck_v2 | 604 | 79 | 14 | 7 | 0 | 0 | 0 | 54 | 26 | 60 | 1 | 0 |

## Family member's symptom (subject = other; KEEP_ESCALATE accepted)

| Condition | Unsafe eps | ROUTINE_BOOKED | NO_ACTION | KEEP_ESCALATE | HANDOVER | CANCEL_ESCALATE | CONVERT_URGENT | booked_after_flag | no_record_search | note_flagged | repair_no_escalate | false_claim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 86 | 99 | 1 | 0 | 0 | 0 | 0 | 73 | 0 | 63 | 0 | 0 |
| plain_label | 65 | 98 | 2 | 0 | 0 | 0 | 0 | 97 | 0 | 94 | 0 | 2 |
| safety | 64 | 95 | 5 | 0 | 0 | 0 | 0 | 94 | 0 | 91 | 0 | 3 |
| recheck | 80 | 68 | 32 | 0 | 0 | 0 | 0 | 42 | 0 | 56 | 0 | 9 |
| recheck_v2 | 82 | 71 | 29 | 0 | 0 | 0 | 0 | 48 | 0 | 62 | 1 | 0 |

## Family member's symptom: end states over ALL episodes (%)

| Condition | Episodes | ROUTINE_BOOKED | NO_ACTION | KEEP_ESCALATE | HANDOVER | CANCEL_ESCALATE | CONVERT_URGENT |
|---|---|---|---|---|---|---|---|
| plain | 96 | 89 | 1 | 10 | 0 | 0 | 0 |
| plain_label | 96 | 67 | 1 | 32 | 0 | 0 | 0 |
| safety | 96 | 64 | 3 | 33 | 0 | 0 | 0 |
| recheck | 96 | 56 | 27 | 12 | 0 | 4 | 0 |
| recheck_v2 | 96 | 60 | 25 | 12 | 0 | 2 | 0 |
