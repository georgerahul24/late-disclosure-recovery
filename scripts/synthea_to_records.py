"""Convert Synthea CSV output into our PatientRecord JSON and build patient pools.

    python scripts/synthea_to_records.py --csv /ssd_scratch/gr/lma/synthea/latest-csv \
        --out data/synthea

Two streaming passes, so the multi-GB observations.csv never sits in memory:
  pass 1: patients, medications, conditions -> eligibility + pools
  pass 2: encounters, observations for selected patients only

Pools (rules in recheck/rules.py decide membership, so pools and grading agree):
  head_pos   active anticoagulant or non-aspirin antiplatelet
  head_neg   not head_pos, valid negative (under 65, no seizure disorder)
  hypo_pos   active insulin or sulfonylurea
  hypo_neg   not hypo_pos, valid negative (no past hypoglycaemia)
  foot_pos   active diabetes (not prediabetes / gestational)
  foot_neg   not foot_pos, valid negative (no peripheral vascular disease)
  general    any eligible adult (universal red flags and benign scenarios)

Eligible = alive at the reference date and aged 18 to 90.

History kept per patient: ALL medications (collapsed per drug into one
interval; stopped drugs stay as distractors), ALL conditions, the 80 most
recent encounters and the 120 most recent observations from the last 5 years.
This cap is a size decision, documented in data/synthea/README.md.

Outputs: <out>/patients.json, <out>/pools.json, <out>/conversion_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck import rules  # noqa: E402
from recheck.records import (REFERENCE_DATE, Condition, Encounter, Medication, Observation,  # noqa: E402
                             PatientRecord, save_patients)

csv.field_size_limit(10**8)
MAX_ENC = 80
MAX_OBS = 120
OBS_YEARS = 5
POOL_CAP = {"head_pos": 80, "head_neg": 200, "hypo_pos": 80, "hypo_neg": 200, "foot_pos": 80,
            "foot_neg": 200, "general": 250}


def d(s: str | None) -> str | None:
    return s[:10] if s else None


def clean_name(s: str) -> str:
    return re.sub(r"\d+", "", s).strip()


def read(path: Path):
    with open(path, newline="") as fh:
        yield from csv.DictReader(fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default=str(ROOT / "data" / "synthea"))
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()
    src, out = Path(args.csv), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ref = REFERENCE_DATE
    rng = random.Random(args.seed)

    # ---- pass 1 -----------------------------------------------------------
    people = {}
    n_total = n_dead = 0
    for r in read(src / "patients.csv"):
        n_total += 1
        if r.get("DEATHDATE"):
            n_dead += 1
            continue
        b = date.fromisoformat(r["BIRTHDATE"][:10])
        age = ref.year - b.year - ((ref.month, ref.day) < (b.month, b.day))
        if 18 <= age <= 90:
            people[r["Id"]] = r
    meds: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in read(src / "medications.csv"):
        if r["PATIENT"] in people:
            meds[r["PATIENT"]][r["DESCRIPTION"]].append((d(r["START"]), d(r.get("STOP"))))
    conds: dict[str, list] = defaultdict(list)
    for r in read(src / "conditions.csv"):
        if r["PATIENT"] in people:
            conds[r["PATIENT"]].append((r["DESCRIPTION"], d(r["START"]), d(r.get("STOP"))))

    def build(pid: str) -> PatientRecord:
        r = people[pid]
        short = "S" + pid.replace("-", "")[:8]
        p = PatientRecord(short, f"{clean_name(r['FIRST'])} {clean_name(r['LAST'])}", r["BIRTHDATE"][:10],
                          r["GENDER"])
        n = 0
        for desc, spans in sorted(meds[pid].items()):
            n += 1
            start = min(s for s, _ in spans)
            active = any(e is None or e > ref.isoformat() for _, e in spans)
            stop = None if active else max(e for _, e in spans)
            p.medications.append(Medication(f"{short}-M{n:03d}", desc, start, stop))
        seen = set()
        for desc, start, stop in sorted(conds[pid], key=lambda x: x[1] or ""):
            if (desc, start) in seen:
                continue
            seen.add((desc, start))
            n += 1
            p.conditions.append(Condition(f"{short}-C{n:03d}", desc, start, stop))
        return p

    recs = {pid: build(pid) for pid in people}
    pools = defaultdict(list)
    for pid, p in recs.items():
        pools["general"].append(pid)
        for fam in ("head", "hypo", "foot"):
            res = rules.evaluate(fam, p)
            if res.urgent:
                pools[f"{fam}_pos"].append(pid)
            elif res.valid_negative:
                pools[f"{fam}_neg"].append(pid)

    # Prefer negatives that carry distractors (aspirin only, stopped risk drugs,
    # metformin-only diabetes): these make the matched pairs hard.
    def distractor_score(pid: str, fam: str) -> int:
        p = recs[pid]
        s = 0
        for m in p.medications:
            c = m.med_class
            if fam == "head" and c in ("antiplatelet", "anticoagulant"):
                s += 2 if not m.active else 1  # stopped clopidogrel/warfarin, or active aspirin
            if fam == "hypo" and (c in ("insulin", "sulfonylurea") and not m.active or c == "other_diabetes" and m.active):
                s += 2
        if fam == "foot" and any("prediabetes" in c.name.lower() for c in p.conditions):
            s += 2
        return s

    selected: dict[str, list[str]] = {}
    for pool, ids in pools.items():
        ids = sorted(ids)
        rng.shuffle(ids)
        if pool.endswith("_neg"):
            fam = pool.split("_")[0]
            ids.sort(key=lambda i: -distractor_score(i, fam))  # stable: shuffled within score
        selected[pool] = ids[:POOL_CAP[pool]]
    keep = set().union(*selected.values())

    # ---- pass 2 -----------------------------------------------------------
    encs: dict[str, list] = defaultdict(list)
    for r in read(src / "encounters.csv"):
        if r["PATIENT"] in keep:
            encs[r["PATIENT"]].append((d(r["START"]), r.get("ENCOUNTERCLASS", ""), r.get("DESCRIPTION", ""),
                                       r.get("REASONDESCRIPTION", "")))
    cutoff = date(ref.year - OBS_YEARS, ref.month, ref.day).isoformat()
    obs: dict[str, list] = defaultdict(list)
    for r in read(src / "observations.csv"):
        if r["PATIENT"] in keep and (r["DATE"][:10] >= cutoff):
            unit = r.get("UNITS") or ""
            obs[r["PATIENT"]].append((d(r["DATE"]), r["DESCRIPTION"], f"{r.get('VALUE', '')} {unit}".strip()))

    final = []
    id_map = {}
    for pid in sorted(keep):
        p = recs[pid]
        n = len(p.medications) + len(p.conditions)
        for e in sorted(encs[pid], reverse=True)[:MAX_ENC]:
            n += 1
            reason = e[3] or e[2]
            p.encounters.append(Encounter(f"{p.patient_id}-E{n:03d}", e[0], e[1], reason))
        for o in sorted(obs[pid], reverse=True)[:MAX_OBS]:
            n += 1
            p.observations.append(Observation(f"{p.patient_id}-O{n:03d}", o[0], o[1], o[2]))
        final.append(p)
        id_map[pid] = p.patient_id

    save_patients(final, out / "patients.json")
    pools_out = {k: [id_map[i] for i in v] for k, v in selected.items()}
    (out / "pools.json").write_text(json.dumps(pools_out, indent=1))
    lines = [
        "# Synthea conversion report", "",
        f"- Synthea patients in CSV: {n_total} ({n_dead} dead)",
        f"- Eligible (alive, 18 to 90 on {ref}): {len(people)}",
        f"- Selected for the benchmark: {len(final)}", "",
        "| Pool | Eligible | Selected |", "|---|---|---|",
    ]
    for k in sorted(pools):
        lines.append(f"| {k} | {len(pools[k])} | {len(selected[k])} |")
    meds_seen = defaultdict(int)
    for pid in people:
        for desc in meds[pid]:
            c = recs[pid].medications and next((m.med_class for m in recs[pid].medications if m.name == desc), None)
            if c:
                meds_seen[(c, desc)] += 1
    lines += ["", "## Risk-relevant drug descriptions found (class, description, n patients)", "",
              "| Class | Description | Patients |", "|---|---|---|"]
    for (c, desc), k in sorted(meds_seen.items(), key=lambda x: (x[0][0], -x[1])):
        lines.append(f"| {c} | {desc} | {k} |")
    (out / "conversion_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:16]))


if __name__ == "__main__":
    main()
