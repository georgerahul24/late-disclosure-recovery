# Extra facts: runs/llm_main, runs/llm_v2, runs/llm_ablate, runs/llm_faults, runs/scripted_main, runs/scripted_faults

Counts over all episodes each condition ran (all phrasings, timings, seeds and faults). Made by `scripts/extra_facts.py`.

| Condition | Episodes | Red-flag eps | Policy/strict disagree (red-flag eps) | Timing violated | Eps with a false claim | False claims by action | Mean tool calls / ep | Mean tokens in / out per ep |
|---|---|---|---|---|---|---|---|---|
| book_only | 4716 | 2448 | 0 (0.0%) | 0 | 0 | - | - | - (no LLM) |
| dsc | 6420 | 3396 | 0 (0.0%) | 0 | 0 | - | - | - (no LLM) |
| hybrid | 6420 | 3396 | 48 (1.4%) | 209 | 1805 | book 1111, cancel 325, escalate 616 | 7.0 | 14697 / 624 |
| plain | 6420 | 3396 | 465 (13.7%) | 221 | 784 | book 731, escalate 105 | 6.1 | 10186 / 562 |
| plain_label | 4716 | 2448 | 200 (8.2%) | 0 | 454 | book 321, cancel 4, escalate 178 | 6.0 | 10102 / 526 |
| recheck | 6420 | 3396 | 148 (4.4%) | 206 | 1750 | book 1121, cancel 327, escalate 549 | 7.1 | 14780 / 628 |
| recheck_detector_tool | 786 | 408 | 25 (6.1%) | 0 | 132 | book 93, cancel 15, escalate 52 | 6.9 | 14386 / 683 |
| recheck_full_record | 786 | 408 | 20 (4.9%) | 1 | 172 | book 96, cancel 53, escalate 49 | 7.1 | 17464 / 640 |
| recheck_no_detector | 786 | 408 | 25 (6.1%) | 0 | 146 | book 93, cancel 32, escalate 64 | 6.5 | 13382 / 710 |
| recheck_no_ledger | 786 | 408 | 23 (5.6%) | 0 | 148 | book 64, cancel 33, escalate 79 | 6.7 | 13301 / 612 |
| recheck_no_readback | 2490 | 1356 | 63 (4.6%) | 211 | 824 | book 533, cancel 136, escalate 287 | 6.8 | 13516 / 610 |
| recheck_no_retrieval | 786 | 408 | 29 (7.1%) | 1 | 176 | book 93, cancel 61, escalate 60 | 6.7 | 12953 / 641 |
| recheck_single_pass | 786 | 408 | 19 (4.7%) | 0 | 270 | book 113, cancel 116, escalate 97 | 6.2 | 10699 / 515 |
| recheck_v2 | 4716 | 2448 | 103 (4.2%) | 1 | 324 | book 126, cancel 29, escalate 201 | 7.5 | 16027 / 677 |
| rule_gate | 4716 | 2448 | 9 (0.4%) | 0 | 0 | - | - | - (no LLM) |
| safety | 4716 | 2448 | 587 (24.0%) | 1 | 128 | book 60, escalate 81 | 6.2 | 10534 / 582 |

Total episodes: 56466

## End states on red-flag episodes, by fault

Counts of the final backend end state (see docs/design.md section 3).

