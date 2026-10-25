# scripts/ (command line entry points)

Run from the repo root with the venv Python (`.venv/bin/python scripts/<name>.py`).

| Script | What it does | Output |
|---|---|---|
| `make_dev_data.py` | Rebuilds the dev fixtures (patients, scenarios, policy, seeds). It does not overwrite the frozen keyword list. Deterministic (seed 7). | `data/dev/*.json`, `data/detector/*.json` |
| `run_pilot.py` | Scripted-controller pilot: 13 controllers on the main episodes, plus a tool-fault table. Asserts the sanity checks (oracle 0% unsafe and 100% completion, book-only 100% unsafe). CPU only, about 1 second. | `runs/pilot/summary.md`, `summary.json`, one JSONL per controller |
| `run_llm.py` | Runs LLM conditions against one or more OpenAI-compatible servers in parallel threads. Can be resumed (skips finished episodes in the JSONL). Options: `--conditions`, `--seeds`, `--detector tfidf|oracle|lora:<dir>`, `--phrasings`, `--faults`, `--limit`, `--data`, `--out`. | `<out>/<cond>_s<seed>.jsonl`, `<out>/summary.md`, `summary.json` |

Every JSONL line is one `EpisodeResult`: episode, agent, scenario meta, transcript, tool calls, ledger, notes, final backend state, disclosure turn, grade, and for LLM runs a usage block (model calls, tokens, NOTE parse failures). To inspect one trace:

```bash
head -1 runs/llm/recheck_s0.jsonl | python -m json.tool | less
```
