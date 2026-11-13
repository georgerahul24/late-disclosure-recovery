"""Score the filled hand-labelling sheets made by scripts/export_labelling.py.

    python scripts/score_labels.py --dir labelling --out results/labels_v1.md

Reports only what is filled in (blank rows are skipped and counted):
  - action policy: Cohen's kappa between labellers A and B on "red flag" and on
    each end state being acceptable; agreement of each labeller with the
    benchmark's current labels
  - stage check: agreement and kappa of the human first-failed stage with the
    automatic stage
  - advice judge: PPV / NPV in the sample (balanced on the judge verdict) and
    sensitivity / specificity reweighted by how often the judge flags a turn
    (advice_labels.csv, advice_labels_meta.json)
  - eval text and seeds review: how many items were marked not realistic or wrong
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.records import load_patients  # noqa: E402
from recheck.scenarios import load_scenarios  # noqa: E402

STATES = ["CANCEL_ESCALATE", "CONVERT_URGENT", "KEEP_ESCALATE", "HANDOVER", "ROUTINE_BOOKED", "NO_ACTION"]


def kappa(a: list, b: list) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return None if pe == 1 else (po - pe) / (1 - pe)


def col(row: dict, prefix: str) -> str:
    k = next((k for k in row if k.startswith(prefix)), None)
    return (row.get(k) or "").strip() if k else ""


def yn(x: str) -> bool | None:
    x = x.strip().lower()
    return True if x in ("yes", "y", "true", "1") else False if x in ("no", "n", "false", "0") else None


def states(x: str) -> set[str]:
    return {s for s in STATES if s in x.upper().replace(" ", "_")}


def read(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open())) if path.exists() else []


def f(x):
    return "--" if x is None else f"{x:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="labelling")
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--patients", default=str(ROOT / "data/eval/patients_v1.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = Path(args.dir)
    SC = load_scenarios(args.scenarios)
    P = load_patients(args.patients)
    P = P if isinstance(P, dict) else {p.patient_id: p for p in P}
    L = ["# Hand-label results", "", f"Made by `scripts/score_labels.py` from `{d}/`.", ""]

    # policy
    A = {r["scenario_id"]: r for r in read(d / "policy_review_A.csv")}
    B = {r["scenario_id"]: r for r in read(d / "policy_review_B.csv")}
    both = [s for s in A if s in B and yn(col(A[s], "YOUR_red_flag")) is not None and yn(col(B[s], "YOUR_red_flag")) is not None]
    L += ["## 1. Action policy (two labellers, blind to the benchmark labels)", "",
          f"Scenarios labelled by both: {len(both)} of {len(SC)}", ""]
    if both:
        ra = [yn(col(A[s], "YOUR_red_flag")) for s in both]
        rb = [yn(col(B[s], "YOUR_red_flag")) for s in both]
        L.append(f"- Red flag, A vs B: agreement {sum(x == y for x, y in zip(ra, rb)) / len(both):.2f}, Cohen's kappa {f(kappa(ra, rb))}")
        for name, lab in (("A", A), ("B", B)):
            mine = [yn(col(lab[s], "YOUR_red_flag")) for s in both]
            cur = [SC[s].is_red_flag(P[SC[s].patient_id]) for s in both]
            L.append(f"- Red flag, {name} vs benchmark: agreement {sum(x == y for x, y in zip(mine, cur)) / len(both):.2f}, "
                     f"kappa {f(kappa(mine, cur))}")
        L += ["", "| End state acceptable | kappa A vs B | A vs benchmark | B vs benchmark |", "|---|---|---|---|"]
        for st in STATES:
            sa = [st in states(col(A[s], "YOUR_acceptable")) for s in both]
            sb = [st in states(col(B[s], "YOUR_acceptable")) for s in both]
            cur = [st in SC[s].acceptable(P[SC[s].patient_id]) for s in both]
            L.append(f"| {st} | {f(kappa(sa, sb))} | {f(kappa(sa, cur))} | {f(kappa(sb, cur))} |")
        dis = [s for s in both if yn(col(A[s], "YOUR_red_flag")) != SC[s].is_red_flag(P[SC[s].patient_id])
               or yn(col(B[s], "YOUR_red_flag")) != SC[s].is_red_flag(P[SC[s].patient_id])]
        L += ["", f"Scenarios where a labeller disagrees with the benchmark on red flag: {', '.join(dis) or 'none'}"]

    # stage check
    rows = [r for r in read(d / "stage_check.csv") if col(r, "YOUR_first_failed_stage")[:1].isdigit()]
    L += ["", "## 2. Stage check (human vs automatic first-failed stage)", "", f"Episodes labelled: {len(rows)}"]
    if rows:
        h = [col(r, "YOUR_first_failed_stage")[:1] for r in rows]
        a = [col(r, "auto_stage") for r in rows]
        L.append(f"- Agreement {sum(x == y for x, y in zip(h, a)) / len(rows):.2f}, Cohen's kappa {f(kappa(h, a))}")
        L.append(f"- Confusions (human, auto): {dict(Counter((x, y) for x, y in zip(h, a) if x != y))}")

    # advice judge
    rows = [r for r in read(d / "advice_labels.csv") if yn(col(r, "YOUR_advice")) is not None]
    L += ["", "## 3. Advice judge vs human", "", f"Replies labelled: {len(rows)}"]
    if rows:
        tp = sum(1 for r in rows if yn(col(r, "YOUR_advice")) and yn(col(r, "judge_advice")))
        fn = sum(1 for r in rows if yn(col(r, "YOUR_advice")) and not yn(col(r, "judge_advice")))
        fp = sum(1 for r in rows if not yn(col(r, "YOUR_advice")) and yn(col(r, "judge_advice")))
        tn = len(rows) - tp - fn - fp
        L.append(f"- Human advice = yes: {tp + fn}; no: {fp + tn}")
        ppv = tp / (tp + fp) if tp + fp else None
        npv = tn / (tn + fn) if tn + fn else None
        L.append(f"- In the sample: PPV {f(ppv)}, NPV {f(npv)}, kappa "
                 f"{f(kappa([yn(col(r, 'YOUR_advice')) for r in rows], [yn(col(r, 'judge_advice')) for r in rows]))}")
        meta = d / "advice_labels_meta.json"
        q = json.loads(meta.read_text()).get("judge_flagged_turn_share_llm_main") if meta.exists() else None
        if q is not None and ppv is not None and npv is not None:
            # The sample is balanced on the judge verdict, so sensitivity and
            # specificity must be reweighted by how often the judge flags a turn (q).
            prev = ppv * q + (1 - npv) * (1 - q)
            sens = ppv * q / prev if prev else None
            spec = npv * (1 - q) / (1 - prev) if prev < 1 else None
            L.append(f"- Reweighted to all judged turns (judge flags {100 * q:.2f}%): sensitivity {f(sens)}, "
                     f"specificity {f(spec)}, estimated human advice rate {100 * prev:.2f}%")

    # text and seeds
    for fn_, label, keys in (("eval_text_review.csv", "Eval text", ("YOUR_realistic", "YOUR_wording")),
                             ("seeds_review.csv", "Detector seeds", ("YOUR_label_correct",))):
        rows = read(d / fn_)
        done = [r for r in rows if any(yn(col(r, k)) is not None for k in keys)]
        bad = [r for r in done if any(yn(col(r, k)) is False for k in keys)]
        L += ["", f"## {label} review", "", f"Reviewed {len(done)} of {len(rows)}; marked not OK: {len(bad)}"]
        if bad:
            L.append("IDs: " + ", ".join(r.get("scenario_id") or r.get("seed_id") for r in bad))
    Path(args.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
