# Results: runs/llm_main, runs/llm_v2, runs/llm_ablate, runs/llm_faults, runs/scripted_main, runs/scripted_faults

Unit = scenario (means over timings, phrasings, seeds). 95% CIs: scenario bootstrap, 10,000 resamples.

## 1. Core episodes (volunteered disclosure, own symptom, no fault)

| Condition | Seeds | Red-flag eps | Policy unsafe [95% CI] | Strict unsafe [95% CI] | Lenient | T1 / MID / POST policy | Completion | Over-esc. | Contrast cons. | Stage shares 1/2/3/4/5 | False-claim eps | Valid calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| book_only | 3 | 1872 | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 | 100.0 / 100.0 / 100.0 | 100.0 | 0.0 | 0.0 | 100/0/0/0/0 | 0 | 100.0 |
| dsc | 3 | 1872 | 6.5 [4.2, 9.1] | 6.5 [4.2, 9.1] | 6.5 | 5.1 / 7.4 / 7.1 | 99.6 | 0.4 | 93.3 | 95/5/0/0/0 | 0 | 100.0 |
| hybrid | 3 | 1872 | 69.8 [66.1, 73.6] | 70.4 [66.6, 74.1] | 68.9 | 78.0 / 60.3 / 71.2 | 64.0 | 12.5 | 10.0 | 17/43/15/5/20 | 960 | 99.1 |
| plain | 3 | 1872 | 89.8 [86.9, 92.5] | 98.7 [98.0, 99.4] | 58.0 | 94.6 / 76.4 / 98.4 | 97.9 | 19.4 | 12.8 | 27/20/52/0/1 | 76 | 95.3 |
| plain_label | 3 | 1872 | 88.8 [86.5, 91.0] | 95.5 [94.0, 96.8] | 72.1 | 97.1 / 69.9 / 99.4 | 94.0 | 13.1 | 11.1 | 21/36/40/0/3 | 347 | 96.1 |
| recheck | 3 | 1872 | 73.7 [70.4, 76.9] | 75.9 [72.5, 79.2] | 67.9 | 88.0 / 59.6 / 73.6 | 66.4 | 12.8 | 9.4 | 16/40/21/4/19 | 890 | 98.9 |
| recheck_detector_tool | 1 | 312 | 70.8 [65.4, 76.0] | 74.7 [68.9, 80.1] | 59.9 | 78.8 / 61.5 / 72.1 | 77.2 | 11.1 | 11.7 | 6/52/22/8/12 | 114 | 98.0 |
| recheck_full_record | 1 | 312 | 76.0 [71.5, 80.1] | 78.8 [74.7, 82.7] | 64.1 | 89.4 / 60.6 / 77.9 | 65.8 | 11.7 | 10.0 | 17/35/27/2/19 | 137 | 98.5 |
| recheck_no_detector | 1 | 312 | 80.4 [76.0, 84.6] | 83.7 [79.5, 87.5] | 66.3 | 91.3 / 67.3 / 82.7 | 79.4 | 10.3 | 6.7 | 7/49/29/8/7 | 120 | 96.6 |
| recheck_no_ledger | 1 | 312 | 75.6 [71.5, 79.8] | 77.9 [74.0, 81.7] | 63.8 | 94.2 / 60.6 / 72.1 | 71.7 | 16.4 | 7.2 | 7/43/32/3/15 | 128 | 96.2 |
| recheck_no_readback | 1 | 312 | 74.7 [69.9, 79.5] | 76.6 [71.8, 81.1] | 66.7 | 92.3 / 55.8 / 76.0 | 70.3 | 10.8 | 10.0 | 9/44/26/6/15 | 169 | 99.0 |
| recheck_no_retrieval | 1 | 312 | 68.9 [63.5, 74.0] | 74.0 [69.2, 78.8] | 54.2 | 87.5 / 46.2 / 73.1 | 69.4 | 18.1 | 11.1 | 17/37/29/5/12 | 147 | 94.8 |
| recheck_single_pass | 1 | 312 | 87.8 [84.3, 91.3] | 90.4 [87.2, 93.3] | 82.4 | 95.2 / 82.7 / 85.6 | 71.7 | 4.7 | 5.6 | 24/36/19/1/21 | 228 | 99.1 |
| recheck_v2 | 3 | 1872 | 67.0 [63.5, 70.5] | 70.0 [66.5, 73.5] | 59.3 | 88.1 / 52.4 / 60.4 | 73.6 | 16.2 | 15.6 | 17/40/22/5/17 | 255 | 98.4 |
| rule_gate | 3 | 1872 | 98.7 [97.4, 99.7] | 98.7 [97.4, 99.7] | 98.1 | 98.1 / 98.1 / 100.0 | 100.0 | 0.0 | 0.0 | 97/2/1/0/0 | 0 | 100.0 |
| safety | 3 | 1872 | 82.7 [77.8, 87.2] | 98.7 [97.9, 99.4] | 40.5 | 89.4 / 70.7 / 88.0 | 99.1 | 37.2 | 34.4 | 23/15/61/1/1 | 77 | 93.8 |

