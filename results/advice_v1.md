# Advice judge results (UNVALIDATED until scored against human labels)

Runs: runs/llm_main, runs/llm_v2, runs/llm_ablate, runs/llm_faults. Judge: llama3.1:8b-instruct-q8_0, JSON mode, temperature 0. Made by `scripts/summarize_advice.py`. Cells: % of episodes (no tool fault) with at least one agent turn the judge flagged as medical advice; scenario-level mean [95% bootstrap CI].

| Condition | Episodes judged | Not judged | Any advice [95% CI] | Advice-request scenarios | Other scenarios | Judge parse failures (turns) |
|---|---|---|---|---|---|---|
| plain | 4716 | 0 | 55.2 [53.0, 57.4] | 81.2 | 53.3 | 1 |
| safety | 4716 | 0 | 52.1 [50.0, 54.3] | 80.9 | 50.1 | 0 |
| plain_label | 4716 | 0 | 62.4 [60.0, 64.7] | 89.8 | 60.4 | 3 |
| recheck | 4716 | 0 | 54.7 [52.5, 57.1] | 75.3 | 53.3 | 0 |
| hybrid | 4716 | 0 | 55.8 [53.6, 58.1] | 78.1 | 54.2 | 2 |
| recheck_v2 | 4716 | 0 | 52.8 [50.6, 55.1] | 70.7 | 51.5 | 2 |
| recheck_detector_tool | 786 | 0 | 66.8 [63.1, 70.4] | 87.0 | 65.3 | 0 |
| recheck_full_record | 786 | 0 | 65.4 [61.9, 69.0] | 81.5 | 64.3 | 0 |
| recheck_no_detector | 786 | 0 | 64.3 [60.6, 67.9] | 81.5 | 63.1 | 0 |
| recheck_no_ledger | 786 | 0 | 56.7 [53.0, 60.2] | 75.9 | 55.3 | 0 |
| recheck_no_readback | 786 | 0 | 63.3 [59.6, 66.9] | 87.0 | 61.6 | 0 |
| recheck_no_retrieval | 786 | 0 | 59.4 [55.6, 63.1] | 81.5 | 57.8 | 0 |
| recheck_single_pass | 786 | 0 | 62.2 [58.6, 65.8] | 87.0 | 60.4 | 0 |

Paired differences (scenario level, points, exploratory):

| A - B | Diff [95% CI] |
|---|---|
| safety - plain | -3.0 [-5.2, -0.9] |
| recheck - plain | -0.4 [-2.9, 2.0] |
| recheck_v2 - recheck | -1.9 [-3.8, 0.0] |
| plain_label - plain | 7.2 [5.1, 9.3] |

Share of judged agent turns flagged as advice in runs/llm_main: 17479 / 94314 = 18.53%
