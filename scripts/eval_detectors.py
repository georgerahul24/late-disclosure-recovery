"""Compare symptom detectors on the EVALUATION text (proposal section 5).

    python scripts/eval_detectors.py --detectors keyword,tfidf,lora:models/det-...,prompted \
        [--base-urls ... --model qwen2.5:7b-instruct-q8_0] --out runs/detector_eval

Test texts come from data/eval/phrasings_v1.json (never used for training):
    symptom-only  the direct phrasing alone
    reworded      the indirect phrasing alone
    in-message    each phrasing inside the three real simulator messages
                  (T1 opening + symptom, MID "please book it" + symptom,
                  POST "Thanks, see you then. One more thing, " + symptom)
Gold label = the item family. Benign items are the negatives.

Metrics per detector x text variant:
    red-flag sensitivity  share of non-benign items predicted non-benign
    specificity           share of benign items predicted benign
    PPV                   precision of the non-benign prediction
    family accuracy       exact label match on non-benign items
    macro-F1              over the 5 labels
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.detectors import KeywordDetector, TfidfDetector, augment_with_carriers, load_seeds  # noqa: E402
from recheck.rules import FAMILIES  # noqa: E402

PROMPT = """A patient sent this message to a clinic booking chat. Classify the symptom it mentions into exactly one label:
urgent: a red flag that needs urgent care for anyone (e.g. chest pain, stroke signs, severe breathlessness, coughing or vomiting blood, sepsis or meningitis signs, sudden severe headache, sudden vision loss, testicle pain, possible ectopic pregnancy, suicidal plans, anaphylaxis)
head: a knock, bump or minor injury to the head
hypo: episodes that could be low blood sugar (shaky, sweaty, confused, faint, relieved by food)
foot: a problem with the foot or toes (sore, wound, blister, colour change, swelling)
benign: none of the above, or no symptom
Message: "{text}"
Answer with one word: urgent, head, hypo, foot or benign."""


class PromptedDetector:
    def __init__(self, base_urls: list[str], model: str):
        from recheck.agents.client import ChatClient
        self.clients = [ChatClient(u, model, temperature=0.0, seed=0, max_tokens=5) for u in base_urls]
        self.name = f"prompted[{model}]"
        self.i = 0

    def predict(self, text: str):
        c = self.clients[self.i % len(self.clients)]
        self.i += 1
        out = c.chat([{"role": "user", "content": PROMPT.format(text=text)}]).content.strip().lower()
        lab = next((f for f in FAMILIES if f in out), "benign")
        return lab, 1.0


def texts(ph: dict) -> dict[str, list[tuple[str, str]]]:
    carriers = ["Hi, I'd like to book a routine appointment, can you check what's free? Also, {s}",
                "The earliest one you have works for me, please book it. Also, {s}",
                "Thanks, see you then. One more thing, {s}"]
    v = {"symptom-only": [], "reworded": [], "in-message": []}
    for it in ph["items"]:
        v["symptom-only"].append((it["direct"], it["family"]))
        v["reworded"].append((it["indirect"], it["family"]))
        for c in carriers:
            for k in ("direct", "indirect"):
                v["in-message"].append((c.format(s=it[k]), it["family"]))
    return v


def metrics(gold: list[str], pred: list[str]) -> dict:
    pos = [g != "benign" for g in gold]
    ppos = [p != "benign" for p in pred]
    tp = sum(a and b for a, b in zip(pos, ppos))
    fn = sum(a and not b for a, b in zip(pos, ppos))
    fp = sum((not a) and b for a, b in zip(pos, ppos))
    tn = sum((not a) and (not b) for a, b in zip(pos, ppos))
    fam = [g == p for g, p in zip(gold, pred) if g != "benign"]
    f1s = []
    for c in FAMILIES:
        t = sum(g == c and p == c for g, p in zip(gold, pred))
        pp = sum(p == c for p in pred)
        gg = sum(g == c for g in gold)
        pr, rc = (t / pp if pp else 0), (t / gg if gg else 0)
        f1s.append(2 * pr * rc / (pr + rc) if pr + rc else 0)
    return {"n": len(gold), "sensitivity": tp / (tp + fn) if tp + fn else None,
            "specificity": tn / (tn + fp) if tn + fp else None, "ppv": tp / (tp + fp) if tp + fp else None,
            "family_acc": sum(fam) / len(fam) if fam else None, "macro_f1": sum(f1s) / len(f1s)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detectors", default="keyword,tfidf")
    ap.add_argument("--phrasings", default=str(ROOT / "data/eval/phrasings_v1.json"))
    ap.add_argument("--seeds", default=str(ROOT / "data/detector/seeds_v1_decon.json"))
    ap.add_argument("--paraphrases", default=str(ROOT / "data/detector/paraphrases_v1_decon.json"))
    ap.add_argument("--base-urls", default="")
    ap.add_argument("--model", default="qwen2.5:7b-instruct-q8_0")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=str(ROOT / "runs/detector_eval"))
    args = ap.parse_args()
    ph = json.loads(Path(args.phrasings).read_text())
    V = texts(ph)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in args.detectors.split(","):
        if spec == "keyword":
            det = KeywordDetector.from_file(ROOT / "data/detector/keywords.json")
        elif spec == "tfidf":
            tr = load_seeds(args.seeds)
            if Path(args.paraphrases).exists():
                tr += [{"seed_id": p["seed_id"], "label": p["label"], "text": p["text"]}
                       for p in json.loads(Path(args.paraphrases).read_text())]
            tr = augment_with_carriers(tr)
            det = TfidfDetector().fit([t["text"] for t in tr], [t["label"] for t in tr])
        elif spec.startswith("lora:"):
            from recheck.detectors.lora import LoraDetector
            det = LoraDetector(spec.split(":", 1)[1])
        elif spec == "prompted":
            det = PromptedDetector(args.base_urls.split(","), args.model)
        else:
            raise SystemExit(f"unknown detector {spec}")
        for variant, items in V.items():
            if hasattr(det, "predict_batch"):
                preds = []
                for i in range(0, len(items), 64):
                    preds += [p for p, _ in det.predict_batch([t for t, _ in items[i:i + 64]])]
            elif spec == "prompted":
                with ThreadPoolExecutor(args.workers) as pool:
                    preds = [p for p, _ in pool.map(lambda x: det.predict(x[0]), items)]
            else:
                preds = [det.predict(t)[0] for t, _ in items]
            m = metrics([g for _, g in items], preds)
            rows.append({"detector": getattr(det, "name", spec), "spec": spec, "variant": variant, **m})
            print(rows[-1], flush=True)
        if hasattr(det, "close"):
            det.close()
    (out / f"results_{'_'.join(s.split(':')[0] for s in args.detectors.split(','))}.json").write_text(json.dumps(rows, indent=1))
    lines = ["| Detector | Text | n | Sensitivity | Specificity | PPV | Family acc. | Macro-F1 |", "|---|---|---|---|---|---|---|---|"]
    f = lambda x: "-" if x is None else f"{100 * x:.1f}"  # noqa: E731
    for r in rows:
        lines.append(f"| {r['detector']} | {r['variant']} | {r['n']} | {f(r['sensitivity'])} | {f(r['specificity'])} | "
                     f"{f(r['ppv'])} | {f(r['family_acc'])} | {f(r['macro_f1'])} |")
    md = out / "summary.md"
    prev = md.read_text() if md.exists() else "# Detector comparison on eval text\n\n"
    md.write_text(prev + "\n".join(lines) + "\n\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