## 2. Hypothesis tests (paired by scenario; difference = A - B in percentage points)

### H1: strict unsafe rises from T1 to POST (plain, safety)

| Condition | POST - T1 strict unsafe [95% CI] | n scenarios | H1 (>=10 pts and CI excludes 0) |
|---|---|---|---|
| plain | 0.5 [-0.2, 1.3] | 104 | not supported |
| safety | 0.5 [0.0, 1.1] | 104 | not supported |
Each comparison uses only the (seed, phrasing) cells that both conditions ran. Ablations ran seed 0 with direct phrasing, so they are compared with RECHECK on those episodes only.


### Confirmatory comparisons on policy unsafe (Holm over 5)

| Test | A | B | A - B [95% CI] | n | p (boot) | p Holm |
|---|---|---|---|---|---|---|
| H2 | recheck | plain | -16.1 [-20.3, -11.8] | 104 | 0.0000 | 0.0000 |
| H2b | recheck | plain_label | -15.1 [-18.7, -11.3] | 104 | 0.0000 | 0.0000 |
| H2c-ledger | recheck_no_ledger | recheck | 8.3 [2.9, 13.8] | 104 | 0.0022 | 0.0022 |
| H2c-single | recheck_single_pass | recheck | 20.5 [15.4, 25.6] | 104 | 0.0000 | 0.0000 |
| Hybrid-DSC | hybrid | dsc | 63.3 [59.6, 67.0] | 104 | 0.0000 | 0.0000 |

Exploratory (policy):

| Test | A | B | A - B [95% CI] | n |
|---|---|---|---|---|
| no_detector | recheck_no_detector | recheck | 13.1 [7.7, 18.6] | 104 |
| detector_tool | recheck_detector_tool | recheck | 3.5 [-2.6, 9.6] | 104 |
| no_retrieval | recheck_no_retrieval | recheck | 1.6 [-4.8, 7.7] | 104 |
| full_record | recheck_full_record | recheck | 8.7 [2.9, 14.4] | 104 |
| no_readback | recheck_no_readback | recheck | 7.4 [1.9, 12.8] | 104 |
| safety-plain | safety | plain | -7.1 [-10.1, -4.4] | 104 |
| rule_gate-plain | rule_gate | plain | 8.9 [5.9, 12.0] | 104 |
| v2-recheck | recheck_v2 | recheck | -6.7 [-9.2, -4.3] | 104 |
| v2-plain | recheck_v2 | plain | -22.8 [-27.3, -18.1] | 104 |

### Confirmatory comparisons on strict unsafe (Holm over 5)

| Test | A | B | A - B [95% CI] | n | p (boot) | p Holm |
|---|---|---|---|---|---|---|
| H2 | recheck | plain | -22.9 [-26.1, -19.6] | 104 | 0.0000 | 0.0000 |
| H2b | recheck | plain_label | -19.6 [-22.8, -16.3] | 104 | 0.0000 | 0.0000 |
| H2c-ledger | recheck_no_ledger | recheck | 5.8 [0.6, 10.9] | 104 | 0.0284 | 0.0284 |
| H2c-single | recheck_single_pass | recheck | 18.3 [13.5, 23.1] | 104 | 0.0000 | 0.0000 |
| Hybrid-DSC | hybrid | dsc | 63.8 [60.1, 67.6] | 104 | 0.0000 | 0.0000 |

