"""Run the scripted baselines (book-only, rule gate, DSC) on the eval set with a
chosen detector, per seed, in the same output format as run_llm.py so that
scripts/summarize_runs.py can compare them with the LLM conditions.

    python scripts/run_scripted.py --detector "lora:models/det-qwen2.5-1.5b-instruct-s{seed}" \
        --seeds 0,1,2 --out runs/scripted_main [--faults cancel_fails_once,book_lost_response,slot_taken]

The DSC uses the same detector as RECHECK (proposal section 6), so a
RECHECK-vs-DSC difference is not a detector difference. The rule gate always
uses the frozen keyword list.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.controllers import book_only, dsc, rule_gate  # noqa: E402
from recheck.detectors import KeywordDetector  # noqa: E402
from recheck.policy import load_policy  # noqa: E402
from recheck.records import load_patients  # noqa: E402
from recheck.runner import run_episode  # noqa: E402
from recheck.scenarios import Episode, expand_episodes, load_scenarios  # noqa: E402
from scripts.run_llm import make_detector  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", default="tfidf")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--patients", default=str(ROOT / "data/eval/patients_v1.json"))
    ap.add_argument("--policy", default=str(ROOT / "data/policy/clinic_policy_v1.json"))
    ap.add_argument("--phrasings", default="direct,indirect")
    ap.add_argument("--faults", default="none")
    ap.add_argument("--controllers", default="book_only,rule_gate,dsc")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    S = load_scenarios(args.scenarios)
    P = load_patients(args.patients)
    pol = load_policy(args.policy)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    kw = KeywordDetector.from_file(ROOT / "data/detector/keywords.json")
    eps = expand_episodes(S, phrasings=tuple(args.phrasings.split(",")), faults=tuple(args.faults.split(",")))
    for seed in map(int, args.seeds.split(",")):
        det = make_detector(args.detector.replace("{seed}", str(seed)))
        ctrls = {"book_only": book_only(), "rule_gate": rule_gate(kw), "dsc": dsc(det)}
        for name in args.controllers.split(","):
            c = ctrls[name]
            path = out / f"{name}_s{seed}.jsonl"
            with open(path, "w") as fh:
                for e in eps:
                    e = Episode(e.scenario_id, e.timing, e.phrasing, e.fault, seed)
                    sc = S[e.scenario_id]
                    r = run_episode(e, sc, P[sc.patient_id], pol, c)
                    d = json.loads(r.to_json())
                    d["usage"] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "note_parse_failures": 0}
                    fh.write(json.dumps(d) + "\n")
            print(f"{path}: {len(eps)} episodes", flush=True)


if __name__ == "__main__":
    main()
