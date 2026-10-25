"""Run LLM conditions against one or more OpenAI-compatible servers.

    python scripts/run_llm.py --conditions plain,recheck --model qwen2.5:7b-instruct-q8_0 \
        --base-urls http://localhost:11434/v1,http://localhost:11435/v1 --workers 8 \
        --seeds 0,1,2 --out runs/llm_dev

Episodes are spread over the servers round-robin, `--workers` at a time.
Output per condition: <out>/<condition>_s<seed>.jsonl, plus <out>/summary.md
and summary.json over all conditions. Re-running skips episodes already in
the JSONL (resume after a crash or a SLURM time limit).
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.agents import CONDITIONS, ChatClient, LLMAgent  # noqa: E402
from recheck.analysis import fmt_ci, summarize  # noqa: E402
from recheck.detectors import OracleDetector, TfidfDetector, augment_with_carriers, load_seeds  # noqa: E402
from recheck.policy import load_policy  # noqa: E402
from recheck.records import load_patients  # noqa: E402
from recheck.runner import run_episode  # noqa: E402
from recheck.scenarios import expand_episodes, load_scenarios  # noqa: E402


DETECTOR_SEEDS = ROOT / "data" / "detector" / "seeds_v1_decon.json"
_TFIDF: dict = {}


def make_detector(kind: str, seeds_path: Path = DETECTOR_SEEDS):
    if kind == "oracle":
        return OracleDetector()
    if kind == "tfidf":
        key = str(seeds_path)
        if key not in _TFIDF:  # train once, share across episodes (predict is read-only)
            seeds = augment_with_carriers(load_seeds(seeds_path))
            _TFIDF[key] = TfidfDetector().fit([s["text"] for s in seeds], [s["label"] for s in seeds])
        return _TFIDF[key]
    if kind.startswith("lora:"):
        from recheck.detectors.lora import LoraDetector  # noqa: WPS433 (needs torch)
        return LoraDetector(kind.split(":", 1)[1])
    raise ValueError(kind)


def load_done(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # partial last line after a crash
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", default="plain,safety,plain_label,recheck,hybrid")
    ap.add_argument("--model", default="qwen2.5:7b-instruct-q8_0")
    ap.add_argument("--base-urls", default="http://localhost:11434/v1")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--detector", default="tfidf", help="tfidf | oracle | lora:<adapter_dir>")
    ap.add_argument("--detector-seeds", default=str(DETECTOR_SEEDS), help="training seeds for the tfidf detector")
    ap.add_argument("--data", default=str(ROOT / "data" / "dev"), help="dir with patients/scenarios/policy.json (dev)")
    ap.add_argument("--scenarios", help="override: scenarios JSON (e.g. data/eval/scenarios_v1.json)")
    ap.add_argument("--patients", help="override: patients JSON")
    ap.add_argument("--policy", help="override: policy JSON")
    ap.add_argument("--phrasings", default="direct,indirect")
    ap.add_argument("--faults", default="none")
    ap.add_argument("--limit", type=int, default=0, help="only the first N episodes (smoke test)")
    ap.add_argument("--out", default=str(ROOT / "runs" / "llm"))
    args = ap.parse_args()

    data = Path(args.data)
    patients = load_patients(args.patients or data / "patients.json")
    scenarios = load_scenarios(args.scenarios or data / "scenarios.json")
    policy = load_policy(args.policy or data / "policy.json")
    urls = args.base_urls.split(",")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    det_proto = args.detector
    det_seeds = Path(args.detector_seeds)
    lock = threading.Lock()

    eps_all = expand_episodes(scenarios, phrasings=tuple(args.phrasings.split(",")),
                              faults=tuple(args.faults.split(",")))
    if args.limit:
        eps_all = eps_all[:args.limit]

    all_results: dict[str, list[dict]] = {}
    for cond in args.conditions.split(","):
        assert cond in CONDITIONS, f"unknown condition {cond}; choose from {list(CONDITIONS)}"
        for seed in map(int, args.seeds.split(",")):
            path = out / f"{cond}_s{seed}.jsonl"
            done = load_done(path)
            done_ids = {json.dumps(d["episode"], sort_keys=True) for d in done}
            todo = [e for e in eps_all
                    if json.dumps({**e.__dict__, "seed": seed}, sort_keys=True) not in done_ids]
            print(f"[{cond} s{seed}] {len(done)} done, {len(todo)} to run", flush=True)
            t0 = time.time()

            def work(i_ep):
                i, ep = i_ep
                ep = type(ep)(ep.scenario_id, ep.timing, ep.phrasing, ep.fault, seed)
                client = ChatClient(urls[i % len(urls)], args.model, temperature=args.temperature, seed=seed)
                det = make_detector(det_proto, det_seeds) if CONDITIONS[cond].detector_label or CONDITIONS[cond].detector_tool else None
                agent = LLMAgent(cond, client, detector=det)
                sc = scenarios[ep.scenario_id]
                r = run_episode(ep, sc, patients[sc.patient_id], policy, agent,
                                allow_full_record=CONDITIONS[cond].full_record)
                d = json.loads(r.to_json())
                d["usage"] = {"calls": client.n_calls, "tokens_in": client.tokens_in, "tokens_out": client.tokens_out,
                              "note_parse_failures": agent.parse_failures}
                with lock:
                    with open(path, "a") as fh:
                        fh.write(json.dumps(d) + "\n")
                return d

            with ThreadPoolExecutor(args.workers) as pool:
                futs = [pool.submit(work, x) for x in enumerate(todo)]
                for k, f in enumerate(as_completed(futs), 1):
                    try:
                        f.result()
                    except Exception as e:  # keep going; failed episodes are re-run on resume
                        print(f"  episode failed: {e!r}", flush=True)
                    if k % 20 == 0:
                        print(f"  {k}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)
            all_results.setdefault(cond, []).extend(load_done(path))

    lines = ["| Condition | Policy unsafe [CI] | Strict unsafe [CI] | Lenient | T1 / MID / POST (policy) | Completion | Over-esc | Contrast | Stages | Calls/ep | NOTE fail |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    summary = {}
    for cond, res in all_results.items():
        s = summarize(res)
        n_calls = sum(r["usage"]["calls"] for r in res) / max(len(res), 1)
        nf = sum(r["usage"]["note_parse_failures"] for r in res)
        s["calls_per_episode"] = n_calls
        summary[cond] = s
        cc = s["contrast_consistency"]
        lines.append(f"| {cond} | {fmt_ci(s['unsafe_policy'])} | {fmt_ci(s['unsafe_strict'])} | {100*s['unsafe_lenient'][0]:.1f} | "
                     f"{100*s['unsafe_policy_T1']:.0f} / {100*s['unsafe_policy_MID']:.0f} / {100*s['unsafe_policy_POST']:.0f} | "
                     f"{100*s['completed'][0]:.1f} | {100*s['over_escalated'][0]:.1f} | {'-' if cc is None else f'{100*cc:.0f}'} | "
                     f"{s['stages']} | {n_calls:.1f} | {nf} |")
    (out / "summary.md").write_text(f"# LLM runs: {args.model}, detector={args.detector}\n\n" + "\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
