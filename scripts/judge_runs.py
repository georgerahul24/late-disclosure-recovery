"""Apply the advice judge to finished LLM runs.

    cluster/run_in_hold.sh <job> scripts/judge_runs.py --runs runs/llm_eval \
        (run_in_hold passes --model/--base-urls; use --judge-model to pick the judge)

For each <cond>_s<seed>.jsonl in --runs writes <cond>_s<seed>.judge.jsonl with
one line per episode: {"episode": ..., "turns": [{"turn", "advice", "quote", "parse_ok"}]}.
Resumable. Also writes advice_summary.md: share of episodes with >=1 advice
turn, per condition, plus judge parse failures. Numbers are UNVALIDATED until
the judge is checked against human labels (todo.md).

Also exports a stratified sample for human labelling (--label-sample N) to
<runs>/advice_label_sample.jsonl, with the judge verdict hidden.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.agents.client import ChatClient  # noqa: E402
from recheck.judge import AdviceJudge  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    """Lines of a judge file; skips a half-written last line left by a killed job."""
    out = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--judge-model", default="llama3.1:8b-instruct-q8_0")
    ap.add_argument("--model", help="(ignored; passed by run_in_hold.sh)")
    ap.add_argument("--base-urls", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--label-sample", type=int, default=60)
    args = ap.parse_args()
    urls = args.base_urls.split(",")
    runs = Path(args.runs)
    lock = threading.Lock()
    summary = []
    all_turns = []
    for f in sorted(runs.glob("*_s*.jsonl")):
        if f.name.endswith(".judge.jsonl"):
            continue
        out = f.with_suffix(".judge.jsonl")
        done = {json.dumps(j["episode"], sort_keys=True) for j in read_jsonl(out)}
        eps = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        todo = [e for e in eps if json.dumps(e["episode"], sort_keys=True) not in done]
        print(f"{f.name}: {len(eps)} episodes, {len(todo)} to judge", flush=True)

        def work(i_e):
            i, e = i_e
            j = AdviceJudge(ChatClient(urls[i % len(urls)], args.judge_model, temperature=0.0, seed=0, max_tokens=120,
                                      json_mode=True))
            turns = j.judge_episode(e)
            with lock, open(out, "a") as fh:
                fh.write(json.dumps({"episode": e["episode"], "turns": turns}) + "\n")

        with ThreadPoolExecutor(args.workers) as pool:
            list(pool.map(work, enumerate(todo)))
        judged = {json.dumps(j["episode"], sort_keys=True): j["turns"] for j in read_jsonl(out)}
        n_adv = sum(1 for t in judged.values() if any(x["advice"] for x in t))
        n_fail = sum(1 for t in judged.values() for x in t if not x["parse_ok"])
        summary.append((f.stem, len(judged), n_adv, n_fail))
        by_ep = {json.dumps(e["episode"], sort_keys=True): e for e in eps}
        for k, turns in judged.items():
            e = by_ep.get(k)
            if not e:
                continue
            for x in turns:
                txt = next((t["text"] for t in e["transcript"] if t["role"] == "agent" and t["turn"] == x["turn"]), "")
                pat = next((t["text"] for t in e["transcript"] if t["role"] == "patient" and t["turn"] == x["turn"]), "")
                all_turns.append({"run": f.stem, "episode": e["episode"], "turn": x["turn"], "patient": pat,
                                  "agent": txt, "_judge": x["advice"]})
    lines = ["# Advice judge (UNVALIDATED until checked against human labels)", "",
             f"Judge model: `{args.judge_model}`", "",
             "| Run | Episodes | Episodes with advice | % | Judge parse failures (turns) |", "|---|---|---|---|---|"]
    for name, n, a, fl in summary:
        lines.append(f"| {name} | {n} | {a} | {100 * a / max(1, n):.1f} | {fl} |")
    (runs / "advice_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if args.label_sample and all_turns:
        rng = random.Random(0)
        pos = [t for t in all_turns if t["_judge"]]
        neg = [t for t in all_turns if t["_judge"] is False]
        k = args.label_sample // 2
        sample = rng.sample(pos, min(k, len(pos))) + rng.sample(neg, min(args.label_sample - min(k, len(pos)), len(neg)))
        rng.shuffle(sample)
        with open(runs / "advice_label_sample.jsonl", "w") as fh:
            for i, t in enumerate(sample):
                fh.write(json.dumps({"id": i, "patient": t["patient"], "agent": t["agent"], "human_advice": None,
                                     "_judge_hidden": t["_judge"], "run": t["run"], "episode": t["episode"],
                                     "turn": t["turn"]}) + "\n")
        print(f"wrote {len(sample)} turns for human labelling (balanced on judge verdict)")


if __name__ == "__main__":
    main()
