"""Remove detector TRAINING texts that overlap the evaluation text.

    python scripts/decontaminate.py --train data/detector/seeds_v1.json \
        --out data/detector/seeds_v1_decon.json [--n 6]

A training text is dropped if it shares >= n consecutive words with ANY
evaluation string (symptom phrasings, both versions, openings, advice
requests). Only training data is changed; the evaluation set is never edited
after the fact. The report (<out>.report.json) lists every dropped text and
the eval string it matched, so the step can be reported in the paper
(proposal section 5: "we report the maximum n-gram overlap").
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def words(t: str) -> list[str]:
    return re.findall(r"[a-z']+", t.lower())


def grams(t: str, n: int) -> set[tuple]:
    w = words(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--eval", default=str(ROOT / "data/eval/phrasings_v1.json"))
    ap.add_argument("--n", type=int, default=6)
    args = ap.parse_args()
    ev = json.loads(Path(args.eval).read_text())
    eval_texts = [o["text"] for o in ev["openings"]]
    for it in ev["items"]:
        eval_texts += [it["direct"], it["indirect"], it.get("advice_request") or ""]
    index: dict[tuple, str] = {}
    for t in eval_texts:
        for g in grams(t, args.n):
            index.setdefault(g, t)
    train = json.loads(Path(args.train).read_text())
    kept, dropped = [], []
    for r in train:
        hit = next((index[g] for g in grams(r["text"], args.n) if g in index), None)
        if hit:
            dropped.append({"seed_id": r["seed_id"], "label": r["label"], "text": r["text"], "matched_eval": hit})
        else:
            kept.append(r)
    Path(args.out).write_text(json.dumps(kept, indent=1))
    rep = {"n": args.n, "train_in": len(train), "kept": len(kept), "dropped": len(dropped),
           "dropped_by_label": {l: sum(d["label"] == l for d in dropped) for l in sorted({d["label"] for d in dropped})},
           "dropped_items": dropped}
    Path(args.out).with_suffix(".report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k != "dropped_items"}, indent=1))


if __name__ == "__main__":
    main()
