# ai report/ (mid-submission report)

- `report.tex` is the report source and `report.pdf` is the built report.
- `tables/` holds **generated** tables and number macros (`numbers.tex`). Never edit them by hand.

## Rebuild after new runs

From the repo root:

```bash
cluster/sync.sh pull        # or unpack results/runs_v1/*.tar.gz into runs/
.venv/bin/python scripts/summarize_runs.py --runs runs/llm_main runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults \
    --out results/final_v1.md
.venv/bin/python scripts/timing_model.py --runs runs/llm_main --scenarios data/eval/scenarios_v1.json \
    --conditions plain,plain_label,safety,recheck,hybrid --metric unsafe_policy --out results/final_timing_policy.md
.venv/bin/python scripts/make_report_tables.py --runs runs/llm_main runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults \
    --detectors results/detectors_eval_v1.json --gee results/final_timing_policy.md --out "ai report/tables"
cd "ai report" && latexmk -pdf report.tex
```

The version from 29 Oct (git tag `midsem`) uses **all finished runs**: 5 LLM conditions and 3 scripted ones (3 seeds each), 7 RECHECK ablations (seed 0, direct), and tool faults for 4 LLM conditions plus the DSC. That is 51,750 graded episodes. The advice judge has not been run yet, so the report gives no advice-quality numbers.
