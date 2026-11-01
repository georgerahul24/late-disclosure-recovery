"""Re-grade every stored episode with the current grader and compare.

    python scripts/regrade_check.py --runs runs/llm_main runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults

Each episode line stores the grade made when it ran. If the grader changed
after some runs started, stored grades could be stale. This rebuilds each
EpisodeResult from the stored transcript, calls, notes and final backend
state, grades it again, and counts any field that differs. Exit code 1 if
anything differs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.grader import grade_episode  # noqa: E402
from recheck.records import load_patients  # noqa: E402
from recheck.runner import EpisodeResult  # noqa: E402
from recheck.scenarios import load_scenarios  # noqa: E402

FIELDS = ["red_flag", "end_state", "acceptable", "unsafe_policy", "unsafe_strict", "unsafe_lenient",
          "policy_strict_disagree", "stage", "stage_strict", "completed", "over_escalated", "duplicate_booking",
          "false_claims", "unsafe_actions", "elicited", "timing_violated"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--patients", default=str(ROOT / "data/eval/patients_v1.json"))
    args = ap.parse_args()
    SC = load_scenarios(args.scenarios)
    P = load_patients(args.patients)
    P = P if isinstance(P, dict) else {p.patient_id: p for p in P}
    n = 0
    diff = Counter()
    examples = []
    for d in args.runs:
        for f in sorted(Path(d).glob("*_s[0-9]*.jsonl")):  # episode files only (not .judge.jsonl or the label sample)
            if f.name.endswith(".judge.jsonl"):
                continue
            for line in f.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                res = EpisodeResult(**{k: r[k] for k in ("episode", "agent", "scenario", "transcript", "calls", "ledger",
                                                         "notes", "final_state", "disclosed_turn", "timing_violated")})
                sc = SC[r["episode"]["scenario_id"]]
                g = json.loads(json.dumps(grade_episode(res, sc, P[sc.patient_id]), default=str))
                n += 1
                for k in FIELDS:
                    if g.get(k) != r["grade"].get(k):
                        diff[(f.parent.name, k)] += 1
                        if len(examples) < 5:
                            examples.append((str(f), r["episode"], k, r["grade"].get(k), g.get(k)))
    print(f"re-graded {n} episodes")
    if diff:
        for (run, k), c in sorted(diff.items()):
            print(f"  DIFF {run} {k}: {c}")
        for e in examples:
            print("  e.g.", e)
        sys.exit(1)
    print("all stored grades match the current grader")


if __name__ == "__main__":
    main()
