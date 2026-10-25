# scripts/ (command line entry points)

Run from the repo root with the venv Python (`.venv/bin/python scripts/<name>.py`).

| Script | What it does | Output |
|---|---|---|
| `make_dev_data.py` | Rebuilds the dev fixtures (patients, scenarios, policy, seeds). It does not overwrite the frozen keyword list. Deterministic (seed 7). | `data/dev/*.json`, `data/detector/*.json` |
| `run_pilot.py` | Scripted-controller pilot: 13 controllers on the main episodes, plus a tool-fault table. Asserts the sanity checks (oracle 0% unsafe and 100% completion, book-only 100% unsafe). CPU only, about 1 second. | `runs/pilot/summary.md`, `summary.json`, one JSONL per controller |
| `synthea_to_records.py` | Converts Synthea CSVs (node scratch) into `PatientRecord` JSON and rule-based pools. It streams the CSVs, so the multi-GB observations file never sits in memory. | `data/synthea/patients.json`, `pools.json`, `conversion_report.md` |
| `build_eval.py` | Builds the evaluation set from phrasings plus Synthea pools: matched pairs, sex and age constraints, extra episode types, verified sources, and a leakage report. | `data/eval/scenarios_v1.json`, `patients_v1.json`, `BUILD_REPORT.md` |
| `decontaminate.py` | Drops training texts that share n or more consecutive words (default 6) with any eval text. | `<out>.json`, `<out>.report.json` |
| `paraphrase_seeds.py` | Makes LLM paraphrases of the detector seeds (training only), with a filter and a label-check call. | `data/detector/paraphrases_v1.json` |
| `train_detector.py` | LoRA 5-way classifier: Qwen2.5 base, grouped 85/15 split, fp16 base with fp32 trainable weights. Fails if the paraphrases file is missing. | adapter dir with `metrics.json` |
| `eval_detectors.py` | Keyword vs TF-IDF vs prompted LLM vs LoRA on the eval text: symptom-only, reworded and in-message. | `runs/detector_eval/summary.md`, `results_*.json` |
| `judge_runs.py` | LLM advice judge over finished runs (UNVALIDATED). It also exports a balanced sample for human labels. | `*.judge.jsonl`, `advice_summary.md`, `advice_label_sample.jsonl` |
| `summarize_runs.py` | Full analysis: core table, H1, H2/H2b/H2c with Holm, TOST, pass^k, third-party, extras and faults. | `results/<name>.md` and `.json` |
| `make_tables.py` | Turns the `summarize_runs.py` JSON into LaTeX tables for the paper. | `paper/sections/results_tables.tex` |
| `run_llm.py` | Runs LLM conditions against one or more OpenAI-compatible servers in parallel threads. Can be resumed (skips finished episodes in the JSONL). Options: `--conditions`, `--seeds`, `--detector tfidf|oracle|lora:<dir>`, `--phrasings`, `--faults`, `--limit`, `--data`, `--out`. | `<out>/<cond>_s<seed>.jsonl`, `<out>/summary.md`, `summary.json` |

Every JSONL line is one `EpisodeResult`: episode, agent, scenario meta, transcript, tool calls, ledger, notes, final backend state, disclosure turn, grade, and for LLM runs a usage block (model calls, tokens, NOTE parse failures). To inspect one trace:

```bash
head -1 runs/llm/recheck_s0.jsonl | python -m json.tool | less
```
