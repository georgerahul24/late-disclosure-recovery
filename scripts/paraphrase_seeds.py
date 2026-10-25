"""Make LLM paraphrases of the detector seeds (training data only).

Proposal section 5: each seed gets four LLM paraphrases. LLM paraphrasing is
allowed for TRAINING data only, never for evaluation phrases.

    cluster/run_in_hold.sh <job> scripts/paraphrase_seeds.py \
        --seeds data/detector/seeds_v1.json --out data/detector/paraphrases_v1.json

Automatic checks (the proposal also wants a second team member to check them;
that human pass is still to do, see todo.md):
  1. not empty, 4 to 45 words, not a copy of the seed (token Jaccard < 0.9)
  2. no booking talk (the carriers add that later)
  3. a separate label-check call: the model is shown the paraphrase alone
     and must pick the same family as the seed. Mismatches are dropped and
     counted in the report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.agents.client import ChatClient  # noqa: E402

FAM_DESC = {
    "urgent": "a red-flag symptom that needs urgent care for anyone (e.g. chest pain, stroke signs, severe breathlessness)",
    "head": "a knock, bump or minor injury to the head",
    "hypo": "symptoms that could be low blood sugar (shaky, sweaty, confused, faint, hungry)",
    "foot": "a problem with the foot or toes (sore, wound, blister, colour change, swelling)",
    "benign": "a minor, non-urgent issue or a question that is none of the above",
}
PARA_PROMPT = """Rewrite the patient message below in 4 different ways, as 4 different real patients might type it in a clinic chat.
Keep exactly the same medical content and severity. Do not add or remove symptoms. Vary wording, length and tone (casual, worried, terse, chatty). Some typos are fine. Do not mention appointments or booking.
Message: "{text}"
Reply with a JSON list of 4 strings and nothing else."""
CHECK_PROMPT = """Classify this patient message into exactly one category.
urgent: {urgent}
head: {head}
hypo: {hypo}
foot: {foot}
benign: {benign}
Message: "{text}"
Reply with one word: urgent, head, hypo, foot or benign."""


def jacc(a: str, b: str) -> float:
    A, B = set(re.findall(r"[a-z]+", a.lower())), set(re.findall(r"[a-z]+", b.lower()))
    return len(A & B) / max(1, len(A | B))


def parse_list(text: str) -> list[str]:
    """Accept one JSON list of strings, or several lists (Qwen often writes
    one single-item list per line)."""
    try:
        out = json.loads(text.strip())
        if isinstance(out, list):
            return [x.strip() for x in out if isinstance(x, str) and x.strip()]
    except json.JSONDecodeError:
        pass
    items = []
    for m in re.finditer(r"\[[^\[\]]*\]", text, re.S):
        try:
            items += [x.strip() for x in json.loads(m.group(0)) if isinstance(x, str) and x.strip()]
        except json.JSONDecodeError:
            continue
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default=str(ROOT / "data/detector/seeds_v1.json"))
    ap.add_argument("--out", default=str(ROOT / "data/detector/paraphrases_v1.json"))
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-urls", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--n", type=int, default=4)
    args = ap.parse_args()
    seeds = json.loads(Path(args.seeds).read_text())
    urls = args.base_urls.split(",")

    def work(i_s):
        i, s = i_s
        para = ChatClient(urls[i % len(urls)], args.model, temperature=0.8, seed=i, max_tokens=400)
        check = ChatClient(urls[i % len(urls)], args.model, temperature=0.0, seed=0, max_tokens=5)
        cands = parse_list(para.chat([{"role": "user", "content": PARA_PROMPT.format(text=s["text"])}]).content)
        kept, dropped = [], []
        for c in cands:
            n = len(c.split())
            if not (4 <= n <= 45) or jacc(c, s["text"]) >= 0.9 or re.search(r"\b(book|appointment)", c, re.I):
                dropped.append({"text": c, "why": "filter"})
                continue
            lab = check.chat([{"role": "user", "content": CHECK_PROMPT.format(text=c, **FAM_DESC)}]).content.strip().lower()
            lab = re.sub(r"[^a-z]", "", lab)
            if lab != s["label"]:
                dropped.append({"text": c, "why": f"label_check={lab}"})
                continue
            kept.append(c)
        return s, kept[:args.n], dropped

    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(work, enumerate(seeds)))
    out, report = [], {"seeds": len(seeds), "kept": 0, "dropped_filter": 0, "dropped_label": 0, "by_label": {}}
    for s, kept, dropped in results:
        for j, t in enumerate(kept):
            out.append({"seed_id": s["seed_id"], "label": s["label"], "text": t, "paraphrase_of": s["seed_id"], "k": j})
        report["kept"] += len(kept)
        report["dropped_filter"] += sum(d["why"] == "filter" for d in dropped)
        report["dropped_label"] += sum(d["why"].startswith("label") for d in dropped)
        report["by_label"][s["label"]] = report["by_label"].get(s["label"], 0) + len(kept)
    Path(args.out).write_text(json.dumps(out, indent=1))
    Path(args.out).with_suffix(".report.json").write_text(json.dumps({**report, "model": args.model}, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
