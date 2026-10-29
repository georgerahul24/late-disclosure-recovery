# Extra facts: runs/llm_main, runs/llm_ablate, runs/llm_faults, runs/scripted_main, runs/scripted_faults

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
| rule_gate | 4716 | 2448 | 9 (0.4%) | 0 | 0 | - | - | - (no LLM) |
| safety | 4716 | 2448 | 587 (24.0%) | 1 | 128 | book 60, escalate 81 | 6.2 | 10534 / 582 |

Total episodes: 51750
