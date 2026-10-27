# ai report/ (mid-submission report)

- `report.tex` is the report source and `report.pdf` is the built report.
- `tables/` holds **generated** tables and number macros (`numbers.tex`). Never edit them by hand.

## Rebuild after new runs

From the repo root:

```bash
cluster/sync.sh pull
.venv/bin/python scripts/summarize_runs.py --runs runs/llm_main runs/scripted_main runs/scripted_faults --out results/mid_v1.md
.venv/bin/python scripts/timing_model.py --runs runs/llm_main --scenarios data/eval/scenarios_v1.json \
    --conditions plain,plain_label --metric unsafe_policy --out results/mid_timing_policy.md
.venv/bin/python scripts/make_report_tables.py --runs runs/llm_main runs/scripted_main runs/scripted_faults \
    --detectors results/detectors_eval_v1.json --gee results/mid_timing_policy.md --out "ai report/tables"
cd "ai report" && latexmk -pdf report.tex
```

The version from 28 Oct uses only the conditions that had finished all 3 seeds: Plain, Plain + Label, RECHECK and Hybrid (copied to `runs/mid`), plus the scripted runs. Safety, the ablations and the LLM faults were still running.
