# Extra facts: runs/llm_qwen14b

Counts over all episodes each condition ran (all phrasings, timings, seeds and faults). Made by `scripts/extra_facts.py`.

| Condition | Episodes | Red-flag eps | Policy/strict disagree (red-flag eps) | Timing violated | Eps with a false claim | False claims by action | Mean tool calls / ep | Mean tokens in / out per ep |
|---|---|---|---|---|---|---|---|---|
| plain | 1572 | 816 | 114 (14.0%) | 276 | 152 | book 156, escalate 11 | 8.0 | 15027 / 916 |
| plain_label | 1572 | 816 | 95 (11.6%) | 108 | 303 | book 299, cancel 4, escalate 18 | 7.6 | 14090 / 828 |
| recheck | 1572 | 816 | 98 (12.0%) | 5 | 105 | book 77, cancel 24, escalate 13 | 8.0 | 19471 / 858 |
| recheck_v2 | 1572 | 816 | 104 (12.7%) | 3 | 5 | book 1, cancel 5, escalate 1 | 8.2 | 19923 / 874 |
| safety | 1572 | 816 | 175 (21.4%) | 207 | 178 | book 175, cancel 2, escalate 15 | 9.0 | 18054 / 1063 |

Total episodes: 7860

## End states on red-flag episodes, by fault

Counts of the final backend end state (see docs/design.md section 3).

| Condition | Fault | Episodes | End states |
|---|---|---|---|
| plain | none | 816 | CANCEL_ESCALATE 109, KEEP_ESCALATE 286, NO_ACTION 150, ROUTINE_BOOKED 271 |
| plain_label | none | 816 | CANCEL_ESCALATE 111, CONVERT_URGENT 1, KEEP_ESCALATE 238, NO_ACTION 142, ROUTINE_BOOKED 324 |
| recheck | none | 816 | CANCEL_ESCALATE 336, CONVERT_URGENT 82, KEEP_ESCALATE 213, NO_ACTION 37, ROUTINE_BOOKED 148 |
| recheck_v2 | none | 816 | CANCEL_ESCALATE 342, CONVERT_URGENT 98, KEEP_ESCALATE 210, NO_ACTION 11, ROUTINE_BOOKED 155 |
| safety | none | 816 | CANCEL_ESCALATE 124, KEEP_ESCALATE 406, NO_ACTION 86, ROUTINE_BOOKED 200 |
