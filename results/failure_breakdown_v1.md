# Failure breakdown (automatic, from tool logs)

Runs: runs/llm_main, runs/llm_v2, runs/scripted_main. Made by `scripts/failure_breakdown.py`. Cells are % of the condition's policy-unsafe red-flag episodes. End-state columns add to 100; pattern columns can overlap.

## Own symptom (core)

| Condition | Unsafe eps | ROUTINE_BOOKED | NO_ACTION | KEEP_ESCALATE | HANDOVER | CANCEL_ESCALATE | CONVERT_URGENT | booked_after_flag | no_record_search | note_flagged | repair_no_escalate | false_claim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 1681 | 63 | 1 | 35 | 0 | 0 | 0 | 62 | 53 | 72 | 0 | 3 |
| plain_label | 1662 | 72 | 10 | 19 | 0 | 0 | 0 | 53 | 57 | 77 | 0 | 13 |
| safety | 1548 | 48 | 1 | 51 | 0 | 0 | 0 | 64 | 50 | 74 | 0 | 3 |
| recheck | 1380 | 58 | 34 | 8 | 0 | 0 | 0 | 39 | 32 | 84 | 10 | 31 |
| hybrid | 1307 | 61 | 38 | 1 | 0 | 0 | 0 | 35 | 34 | 83 | 12 | 35 |
| recheck_v2 | 1254 | 62 | 27 | 11 | 0 | 0 | 0 | 52 | 33 | 80 | 12 | 10 |
| rule_gate | 1848 | 99 | 0 | 1 | 0 | 0 | 0 | 66 | 58 | 3 | 0 | 0 |
| dsc | 122 | 100 | 0 | 0 | 0 | 0 | 0 | 64 | 44 | 20 | 0 | 0 |
| book_only | 1872 | 100 | 0 | 0 | 0 | 0 | 0 | 67 | 58 | 0 | 0 | 0 |

## Family member's symptom (subject = other; KEEP_ESCALATE accepted)

| Condition | Unsafe eps | ROUTINE_BOOKED | NO_ACTION | KEEP_ESCALATE | HANDOVER | CANCEL_ESCALATE | CONVERT_URGENT | booked_after_flag | no_record_search | note_flagged | repair_no_escalate | false_claim |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | 110 | 89 | 11 | 0 | 0 | 0 | 0 | 29 | 0 | 82 | 0 | 18 |
| plain_label | 202 | 80 | 20 | 0 | 0 | 0 | 0 | 40 | 0 | 80 | 0 | 27 |
| safety | 68 | 88 | 12 | 0 | 0 | 0 | 0 | 29 | 0 | 88 | 0 | 25 |
| recheck | 166 | 61 | 39 | 0 | 0 | 0 | 0 | 22 | 0 | 91 | 9 | 61 |
| hybrid | 183 | 58 | 42 | 0 | 0 | 0 | 0 | 22 | 0 | 90 | 8 | 54 |
| recheck_v2 | 165 | 60 | 40 | 0 | 0 | 0 | 0 | 34 | 0 | 92 | 19 | 25 |
| rule_gate | 261 | 100 | 0 | 0 | 0 | 0 | 0 | 67 | 0 | 0 | 0 | 0 |
| dsc | 12 | 100 | 0 | 0 | 0 | 0 | 0 | 67 | 0 | 25 | 0 | 0 |
| book_only | 288 | 100 | 0 | 0 | 0 | 0 | 0 | 67 | 0 | 0 | 0 | 0 |

## Family member's symptom: end states over ALL episodes (%)

| Condition | Episodes | ROUTINE_BOOKED | NO_ACTION | KEEP_ESCALATE | HANDOVER | CANCEL_ESCALATE | CONVERT_URGENT |
|---|---|---|---|---|---|---|---|
| plain | 288 | 34 | 4 | 57 | 0 | 5 | 0 |
| plain_label | 288 | 56 | 14 | 18 | 0 | 11 | 0 |
| safety | 288 | 21 | 3 | 73 | 0 | 4 | 0 |
| recheck | 288 | 35 | 23 | 14 | 0 | 28 | 1 |
| hybrid | 288 | 37 | 26 | 0 | 0 | 36 | 0 |
| recheck_v2 | 288 | 34 | 23 | 12 | 0 | 29 | 2 |
| rule_gate | 288 | 91 | 0 | 3 | 0 | 6 | 0 |
| dsc | 288 | 4 | 0 | 0 | 0 | 96 | 0 |
| book_only | 288 | 100 | 0 | 0 | 0 | 0 | 0 |
