"""Export the hand-labelling sheets (CSV, open in Excel or Google Sheets).

    python scripts/export_labelling.py --out labelling

Writes:
  policy_review_A.csv, policy_review_B.csv  action policy, one row per scenario, for
                                            two labellers working alone (Cohen's kappa)
  eval_text_review.csv                      eval phrasings: realistic? label right?
  seeds_review.csv                          detector training seeds
  stage_check.csv                           50 failed red-flag LLM episodes: check the
                                            automatic first-failed stage
Blank columns start with "YOUR_". Score the filled sheets with scripts/score_labels.py.
The advice-judge sheet comes from scripts/judge_runs.py (advice_label_sample.jsonl).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from recheck.records import load_patients  # noqa: E402
from recheck.scenarios import load_scenarios  # noqa: E402
from summarize_runs import load  # noqa: E402

END_STATES = "CANCEL_ESCALATE | CONVERT_URGENT | KEEP_ESCALATE | HANDOVER | ROUTINE_BOOKED | NO_ACTION"
STAGES = "1 detect | 2 context (record not used) | 3 earlier booking not revised | 4 repair failed | 5 not escalated"


def write(path: Path, rows: list[dict]):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--patients", default=str(ROOT / "data/eval/patients_v1.json"))
    ap.add_argument("--seeds", default=str(ROOT / "data/detector/seeds_v1_decon.json"))
    ap.add_argument("--runs", nargs="+", default=["runs/llm_main"])
    ap.add_argument("--n-stage", type=int, default=50)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    SC = load_scenarios(args.scenarios)
    P = load_patients(args.patients)
    P = P if isinstance(P, dict) else {p.patient_id: p for p in P}

    # 1. action policy (blind: the current labels are NOT shown)
    rows = []
    for sid, s in sorted(SC.items()):
        p = P[s.patient_id]
        rows.append({
            "scenario_id": sid, "subject": s.subject, "severe": s.severe,
            "patient": f"{p.sex}, age {p.age()}",
            "current_medicines": "; ".join(m.name for m in p.active_meds()) or "none",
            "current_conditions": "; ".join(c.name for c in p.active_conditions()) or "none",
            "symptom (direct wording)": s.symptom_direct or "",
            "YOUR_red_flag (yes/no)": "",
            f"YOUR_acceptable_end_states (any of: {END_STATES})": "",
            "YOUR_comment": ""})
    write(out / "policy_review_A.csv", rows)
    write(out / "policy_review_B.csv", rows)

    # 2. eval text
    rows = [{"scenario_id": sid, "family": s.family, "kind": s.kind, "subject": s.subject,
             "opening": s.opening, "symptom_direct": s.symptom_direct or "", "symptom_indirect": s.symptom_indirect or "",
             "YOUR_realistic (yes/no)": "", "YOUR_wording_matches_intended_meaning (yes/no)": "", "YOUR_suggested_edit": ""}
            for sid, s in sorted(SC.items())]
    write(out / "eval_text_review.csv", rows)

    # 3. detector seeds
    seeds = json.loads(Path(args.seeds).read_text())
    rows = [{"seed_id": x["seed_id"], "label": x["label"], "text": x["text"], "near_miss_of": x.get("near_miss_of") or "",
             "YOUR_label_correct (yes/no)": "", "YOUR_suggested_label_or_edit": ""} for x in seeds]
    write(out / "seeds_review.csv", rows)

    # 4. stage check: failed red-flag core episodes, spread over conditions and stages
    data = load(args.runs)
    by = defaultdict(list)
    for c, rs in data.items():
        for r in rs:
            g, e = r["grade"], r["episode"]
            s = SC[e["scenario_id"]]
            if (g["red_flag"] and g["unsafe_policy"] and e["fault"] == "none" and s.subject == "self"
                    and s.disclosure == "volunteer" and not s.advice_request):
                by[(c, g["stage"])].append(r)
    rng = random.Random(0)
    keys = sorted(by)
    picked = []
    while len(picked) < args.n_stage and any(by[k] for k in keys):
        for k in keys:  # round robin over (condition, stage) cells
            if by[k] and len(picked) < args.n_stage:
                picked.append(by[k].pop(rng.randrange(len(by[k]))))
    rows = []
    for i, r in enumerate(picked, 1):
        e, s = r["episode"], SC[r["episode"]["scenario_id"]]
        convo = "\n".join(f"[{t['turn']}] {t['role'].upper()}: {t['text']}" for t in r["transcript"])
        calls = "\n".join(f"[{c['turn']}] {c['name']}({json.dumps(c['args'])}) -> {'ok' if c['ok'] else 'FAILED'}"
                          for c in r["calls"])
        notes = "\n".join(f"[{n.get('turn')}] {json.dumps({k: v for k, v in n.items() if k != 'turn'})}" for n in r["notes"])
        p = P[s.patient_id]
        rows.append({"item": i, "condition": r["agent"], "scenario_id": e["scenario_id"], "timing": e["timing"],
                     "phrasing": e["phrasing"], "seed": e["seed"],
                     "why_red_flag": s.rule(p).reason if s.kind == "record_dependent" else f"universal red flag ({s.family})",
                     "end_state": r["grade"]["end_state"], "acceptable_end_states": "; ".join(r["grade"]["acceptable"]),
                     "conversation": convo, "tool_calls": calls, "agent_notes": notes,
                     f"YOUR_first_failed_stage ({STAGES})": "", "YOUR_comment": "",
                     "auto_stage (hidden from you until done; keep this column hidden)": r["grade"]["stage"]})
    write(out / "stage_check.csv", rows)


if __name__ == "__main__":
    main()
