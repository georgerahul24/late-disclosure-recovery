"""Automatic failure breakdown from tool logs (all failed episodes, no sampling).

    python scripts/failure_breakdown.py --runs runs/llm_main runs/scripted_main --out results/failure_breakdown_v1.md

Over red-flag CORE episodes (own symptom, volunteered, no fault) that are
policy-unsafe, per condition, the share with each pattern. Patterns are not
exclusive. All come from the stored tool log, notes and final state:
  end_<STATE>           final end state
  booked_after_flag     a routine `book` succeeded at or after the disclosure turn
  no_record_search      record-dependent scenario, no successful search_record /
                        get_patient_record call after the disclosure
  note_flagged          the agent's own NOTE marked the symptom (detected or urgent)
                        after disclosure, yet the end state is unsafe
  repair_no_escalate    a cancel / update_appointment succeeded after the
                        disclosure but no escalation happened
  false_claim           the episode has a false action claim
A second table does the same for red flags about a family member (subject=other),
where KEEP_ESCALATE is acceptable.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from recheck.scenarios import load_scenarios  # noqa: E402
from summarize_runs import load  # noqa: E402

ORDER = ["plain", "plain_label", "safety", "recheck", "hybrid", "recheck_v2", "rule_gate", "dsc", "book_only"]
STATES = ["ROUTINE_BOOKED", "NO_ACTION", "KEEP_ESCALATE", "HANDOVER", "CANCEL_ESCALATE", "CONVERT_URGENT"]
PATTERNS = ["booked_after_flag", "no_record_search", "note_flagged", "repair_no_escalate", "false_claim"]


def patterns(r, sc) -> set[str]:
    d = r["disclosed_turn"] if r["disclosed_turn"] is not None else 0
    after = [c for c in r["calls"] if c["ok"] and c["turn"] >= d]
    out = {f"end_{r['grade']['end_state']}"}
    if any(c["name"] == "book" for c in after):
        out.add("booked_after_flag")
    if sc.kind == "record_dependent" and not any(c["name"] in ("search_record", "get_patient_record") for c in after):
        out.add("no_record_search")
    if any((n.get("detected") or n.get("urgent")) for n in r["notes"] if n.get("turn", -1) >= d):
        out.add("note_flagged")
    if any(c["name"] in ("cancel", "update_appointment") for c in after) and not r["grade"]["end"]["any_escalation"]:
        out.add("repair_no_escalate")
    if r["grade"].get("false_claims"):
        out.add("false_claim")
    return out


def table(title, data, keep, SC):
    L = [f"## {title}", "", "| Condition | Unsafe eps | " + " | ".join(STATES) + " | " + " | ".join(PATTERNS) + " |",
         "|---" * (2 + len(STATES) + len(PATTERNS)) + "|"]
    for c in [c for c in ORDER if c in data] + sorted(set(data) - set(ORDER)):
        fails = [r for r in data[c] if keep(r) and r["grade"]["unsafe_policy"]]
        if not fails:
            continue
        cnt = Counter(p for r in fails for p in patterns(r, SC[r["episode"]["scenario_id"]]))
        pc = lambda k: f"{100 * cnt[k] / len(fails):.0f}"  # noqa: E731
        L.append(f"| {c} | {len(fails)} | " + " | ".join(pc(f"end_{s}") for s in STATES) + " | "
                 + " | ".join(pc(p) for p in PATTERNS) + " |")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    SC = load_scenarios(args.scenarios)
    data = load(args.runs)

    def base(r):
        s = SC[r["episode"]["scenario_id"]]
        return (r["grade"]["red_flag"] and r["episode"]["fault"] == "none" and s.disclosure == "volunteer"
                and not s.advice_request)
    L = ["# Failure breakdown (automatic, from tool logs)", "",
         f"Runs: {', '.join(args.runs)}. Made by `scripts/failure_breakdown.py`. Cells are % of the condition's "
         "policy-unsafe red-flag episodes. End-state columns add to 100; pattern columns can overlap.", ""]
    L += table("Own symptom (core)", data, lambda r: base(r) and SC[r["episode"]["scenario_id"]].subject == "self", SC)
    L += [""] + table("Family member's symptom (subject = other; KEEP_ESCALATE accepted)", data,
                      lambda r: base(r) and SC[r["episode"]["scenario_id"]].subject == "other", SC)
    # family-member: all episodes (not only failures), end-state shares
    L += ["", "## Family member's symptom: end states over ALL episodes (%)", "",
          "| Condition | Episodes | " + " | ".join(STATES) + " |", "|---" * (2 + len(STATES)) + "|"]
    for c in [c for c in ORDER if c in data]:
        rows = [r for r in data[c] if base(r) and SC[r["episode"]["scenario_id"]].subject == "other"]
        if rows:
            cnt = Counter(r["grade"]["end_state"] for r in rows)
            L.append(f"| {c} | {len(rows)} | " + " | ".join(f"{100 * cnt[s] / len(rows):.0f}" for s in STATES) + " |")
    Path(args.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
