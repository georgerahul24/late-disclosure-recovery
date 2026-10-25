"""Scripted-controller pilot (no LLM). Rebuilds proposal Table 2 on the dev fixtures.

    python scripts/run_pilot.py [--scenarios data/dev/scenarios.json] [--out runs/pilot]

Writes one JSONL per controller plus summary.md / summary.json in --out.
Numbers will NOT match the proposal's Table 2 exactly: the original pilot
code was not handed over and the dev fixtures are different. What must hold
are the sanity checks (oracle = 0% unsafe and 100% completion, book-only =
100% unsafe); these are asserted at the end.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.analysis import fmt_ci, summarize  # noqa: E402
from recheck.controllers import ScriptedController, book_only, dsc, rule_gate  # noqa: E402
from recheck.detectors import KeywordDetector, OracleDetector, TfidfDetector, augment_with_carriers, load_seeds  # noqa: E402
from recheck.policy import load_policy  # noqa: E402
from recheck.records import load_patients  # noqa: E402
from recheck.runner import run_suite  # noqa: E402
from recheck.scenarios import expand_episodes, load_scenarios  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "dev"))
    ap.add_argument("--scenarios")
    ap.add_argument("--patients")
    ap.add_argument("--policy")
    ap.add_argument("--seeds", default=str(ROOT / "data" / "detector" / "dev_seeds.json"),
                    help="detector training seeds for the TF-IDF stand-in")
    ap.add_argument("--out", default=str(ROOT / "runs" / "pilot"))
    args = ap.parse_args()
    data = Path(args.data)
    patients = load_patients(args.patients or data / "patients.json")
    scenarios = load_scenarios(args.scenarios or data / "scenarios.json")
    policy = load_policy(args.policy or data / "policy.json")
    kw = KeywordDetector.from_file(ROOT / "data" / "detector" / "keywords.json")
    seeds = augment_with_carriers(load_seeds(args.seeds))
    tfidf = TfidfDetector().fit([s["text"] for s in seeds], [s["label"] for s in seeds])

    main_eps = expand_episodes(scenarios, phrasings=("direct", "indirect"))
    fault_eps = expand_episodes(scenarios, phrasings=("direct",),
                                faults=("cancel_fails_once", "book_lost_response", "slot_taken"))
    fault_eps = [e for e in fault_eps if e.fault != "none"]

    controllers = [
        book_only(),
        rule_gate(kw),
        ScriptedController(kw, "record", "cancel", name="keyword/record/cancel"),
        ScriptedController(tfidf, "ignore", "cancel", name="tfidf/ignore/cancel"),
        ScriptedController(tfidf, "always", "cancel", name="tfidf/always/cancel"),
        ScriptedController(tfidf, "record", "none", name="tfidf/record/none"),
        ScriptedController(tfidf, "record", "cancel", name="tfidf/record/cancel"),
        dsc(tfidf),
        ScriptedController(OracleDetector(), "ignore", "cancel", name="oracle/ignore/cancel"),
        ScriptedController(OracleDetector(), "always", "cancel", name="oracle/always/cancel"),
        ScriptedController(OracleDetector(), "record", "none", name="oracle/record/none"),
        ScriptedController(OracleDetector(), "record", "cancel", name="oracle/record/cancel"),
        ScriptedController(OracleDetector(), "record", "convert", name="oracle/record/convert"),
    ]
    fault_controllers = [
        ScriptedController(OracleDetector(), "record", "cancel", name="oracle/record/cancel (no rb)"),
        dsc(OracleDetector(), readback=False),
        dsc(OracleDetector(), readback=True),
    ]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    lines = ["| Controller | Policy unsafe [CI] | Strict unsafe [CI] | Lenient | POST policy | Completion | Over-esc | Contrast cons. | Stages (policy) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for c in controllers:
        res = run_suite(main_eps, scenarios, patients, policy, c, out_path=out / f"{c.name.replace('/', '_')}.jsonl")
        s = summarize(res)
        summary[c.name] = s
        cc = s["contrast_consistency"]
        lines.append(f"| {c.name} | {fmt_ci(s['unsafe_policy'])} | {fmt_ci(s['unsafe_strict'])} | "
                     f"{100*s['unsafe_lenient'][0]:.1f} | {100*s['unsafe_policy_POST']:.1f} | "
                     f"{100*s['completed'][0]:.1f} | {100*s['over_escalated'][0]:.1f} | "
                     f"{'-' if cc is None else f'{100*cc:.1f}'} | {s['stages']} |")
    lines += ["", "Tool-fault episodes (red-flag scenarios only, direct phrasing):", "",
              "| Controller | Fault | Policy unsafe | Strict unsafe | Stages |", "|---|---|---|---|---|"]
    for c in fault_controllers:
        for f in ("cancel_fails_once", "book_lost_response", "slot_taken"):
            eps = [e for e in fault_eps if e.fault == f]
            res = run_suite(eps, scenarios, patients, policy, c)
            s = summarize(res)
            summary[f"{c.name}|{f}"] = s
            lines.append(f"| {c.name} | {f} | {100*s['unsafe_policy'][0]:.1f} | {100*s['unsafe_strict'][0]:.1f} | {s['stages']} |")

    n = summary["book_only"]
    header = (f"# Scripted pilot on dev fixtures\n\n{n['n_episodes']} episodes per controller "
              f"({n['n_red_flag']} red-flag, {n['n_routine']} routine) from {len(scenarios)} scenarios. "
              "Unsafe rates are % of red-flag episodes, averaged within scenario, 95% scenario-bootstrap CI. "
              "Completion and over-escalation are % of routine episodes.\n\n")
    (out / "summary.md").write_text(header + "\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(header + "\n".join(lines))

    # Sanity checks (proposal: "eleven automatic checks"; these are the core ones)
    o = summary["oracle/record/cancel"]
    assert o["unsafe_policy"][0] == 0 and o["unsafe_strict"][0] == 0, "oracle must be 0% unsafe"
    assert o["completed"][0] == 1.0, "oracle must complete every routine episode"
    assert summary["book_only"]["unsafe_lenient"][0] == 1.0, "book-only must be 100% unsafe"
    assert summary["oracle/record/none"]["unsafe_policy_T1"] == 0, "no-revision is safe when disclosed before booking"
    print("\nsanity checks passed")


if __name__ == "__main__":
    main()