| Condition | Fault | Episodes | End states |
|---|---|---|---|
| book_only | none | 2448 | ROUTINE_BOOKED 2448 |
| dsc | book_lost_response | 408 | CANCEL_ESCALATE 385, ROUTINE_BOOKED 23 |
| dsc | cancel_fails_once | 132 | CANCEL_ESCALATE 127, ROUTINE_BOOKED 5 |
| dsc | none | 2448 | CANCEL_ESCALATE 2225, ROUTINE_BOOKED 223 |
| dsc | slot_taken | 408 | CANCEL_ESCALATE 385, ROUTINE_BOOKED 23 |
| hybrid | book_lost_response | 408 | CANCEL_ESCALATE 82, CONVERT_URGENT 1, KEEP_ESCALATE 74, NO_ACTION 87, ROUTINE_BOOKED 164 |
| hybrid | cancel_fails_once | 132 | CANCEL_ESCALATE 29, CONVERT_URGENT 8, KEEP_ESCALATE 14, NO_ACTION 6, ROUTINE_BOOKED 75 |
| hybrid | none | 2448 | CANCEL_ESCALATE 711, CONVERT_URGENT 10, KEEP_ESCALATE 34, NO_ACTION 644, ROUTINE_BOOKED 1049 |
| hybrid | slot_taken | 408 | CANCEL_ESCALATE 152, KEEP_ESCALATE 2, NO_ACTION 163, ROUTINE_BOOKED 91 |
| plain | book_lost_response | 408 | CANCEL_ESCALATE 13, KEEP_ESCALATE 182, NO_ACTION 16, ROUTINE_BOOKED 197 |
| plain | cancel_fails_once | 132 | KEEP_ESCALATE 32, ROUTINE_BOOKED 100 |
| plain | none | 2448 | CANCEL_ESCALATE 43, CONVERT_URGENT 1, KEEP_ESCALATE 1009, NO_ACTION 61, ROUTINE_BOOKED 1334 |
| plain | slot_taken | 408 | CANCEL_ESCALATE 169, KEEP_ESCALATE 28, NO_ACTION 152, ROUTINE_BOOKED 59 |
| plain_label | none | 2448 | CANCEL_ESCALATE 123, KEEP_ESCALATE 538, NO_ACTION 217, ROUTINE_BOOKED 1570 |
| recheck | book_lost_response | 408 | CANCEL_ESCALATE 74, CONVERT_URGENT 1, KEEP_ESCALATE 69, NO_ACTION 91, ROUTINE_BOOKED 173 |
| recheck | cancel_fails_once | 132 | CANCEL_ESCALATE 5, CONVERT_URGENT 12, KEEP_ESCALATE 37, NO_ACTION 3, ROUTINE_BOOKED 75 |
| recheck | none | 2448 | CANCEL_ESCALATE 564, CONVERT_URGENT 13, KEEP_ESCALATE 215, NO_ACTION 615, ROUTINE_BOOKED 1041 |
| recheck | slot_taken | 408 | CANCEL_ESCALATE 135, CONVERT_URGENT 1, KEEP_ESCALATE 13, NO_ACTION 186, ROUTINE_BOOKED 73 |
| recheck_detector_tool | none | 408 | CANCEL_ESCALATE 104, CONVERT_URGENT 5, KEEP_ESCALATE 60, NO_ACTION 67, ROUTINE_BOOKED 172 |
| recheck_full_record | none | 408 | CANCEL_ESCALATE 81, CONVERT_URGENT 2, KEEP_ESCALATE 59, NO_ACTION 98, ROUTINE_BOOKED 168 |
| recheck_no_detector | none | 408 | CANCEL_ESCALATE 73, CONVERT_URGENT 2, KEEP_ESCALATE 73, NO_ACTION 57, ROUTINE_BOOKED 203 |
| recheck_no_ledger | none | 408 | CANCEL_ESCALATE 96, CONVERT_URGENT 4, KEEP_ESCALATE 64, NO_ACTION 75, ROUTINE_BOOKED 169 |
| recheck_no_readback | book_lost_response | 408 | CANCEL_ESCALATE 61, KEEP_ESCALATE 88, NO_ACTION 83, ROUTINE_BOOKED 176 |
| recheck_no_readback | cancel_fails_once | 132 | CONVERT_URGENT 13, KEEP_ESCALATE 24, NO_ACTION 3, ROUTINE_BOOKED 92 |
| recheck_no_readback | none | 408 | CANCEL_ESCALATE 92, CONVERT_URGENT 1, KEEP_ESCALATE 41, NO_ACTION 88, ROUTINE_BOOKED 186 |
| recheck_no_readback | slot_taken | 408 | CANCEL_ESCALATE 118, KEEP_ESCALATE 17, NO_ACTION 193, ROUTINE_BOOKED 80 |
| recheck_no_retrieval | none | 408 | CANCEL_ESCALATE 105, CONVERT_URGENT 2, KEEP_ESCALATE 80, NO_ACTION 71, ROUTINE_BOOKED 150 |
| recheck_single_pass | none | 408 | CANCEL_ESCALATE 41, KEEP_ESCALATE 37, NO_ACTION 141, ROUTINE_BOOKED 189 |
| recheck_v2 | none | 2448 | CANCEL_ESCALATE 698, CONVERT_URGENT 27, KEEP_ESCALATE 253, NO_ACTION 455, ROUTINE_BOOKED 1015 |
| rule_gate | none | 2448 | CANCEL_ESCALATE 42, KEEP_ESCALATE 21, ROUTINE_BOOKED 2385 |
| safety | none | 2448 | CANCEL_ESCALATE 37, KEEP_ESCALATE 1452, NO_ACTION 27, ROUTINE_BOOKED 932 |
