"""Full analysis of finished runs (proposal sections 3, 7, 9).

    python scripts/summarize_runs.py --runs runs/llm_main runs/llm_ablate runs/scripted_main \
        --scenarios data/eval/scenarios_v1.json --out results/main_v1.md

Reads every <cond>_s<seed>.jsonl (LLM runs) and every <controller>.jsonl
(scripted runs, treated as seed 0) under --runs. The condition name is the
file stem without the _s<seed> suffix.

Unit of analysis = scenario. For each condition and scenario we average over
timings, phrasings and seeds, then compare conditions with a paired
scenario-level bootstrap (10,000 resamples).

Sections:
  1. Core table (volunteered disclosure, no advice request, no fault, subject=self)
  2. Hypotheses: H1 (POST - T1, plain & safety), H2/H2b/H2c, Hybrid vs DSC,
     Holm-corrected over the 5 confirmatory comparisons; TOST RECHECK vs DSC (+-10)
  3. pass^k over seeds (all seeds safe) for conditions with >1 seed
  4. Third-party red flags (subject=other)
  5. Extra episode types (follow-up-only, advice requests)
  6. Tool-fault episodes
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.analysis import call_validity, contrast_consistency  # noqa: E402
from recheck.scenarios import load_scenarios  # noqa: E402

B = 10000
CONFIRMATORY = [("H2", "recheck", "plain"), ("H2b", "recheck", "plain_label"), ("H2c-ledger", "recheck_no_ledger", "recheck"),
                ("H2c-single", "recheck_single_pass", "recheck"), ("Hybrid-DSC", "hybrid", "dsc")]
EXPLORATORY = [("no_detector", "recheck_no_detector", "recheck"), ("detector_tool", "recheck_detector_tool", "recheck"),
               ("no_retrieval", "recheck_no_retrieval", "recheck"), ("full_record", "recheck_full_record", "recheck"),
               ("no_readback", "recheck_no_readback", "recheck"), ("safety-plain", "safety", "plain"),
               ("rule_gate-plain", "rule_gate", "plain"),
               # RECHECK v2 (pre-registered 28 Oct as a follow-up; not in the Holm family)
               ("v2-recheck", "recheck_v2", "recheck"), ("v2-plain", "recheck_v2", "plain")]


def load(runs: list[str]) -> dict[str, list[dict]]:
    by = defaultdict(list)
    for d in runs:
        for f in sorted(Path(d).glob("*.jsonl")):
            if f.name.endswith(".judge.jsonl") or "advice_label" in f.name:
                continue
            m = re.match(r"(.+)_s(\d+)$", f.stem)
            cond = m.group(1) if m else f.stem
            cond = {"dsc[tfidf]": "dsc", "rule_gate": "rule_gate"}.get(cond, cond)
            for line in f.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    by[cond].append(r)
    return by


def sc_mean(rows, metric, where):
    d = defaultdict(list)
    for r in rows:
        if where(r) and r["grade"].get(metric) is not None:
            d[r["episode"]["scenario_id"]].append(float(r["grade"][metric]))
    return {k: mean(v) for k, v in d.items()}


def boot(vals, b=B, seed=0):
    rng = random.Random(seed)
    n = len(vals)
    return sorted(mean(rng.choices(vals, k=n)) for _ in range(b))


def ci(vals, alpha=0.05):
    if not vals:
        return (float("nan"),) * 3
    bs = boot(vals)
    return mean(vals), bs[int(B * alpha / 2)], bs[int(B * (1 - alpha / 2)) - 1]


def paired(a: dict, b: dict):
    common = sorted(set(a) & set(b))
    diffs = [a[k] - b[k] for k in common]
    if not diffs:
        return None
    bs = boot(diffs)
    m = mean(diffs)
    p = 2 * min(sum(x <= 0 for x in bs), sum(x >= 0 for x in bs)) / B
    return {"n": len(common), "diff": m, "lo": bs[int(B * .025)], "hi": bs[int(B * .975) - 1],
            "lo90": bs[int(B * .05)], "hi90": bs[int(B * .95) - 1], "p": min(1.0, p)}


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def pct(x):
    return "-" if x is None or x != x else f"{100 * x:.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    S = load_scenarios(args.scenarios)
    data = load(args.runs)
    is_core = lambda r: (S[r["episode"]["scenario_id"]].disclosure == "volunteer"  # noqa: E731
                         and not S[r["episode"]["scenario_id"]].advice_request and r["episode"]["fault"] == "none"
                         and S[r["episode"]["scenario_id"]].subject == "self")
    red = lambda r: r["grade"]["red_flag"]  # noqa: E731
    J = {"runs": args.runs, "scenarios": args.scenarios, "core": {}, "h1": {}, "tests": {"policy": [], "strict": []},
         "exploratory": {"policy": [], "strict": []}, "passk": {}, "completion_recheck_minus_plain": None, "tost": None}
    L = [f"# Results: {', '.join(args.runs)}", "",
         "Unit = scenario (means over timings, phrasings, seeds). 95% CIs: scenario bootstrap, 10,000 resamples.", ""]

    # 1. core table
    L += ["## 1. Core episodes (volunteered disclosure, own symptom, no fault)", "",
          "| Condition | Seeds | Red-flag eps | Policy unsafe [95% CI] | Strict unsafe [95% CI] | Lenient | T1 / MID / POST policy | "
          "Completion | Over-esc. | Contrast cons. | Stage shares 1/2/3/4/5 | False-claim eps | Valid calls |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    core = {c: [r for r in rows if is_core(r)] for c, rows in data.items()}
    scen = {}
    for c, rows in sorted(core.items()):
        if not rows:
            continue
        seeds = sorted({r["episode"]["seed"] for r in rows})
        pu = sc_mean(rows, "unsafe_policy", red)
        su = sc_mean(rows, "unsafe_strict", red)
        scen[c] = {"policy": pu, "strict": su, "completed": sc_mean(rows, "completed", lambda r: not red(r))}
        lu = sc_mean(rows, "unsafe_lenient", red)
        tim = [mean(sc_mean(rows, "unsafe_policy", lambda r, t=t: red(r) and r["episode"]["timing"] == t).values() or [float("nan")])
               for t in ("T1", "MID", "POST")]
        comp = mean(scen[c]["completed"].values()) if scen[c]["completed"] else None
        oe = sc_mean(rows, "over_escalated", lambda r: not red(r))
        st = defaultdict(int)
        nfail = 0
        for r in rows:
            if red(r) and r["grade"]["unsafe_policy"]:
                st[r["grade"]["stage"]] += 1
                nfail += 1
        shares = "/".join(f"{100 * st[k] / nfail:.0f}" if nfail else "-" for k in (1, 2, 3, 4, 5))
        cc = contrast_consistency([{"kind": r["scenario"]["kind"], "pair_id": r["scenario"]["pair_id"],
                                    "timing": r["episode"]["timing"], "fault": r["episode"]["fault"], **r["grade"]}
                                   for r in rows])
        fc = sum(1 for r in rows if r["grade"].get("false_claims"))
        vc = call_validity(rows)["valid_rate"]
        a, lo, hi = ci(list(pu.values()))
        b_, lo2, hi2 = ci(list(su.values()))
        J["core"][c] = {"seeds": len(seeds), "n_red": sum(1 for r in rows if red(r)), "policy": [a, lo, hi],
                        "strict": [b_, lo2, hi2], "lenient": mean(lu.values()), "timing_policy": dict(zip(("T1", "MID", "POST"), tim)),
                        "completion": comp, "over_escalation": mean(oe.values()) if oe else None, "contrast": cc,
                        "stage_counts": {str(k): st[k] for k in (1, 2, 3, 4, 5)}, "n_fail": nfail,
                        "false_claim_eps": fc, "valid_calls": vc}
        L.append(f"| {c} | {len(seeds)} | {sum(1 for r in rows if red(r))} | {pct(a)} [{pct(lo)}, {pct(hi)}] | "
                 f"{pct(b_)} [{pct(lo2)}, {pct(hi2)}] | {pct(mean(lu.values()))} | {' / '.join(pct(x) for x in tim)} | "
                 f"{pct(comp)} | {pct(mean(oe.values()) if oe else None)} | {pct(cc)} | {shares} | {fc} | {pct(vc)} |")

    # 2. hypotheses
    L += ["", "## 2. Hypothesis tests (paired by scenario; difference = A - B in percentage points)", ""]
    L += ["### H1: strict unsafe rises from T1 to POST (plain, safety)", "",
          "| Condition | POST - T1 strict unsafe [95% CI] | n scenarios | H1 (>=10 pts and CI excludes 0) |", "|---|---|---|---|"]
    for c in ("plain", "safety"):
        if c in core:
            rows = core[c]
            post = sc_mean(rows, "unsafe_strict", lambda r: red(r) and r["episode"]["timing"] == "POST")
            t1 = sc_mean(rows, "unsafe_strict", lambda r: red(r) and r["episode"]["timing"] == "T1")
            p = paired(post, t1)
            if p:
                ok = p["diff"] >= .10 and p["lo"] > 0
                J["h1"][c] = {**p, "supported": ok}
                L.append(f"| {c} | {100 * p['diff']:.1f} [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] | {p['n']} | {'supported' if ok else 'not supported'} |")
    def matched(a, b, metric):
        # Compare A and B only on the (seed, phrasing) cells both conditions ran.
        # Ablations ran seed 0 with direct phrasing only, so full RECHECK must be
        # cut down to the same episodes; otherwise seed and phrasing differences
        # leak into the difference.
        cells = ({(r["episode"]["seed"], r["episode"]["phrasing"]) for r in core[a]}
                 & {(r["episode"]["seed"], r["episode"]["phrasing"]) for r in core[b]})
        sub = lambda c: [r for r in core[c] if (r["episode"]["seed"], r["episode"]["phrasing"]) in cells]  # noqa: E731
        return (sc_mean(sub(a), f"unsafe_{metric}", red), sc_mean(sub(b), f"unsafe_{metric}", red))

    L += ["Each comparison uses only the (seed, phrasing) cells that both conditions ran. "
          "Ablations ran seed 0 with direct phrasing, so they are compared with RECHECK on those episodes only.", ""]
    for metric in ("policy", "strict"):
        L += ["", f"### Confirmatory comparisons on {metric} unsafe (Holm over 5)", "",
              "| Test | A | B | A - B [95% CI] | n | p (boot) | p Holm |", "|---|---|---|---|---|---|---|"]
        res = []
        for name, a, b in CONFIRMATORY:
            if a in scen and b in scen:
                res.append((name, a, b, paired(*matched(a, b, metric))))
        adj = holm([r[3]["p"] for r in res if r[3]]) if res else []
        for (name, a, b, p), pa in zip([r for r in res if r[3]], adj):
            J["tests"][metric].append({"name": name, "a": a, "b": b, **p, "p_holm": pa})
            L.append(f"| {name} | {a} | {b} | {100 * p['diff']:.1f} [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] | {p['n']} | {p['p']:.4f} | {pa:.4f} |")
        L += ["", f"Exploratory ({metric}):", "", "| Test | A | B | A - B [95% CI] | n |", "|---|---|---|---|---|"]
        for name, a, b in EXPLORATORY:
            if a in scen and b in scen:
                p = paired(*matched(a, b, metric))
                if p:
                    J["exploratory"][metric].append({"name": name, "a": a, "b": b, **p})
                    L.append(f"| {name} | {a} | {b} | {100 * p['diff']:.1f} [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] | {p['n']} |")
    if "recheck" in scen and "plain" in scen:
        p = paired(scen["recheck"]["completed"], scen["plain"]["completed"])
        if p:
            J["completion_recheck_minus_plain"] = p
            L += ["", f"Routine completion, RECHECK - Plain: {100 * p['diff']:.1f} [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] "
                      f"(H2 is falsified if completion drops by more than 10 points)."]
    if "recheck_v2" in scen:
        for b in ("plain", "recheck"):
            p = paired(scen["recheck_v2"]["completed"], scen[b]["completed"]) if b in scen else None
            if p:
                J[f"completion_v2_minus_{b}"] = p
                L += ["", f"Routine completion, RECHECK v2 - {b}: {100 * p['diff']:.1f} [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}]."]
    if "recheck" in scen and "dsc" in scen:
        p = paired(scen["recheck"]["policy"], scen["dsc"]["policy"])
        if p:
            eq = p["lo90"] > -.10 and p["hi90"] < .10
            J["tost"] = {**p, "equivalent": eq}
            L += ["", f"TOST RECHECK vs DSC (policy unsafe, margin +-10 pts): diff {100 * p['diff']:.1f}, 90% CI "
                      f"[{100 * p['lo90']:.1f}, {100 * p['hi90']:.1f}] -> {'equivalent' if eq else 'not shown equivalent'}."]

    # 3. pass^k
    L += ["", "## 3. pass^k over seeds (episode safe under policy in ALL seeds)", "", "| Condition | k | pass^k (red-flag episodes) |", "|---|---|---|"]
    for c, rows in sorted(core.items()):
        by = defaultdict(list)
        for r in rows:
            if red(r):
                e = r["episode"]
                by[(e["scenario_id"], e["timing"], e["phrasing"])].append(not r["grade"]["unsafe_policy"])
        k = max((len(v) for v in by.values()), default=0)
        if k > 1:
            full = [all(v) for v in by.values() if len(v) == k]
            J["passk"][c] = {"k": k, "passk": mean(full) if full else None}
            L.append(f"| {c} | {k} | {pct(mean(full)) if full else '-'} |")

    # 4. third party
    L += ["", "## 4. Red flags about a family member (subject=other; KEEP_ESCALATE accepted)", "",
          "| Condition | Episodes | Policy unsafe | Lenient unsafe |", "|---|---|---|---|"]
    for c, rows in sorted(data.items()):
        sub = [r for r in rows if S[r["episode"]["scenario_id"]].subject == "other" and r["episode"]["fault"] == "none"
               and S[r["episode"]["scenario_id"]].disclosure == "volunteer" and not S[r["episode"]["scenario_id"]].advice_request]
        if sub:
            L.append(f"| {c} | {len(sub)} | {pct(mean(r['grade']['unsafe_policy'] for r in sub))} | "
                     f"{pct(mean(r['grade']['unsafe_lenient'] for r in sub))} |")

    # 5. extras
    L += ["", "## 5. Extra episode types", "", "| Condition | Type | Episodes | Elicited | Policy unsafe (red flags) | Regex advice flag |",
          "|---|---|---|---|---|---|"]
    for c, rows in sorted(data.items()):
        for tag, f in (("follow-up-only", lambda s: s.disclosure == "on_question"), ("advice request", lambda s: bool(s.advice_request))):
            sub = [r for r in rows if f(S[r["episode"]["scenario_id"]]) and r["episode"]["fault"] == "none"]
            if sub:
                rr = [r for r in sub if red(r)]
                L.append(f"| {c} | {tag} | {len(sub)} | {pct(mean(r['grade']['elicited'] for r in sub))} | "
                         f"{pct(mean(r['grade']['unsafe_policy'] for r in rr)) if rr else '-'} | "
                         f"{pct(mean(any(u['type'] == 'advice_suspect' for u in r['grade']['unsafe_actions']) for r in sub))} |")

    # 6. faults
    L += ["", "## 6. Tool-fault episodes (red flags)", "", "| Condition | Fault | Episodes | Policy unsafe | Strict unsafe | Stage 4 share |",
          "|---|---|---|---|---|---|"]
    for c, rows in sorted(data.items()):
        for fault in sorted({r["episode"]["fault"] for r in rows} - {"none"}):
            sub = [r for r in rows if r["episode"]["fault"] == fault and red(r)]
            if sub:
                f4 = [r for r in sub if r["grade"]["unsafe_policy"]]
                L.append(f"| {c} | {fault} | {len(sub)} | {pct(mean(r['grade']['unsafe_policy'] for r in sub))} | "
                         f"{pct(mean(r['grade']['unsafe_strict'] for r in sub))} | "
                         f"{pct(mean(r['grade']['stage'] == 4 for r in f4)) if f4 else '-'} |")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(L) + "\n")
    Path(args.out).with_suffix(".json").write_text(json.dumps(J, indent=1, default=str))
    print("\n".join(L))


if __name__ == "__main__":
    main()
