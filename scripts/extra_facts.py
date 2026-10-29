"""Extra counts for the paper that summarize_runs.py does not print.

    python scripts/extra_facts.py --runs runs/llm_main runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults \
        --out results/extra_facts_v1.md

Per condition, over ALL episodes it ran (every phrasing, timing, seed, fault):
  - episodes, red-flag episodes
  - policy/strict disagreement on red-flag episodes (reviewer pointer)
  - timing_violated episodes (the planned disclosure point could not happen)
  - false claims by claimed action (book / cancel / escalate ...)
  - mean tool calls and tokens per episode
Plain counts; no resampling.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from summarize_runs import load  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = load(args.runs)
    L = [f"# Extra facts: {', '.join(args.runs)}", "",
         "Counts over all episodes each condition ran (all phrasings, timings, seeds and faults). Made by `scripts/extra_facts.py`.", "",
         "| Condition | Episodes | Red-flag eps | Policy/strict disagree (red-flag eps) | Timing violated | "
         "Eps with a false claim | False claims by action | Mean tool calls / ep | Mean tokens in / out per ep |",
         "|---|---|---|---|---|---|---|---|---|"]
    total = 0
    for c, rows in sorted(data.items()):
        total += len(rows)
        red = [r for r in rows if r["grade"]["red_flag"]]
        dis = sum(1 for r in red if r["grade"].get("policy_strict_disagree"))
        tv = sum(1 for r in rows if r["grade"].get("timing_violated"))
        fc = Counter(x["claim"] for r in rows for x in r["grade"].get("false_claims", []))
        fce = sum(1 for r in rows if r["grade"].get("false_claims"))
        us = [r.get("usage") or {} for r in rows]
        calls = mean(u.get("calls", 0) for u in us) if any(us) else float("nan")
        tin = mean(u.get("tokens_in", 0) for u in us) if any(us) else float("nan")
        tout = mean(u.get("tokens_out", 0) for u in us) if any(us) else float("nan")
        llm = any(u.get("tokens_in") for u in us)  # scripted controllers make no LLM calls
        L.append(f"| {c} | {len(rows)} | {len(red)} | {dis} ({100 * dis / len(red):.1f}%) | {tv} | {fce} | "
                 f"{', '.join(f'{k} {v}' for k, v in sorted(fc.items())) or '-'} | "
                 f"{f'{calls:.1f}' if llm else '-'} | {f'{tin:.0f} / {tout:.0f}' if llm else '- (no LLM)'} |")
    L += ["", f"Total episodes: {total}", "",
          "## End states on red-flag episodes, by fault", "",
          "Counts of the final backend end state (see docs/design.md section 3).", "",
          "| Condition | Fault | Episodes | End states |", "|---|---|---|---|"]
    for c, rows in sorted(data.items()):
        for fault in sorted({r["episode"]["fault"] for r in rows}):
            sub = [r for r in rows if r["grade"]["red_flag"] and r["episode"]["fault"] == fault]
            es = Counter(r["grade"]["end_state"] for r in sub)
            L.append(f"| {c} | {fault} | {len(sub)} | {', '.join(f'{k} {v}' for k, v in sorted(es.items()))} |")
    Path(args.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
