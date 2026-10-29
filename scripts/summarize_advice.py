"""Summarise the advice judge over judged runs, and export the labelling sheet.

    python scripts/summarize_advice.py --runs runs/llm_main runs/llm_v2 runs/llm_ablate runs/llm_faults \
        --out results/advice_v1.md --label-sample runs/llm_main/advice_label_sample.jsonl --label-out labelling

Reads <cond>_s<seed>.judge.jsonl next to each <cond>_s<seed>.jsonl. Per
condition (core-style filter: no fault), the share of episodes where the judge
flagged medical advice in at least one agent turn: overall, in advice-request
scenarios, and in the others. Scenario-level means and 95% bootstrap CIs, as in
summarize_runs.py. Judge outputs are UNVALIDATED until scripts/score_labels.py
has the human labels.

--label-sample turns the hidden-verdict sample made by judge_runs.py into
labelling/advice_labels.csv, plus advice_labels_meta.json with the share of
turns the judge flagged (needed to reweight the balanced sample).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from recheck.scenarios import load_scenarios  # noqa: E402
from summarize_runs import ci, paired  # noqa: E402

ORDER = ["plain", "safety", "plain_label", "recheck", "hybrid", "recheck_v2"]


def key(e: dict) -> str:
    return json.dumps(e, sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--label-sample")
    ap.add_argument("--label-out", default="labelling")
    args = ap.parse_args()
    SC = load_scenarios(args.scenarios)
    rows = defaultdict(list)  # cond -> [(episode, advice_any, n_fail_turns)]
    missing = defaultdict(int)
    flagged_turns = total_turns = 0
    for d in args.runs:
        for f in sorted(Path(d).glob("*_s*.judge.jsonl")):
            cond = f.name.rsplit("_s", 1)[0]
            judged = {}
            for line in f.read_text().splitlines():
                try:
                    j = json.loads(line)
                except json.JSONDecodeError:  # half-written line from a killed job
                    continue
                judged[key(j["episode"])] = j["turns"]
            src = f.with_name(f.name.replace(".judge.jsonl", ".jsonl"))
            for line in src.read_text().splitlines():
                if not line.strip():
                    continue
                e = json.loads(line)["episode"]
                t = judged.get(key(e))
                if t is None:
                    missing[cond] += 1
                    continue
                if Path(d).name == "llm_main":
                    flagged_turns += sum(1 for x in t if x["advice"])
                    total_turns += sum(1 for x in t if x["advice"] is not None)
                rows[cond].append((e, any(x["advice"] for x in t), sum(1 for x in t if not x["parse_ok"])))
    L = ["# Advice judge results (UNVALIDATED until scored against human labels)", "",
         f"Runs: {', '.join(args.runs)}. Judge: llama3.1:8b-instruct-q8_0, JSON mode, temperature 0. "
         "Made by `scripts/summarize_advice.py`. Cells: % of episodes (no tool fault) with at least one agent turn "
         "the judge flagged as medical advice; scenario-level mean [95% bootstrap CI].", "",
         "| Condition | Episodes judged | Not judged | Any advice [95% CI] | Advice-request scenarios | Other scenarios | "
         "Judge parse failures (turns) |", "|---|---|---|---|---|---|---|"]
    scen = {}
    for c in [c for c in ORDER if c in rows] + sorted(set(rows) - set(ORDER)):
        rs = [r for r in rows[c] if r[0]["fault"] == "none"]

        def sc_mean(where):
            d = defaultdict(list)
            for e, a, _ in rs:
                if where(SC[e["scenario_id"]]):
                    d[e["scenario_id"]].append(float(a))
            return {k: mean(v) for k, v in d.items()}
        allm = sc_mean(lambda s: True)
        scen[c] = allm
        a, lo, hi = ci(list(allm.values()))
        adv = sc_mean(lambda s: bool(s.advice_request))
        oth = sc_mean(lambda s: not s.advice_request)
        L.append(f"| {c} | {len(rs)} | {missing[c]} | {100 * a:.1f} [{100 * lo:.1f}, {100 * hi:.1f}] | "
                 f"{100 * mean(adv.values()):.1f} | {100 * mean(oth.values()):.1f} | {sum(r[2] for r in rs)} |")
    L += ["", "Paired differences (scenario level, points, exploratory):", "", "| A - B | Diff [95% CI] |", "|---|---|"]
    for a_, b_ in (("safety", "plain"), ("recheck", "plain"), ("recheck_v2", "recheck"), ("plain_label", "plain")):
        if a_ in scen and b_ in scen:
            p = paired(scen[a_], scen[b_])
            if p:
                L.append(f"| {a_} - {b_} | {100 * p['diff']:.1f} [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] |")
    if total_turns:
        L += ["", f"Share of judged agent turns flagged as advice in runs/llm_main: {flagged_turns} / {total_turns} "
                  f"= {100 * flagged_turns / total_turns:.2f}%"]
    Path(args.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))

    if args.label_sample and Path(args.label_sample).exists():
        out = Path(args.label_out)
        out.mkdir(parents=True, exist_ok=True)
        items = [json.loads(x) for x in Path(args.label_sample).read_text().splitlines() if x.strip()]
        with (out / "advice_labels.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "patient_message", "agent_reply", "YOUR_advice (yes/no)", "YOUR_quote", "YOUR_comment",
                        "judge_advice (hidden: do not look until done)", "run", "turn"])
            for it in items:
                w.writerow([it["id"], it["patient"], it["agent"], "", "", "", it["_judge_hidden"], it["run"], it["turn"]])
        (out / "advice_labels_meta.json").write_text(json.dumps(
            {"judge_flagged_turn_share_llm_main": flagged_turns / total_turns if total_turns else None,
             "flagged_turns": flagged_turns, "judged_turns": total_turns,
             "sampling": "balanced on the judge verdict (half flagged, half not), random seed 0"}, indent=1))
        print(f"wrote {out / 'advice_labels.csv'} ({len(items)} rows)")


if __name__ == "__main__":
    main()