Exploratory (strict):

| Test | A | B | A - B [95% CI] | n |
|---|---|---|---|---|
| no_detector | recheck_no_detector | recheck | 11.5 [6.4, 16.7] | 104 |
| detector_tool | recheck_detector_tool | recheck | 2.6 [-3.5, 8.7] | 104 |
| no_retrieval | recheck_no_retrieval | recheck | 1.9 [-4.2, 7.7] | 104 |
| full_record | recheck_full_record | recheck | 6.7 [1.0, 12.2] | 104 |
| no_readback | recheck_no_readback | recheck | 4.5 [-0.6, 9.6] | 104 |
| safety-plain | safety | plain | 0.0 [-0.9, 0.9] | 104 |
| rule_gate-plain | rule_gate | plain | 0.0 [-1.4, 1.2] | 104 |
| v2-recheck | recheck_v2 | recheck | -5.9 [-8.3, -3.5] | 104 |
| v2-plain | recheck_v2 | plain | -28.7 [-32.2, -25.3] | 104 |

Routine completion, RECHECK - Plain: -31.5 [-34.8, -28.2] (H2 is falsified if completion drops by more than 10 points).

Routine completion, RECHECK v2 - plain: -24.3 [-27.8, -20.8].

Routine completion, RECHECK v2 - recheck: 7.2 [5.0, 9.4].

TOST RECHECK vs DSC (policy unsafe, margin +-10 pts): diff 67.2, 90% CI [64.4, 70.1] -> not shown equivalent.

## 3. pass^k over seeds (episode safe under policy in ALL seeds)

| Condition | k | pass^k (red-flag episodes) |
|---|---|---|
| book_only | 3 | 0.0 |
| dsc | 3 | 87.8 |
| hybrid | 3 | 13.1 |
| plain | 3 | 6.7 |
| plain_label | 3 | 6.6 |
| recheck | 3 | 10.9 |
| recheck_v2 | 3 | 13.9 |
| rule_gate | 3 | 1.3 |
| safety | 3 | 14.3 |

## 4. Red flags about a family member (subject=other; KEEP_ESCALATE accepted)

| Condition | Episodes | Policy unsafe | Lenient unsafe |
|---|---|---|---|
| book_only | 288 | 100.0 | 100.0 |
| dsc | 288 | 4.2 | 4.2 |
| hybrid | 288 | 63.5 | 63.5 |
| plain | 288 | 38.2 | 38.2 |
| plain_label | 288 | 70.1 | 70.1 |
| recheck | 288 | 57.6 | 57.6 |
| recheck_detector_tool | 48 | 31.2 | 31.2 |
| recheck_full_record | 48 | 60.4 | 60.4 |
| recheck_no_detector | 48 | 43.8 | 43.8 |
| recheck_no_ledger | 48 | 29.2 | 29.2 |
| recheck_no_readback | 48 | 60.4 | 60.4 |
| recheck_no_retrieval | 48 | 37.5 | 37.5 |
| recheck_single_pass | 48 | 62.5 | 62.5 |
| recheck_v2 | 288 | 57.3 | 57.3 |
| rule_gate | 288 | 90.6 | 90.6 |
| safety | 288 | 23.6 | 23.6 |

## 5. Extra episode types

| Condition | Type | Episodes | Elicited | Policy unsafe (red flags) | Regex advice flag |
|---|---|---|---|---|---|
| book_only | follow-up-only | 72 | 0.0 | 100.0 | 0.0 |
| book_only | advice request | 324 | 100.0 | 100.0 | 0.0 |
| dsc | follow-up-only | 72 | 0.0 | 100.0 | 0.0 |
| dsc | advice request | 324 | 100.0 | 7.9 | 0.0 |
| hybrid | follow-up-only | 72 | 95.8 | 80.6 | 0.0 |
| hybrid | advice request | 324 | 100.0 | 76.4 | 0.0 |
| plain | follow-up-only | 72 | 95.8 | 87.5 | 1.4 |
| plain | advice request | 324 | 100.0 | 80.1 | 0.3 |
| plain_label | follow-up-only | 72 | 97.2 | 100.0 | 0.0 |
| plain_label | advice request | 324 | 100.0 | 87.5 | 1.2 |
| recheck | follow-up-only | 72 | 88.9 | 83.3 | 0.0 |
| recheck | advice request | 324 | 100.0 | 76.4 | 0.0 |
| recheck_detector_tool | follow-up-only | 12 | 100.0 | 83.3 | 0.0 |
| recheck_detector_tool | advice request | 54 | 100.0 | 77.8 | 0.0 |
| recheck_full_record | follow-up-only | 12 | 100.0 | 75.0 | 0.0 |
| recheck_full_record | advice request | 54 | 100.0 | 83.3 | 0.0 |
| recheck_no_detector | follow-up-only | 12 | 100.0 | 66.7 | 0.0 |
| recheck_no_detector | advice request | 54 | 100.0 | 77.8 | 1.9 |
| recheck_no_ledger | follow-up-only | 12 | 100.0 | 66.7 | 0.0 |
| recheck_no_ledger | advice request | 54 | 100.0 | 75.0 | 0.0 |
| recheck_no_readback | follow-up-only | 12 | 91.7 | 75.0 | 0.0 |
| recheck_no_readback | advice request | 54 | 100.0 | 77.8 | 0.0 |
| recheck_no_retrieval | follow-up-only | 12 | 91.7 | 83.3 | 0.0 |
| recheck_no_retrieval | advice request | 54 | 100.0 | 80.6 | 0.0 |
| recheck_single_pass | follow-up-only | 12 | 100.0 | 100.0 | 0.0 |
| recheck_single_pass | advice request | 54 | 100.0 | 88.9 | 0.0 |
| recheck_v2 | follow-up-only | 72 | 94.4 | 62.5 | 0.0 |
| recheck_v2 | advice request | 324 | 100.0 | 72.2 | 0.0 |
| rule_gate | follow-up-only | 72 | 0.0 | 100.0 | 0.0 |
| rule_gate | advice request | 324 | 100.0 | 100.0 | 0.0 |
| safety | follow-up-only | 72 | 98.6 | 76.4 | 0.0 |
| safety | advice request | 324 | 100.0 | 70.8 | 0.3 |

## 6. Tool-fault episodes (red flags)

| Condition | Fault | Episodes | Policy unsafe | Strict unsafe | Stage 4 share |
|---|---|---|---|---|---|
| dsc | book_lost_response | 408 | 5.6 | 5.6 | 0.0 |
| dsc | cancel_fails_once | 132 | 3.8 | 3.8 | 0.0 |
| dsc | slot_taken | 408 | 5.6 | 5.6 | 0.0 |
| hybrid | book_lost_response | 408 | 72.8 | 79.7 | 2.0 |
| hybrid | cancel_fails_once | 132 | 68.9 | 72.0 | 24.2 |
| hybrid | slot_taken | 408 | 62.3 | 62.7 | 0.8 |
| plain | book_lost_response | 408 | 80.4 | 96.8 | 0.0 |
| plain | cancel_fails_once | 132 | 93.2 | 100.0 | 1.6 |
| plain | slot_taken | 408 | 55.6 | 58.6 | 0.0 |
| recheck | book_lost_response | 408 | 74.5 | 81.6 | 2.3 |
| recheck | cancel_fails_once | 132 | 76.5 | 87.1 | 30.7 |
| recheck | slot_taken | 408 | 65.4 | 66.7 | 0.7 |
| recheck_no_readback | book_lost_response | 408 | 77.9 | 85.0 | 0.0 |
| recheck_no_readback | cancel_fails_once | 132 | 83.3 | 90.2 | 28.2 |
| recheck_no_readback | slot_taken | 408 | 68.9 | 71.1 | 1.8 |
