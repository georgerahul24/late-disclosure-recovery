"""Generate every number/table in the mid-submission report from run files.

    python scripts/make_report_tables.py --runs runs/mid runs/scripted_main runs/scripted_faults \
        --detectors runs/detector_eval/results_keyword_tfidf_lora_lora_lora_lora_lora_lora_prompted.json \
        --out "ai report/tables"

Writes one .tex file per table plus numbers.tex (\newcommand macros for
numbers quoted in the text). Never type result numbers by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import summarize_runs as S  # noqa: E402
from recheck.scenarios import load_scenarios  # noqa: E402

NAMES = {"book_only": "Book-only", "rule_gate": "Rule gate (keywords)", "plain": "Plain LLM",
         "plain_label": "Plain + Label", "dsc": "DSC (no LLM)", "safety": "Safety prompt", "recheck": r"\recheck{}",
         "hybrid": "Hybrid"}
ORDER = ["book_only", "rule_gate", "plain", "plain_label", "safety", "recheck", "hybrid", "dsc"]


def pc(x, d=1):
    return "--" if x is None or x != x else f"{100 * x:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--detectors", required=True)
    ap.add_argument("--scenarios", default=str(ROOT / "data/eval/scenarios_v1.json"))
    ap.add_argument("--gee", help="markdown output of scripts/timing_model.py")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    SC = load_scenarios(args.scenarios)
    data = S.load(args.runs)
    is_core = lambda r: (SC[r["episode"]["scenario_id"]].disclosure == "volunteer"  # noqa: E731
                         and not SC[r["episode"]["scenario_id"]].advice_request and r["episode"]["fault"] == "none"
                         and SC[r["episode"]["scenario_id"]].subject == "self")
    red = lambda r: r["grade"]["red_flag"]  # noqa: E731
    conds = [c for c in ORDER if c in data]
    core = {c: [r for r in data[c] if is_core(r)] for c in conds}
    M = {}  # macros

    def mac(name, val):
        M[name] = val

    # ---- main table ------------------------------------------------------
    T = [r"\begin{tabular}{lrrrrrrrr}\toprule",
         r" & \multicolumn{3}{c}{Unsafe (\% of red-flag)} & \multicolumn{3}{c}{Policy unsafe by timing} & & \\",
         r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
         r"Condition & Policy [95\% CI] & Strict & Lenient & T1 & MID & POST & Compl. & Contrast \\ \midrule"]
    scen = {}
    for c in conds:
        rows = core[c]
        pu = S.sc_mean(rows, "unsafe_policy", red)
        su = S.sc_mean(rows, "unsafe_strict", red)
        lu = S.sc_mean(rows, "unsafe_lenient", red)
        comp = S.sc_mean(rows, "completed", lambda r: not red(r))
        scen[c] = {"policy": pu, "strict": su, "lenient": lu, "completed": comp}
        tim = [mean(S.sc_mean(rows, "unsafe_policy", lambda r, t=t: red(r) and r["episode"]["timing"] == t).values())
               for t in ("T1", "MID", "POST")]
        cc = S.contrast_consistency([{"kind": r["scenario"]["kind"], "pair_id": r["scenario"]["pair_id"],
                                      "timing": r["episode"]["timing"], "fault": r["episode"]["fault"], **r["grade"]}
                                     for r in rows])
        a, lo, hi = S.ci(list(pu.values()))
        T.append(f"{NAMES[c]} & {pc(a)} [{pc(lo)}, {pc(hi)}] & {pc(mean(su.values()))} & {pc(mean(lu.values()))} & "
                 f"{pc(tim[0])} & {pc(tim[1])} & {pc(tim[2])} & {pc(mean(comp.values()))} & {pc(cc)} \\\\")
        k = c.replace("_", "")
        mac(f"{k}Policy", pc(a)); mac(f"{k}Strict", pc(mean(su.values()))); mac(f"{k}Lenient", pc(mean(lu.values())))
        mac(f"{k}Compl", pc(mean(comp.values()))); mac(f"{k}Eps", str(len(rows)))
        mac(f"{k}Escal", pc(1 - mean(lu.values())))
        mac(f"{k}TOne", pc(tim[0])); mac(f"{k}TMid", pc(tim[1])); mac(f"{k}TPost", pc(tim[2]))
        oe = S.sc_mean(rows, "over_escalated", lambda r: not red(r))
        mac(f"{k}OverEsc", pc(mean(oe.values())))
        mac(f"{k}FalseClaim", str(sum(1 for r in rows if r["grade"].get("false_claims"))))
        vc = S.call_validity(rows)["valid_rate"]
        mac(f"{k}Valid", pc(vc))
    T.append(r"\bottomrule\end{tabular}")
    (out / "main.tex").write_text("\n".join(T) + "\n")

    # ---- stages ----------------------------------------------------------
    T = [r"\begin{tabular}{lrrrrrr}\toprule",
         r"Condition & Failed eps & 1 Detect & 2 Context & 3 Not revised & 4 Repair failed & 5 Not escalated \\ \midrule"]
    for c in conds:
        st = defaultdict(int)
        n = 0
        for r in core[c]:
            if red(r) and r["grade"]["unsafe_policy"]:
                st[r["grade"]["stage"]] += 1
                n += 1
        if n:
            T.append(f"{NAMES[c]} & {n} & " + " & ".join(f"{100 * st[k] / n:.0f}" for k in (1, 2, 3, 4, 5)) + r" \\")
            if c in ("plain", "plain_label"):
                mac(f"{c.replace('_', '')}StageThree", f"{100 * st[3] / n:.0f}")
                mac(f"{c.replace('_', '')}StageTwo", f"{100 * st[2] / n:.0f}")
                mac(f"{c.replace('_', '')}StageOne", f"{100 * st[1] / n:.0f}")
    T.append(r"\bottomrule\end{tabular}")
    (out / "stages.tex").write_text("\n".join(T) + "\n")

    # ---- paired comparisons ----------------------------------------------
    T = [r"\begin{tabular}{llrrr}\toprule", r"Comparison & Metric & Diff. (pts) & 95\% CI & $p$ \\ \midrule"]
    comps = [("recheck", "plain", r"\recheck{} $-$ Plain (H2)"), ("recheck", "plain_label", r"\recheck{} $-$ Plain + Label (H2b)"),
             ("hybrid", "recheck", r"Hybrid $-$ \recheck{}"), ("hybrid", "dsc", "Hybrid $-$ DSC"),
             ("plain_label", "plain", "Plain + Label $-$ Plain"), ("rule_gate", "plain", "Rule gate $-$ Plain")]
    for a, b, lab in comps:
        if a in scen and b in scen:
            for m in ("policy", "strict", "lenient"):
                p = S.paired(scen[a][m], scen[b][m])
                T.append(f"{lab} & {m} & {100 * p['diff']:.1f} & [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] & "
                         f"{'$<$0.001' if p['p'] < 0.001 else f'{p['p']:.3f}'} \\\\")
                if (a, b) in (("recheck", "plain"), ("recheck", "plain_label"), ("hybrid", "dsc"), ("hybrid", "recheck")):
                    tag = {"plain": "VsPlain", "plain_label": "VsLabel", "dsc": "VsDsc", "recheck": "VsRecheck"}[b]
                    mac(f"{a}{tag}{m.capitalize()}", f"{100 * p['diff']:.1f}")
                    mac(f"{a}{tag}{m.capitalize()}Lo", f"{100 * p['lo']:.1f}")
                    mac(f"{a}{tag}{m.capitalize()}Hi", f"{100 * p['hi']:.1f}")
                if a == "plain_label":
                    mac(f"labelDiff{m.capitalize()}", f"{100 * p['diff']:.1f}")
                    mac(f"labelLo{m.capitalize()}", f"{100 * p['lo']:.1f}")
                    mac(f"labelHi{m.capitalize()}", f"{100 * p['hi']:.1f}")
    # routine completion change (H2 completion criterion)
    for a, b in (("recheck", "plain"), ("hybrid", "plain")):
        if a in scen and b in scen:
            p = S.paired(scen[a]["completed"], scen[b]["completed"])
            T.append(f"{NAMES[a]} $-$ Plain & routine completion & {100 * p['diff']:.1f} & [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] & "
                     f"{'$<$0.001' if p['p'] < 0.001 else f'{p['p']:.3f}'} \\\\")
            mac(f"{a}ComplDrop", f"{-100 * p['diff']:.1f}")
    # H1
    for c in ("plain", "plain_label"):
        if c in core:
            for m in ("unsafe_strict", "unsafe_policy"):
                post = S.sc_mean(core[c], m, lambda r: red(r) and r["episode"]["timing"] == "POST")
                t1 = S.sc_mean(core[c], m, lambda r: red(r) and r["episode"]["timing"] == "T1")
                p = S.paired(post, t1)
                T.append(f"H1 POST $-$ T1, {NAMES[c]} & {m.split('_')[1]} & {100 * p['diff']:.1f} & "
                         f"[{100 * p['lo']:.1f}, {100 * p['hi']:.1f}] & {'$<$0.001' if p['p'] < 0.001 else f'{p['p']:.3f}'} \\\\")
                mac(f"hOne{c.replace('_', '')}{m.split('_')[1].capitalize()}", f"{100 * p['diff']:.1f}")
    T.append(r"\bottomrule\end{tabular}")
    (out / "paired.tex").write_text("\n".join(T) + "\n")

    # why routine episodes were not completed
    T = [r"\begin{tabular}{lrrrrr}\toprule",
         r"Condition & Routine eps & Not completed & No booking at all & Never called \texttt{book} & Claimed ``booked'' falsely \\ \midrule"]
    for c in conds:
        rows = [r for r in core[c] if not red(r)]
        nc = [r for r in rows if not r["grade"]["completed"]]
        if not rows or c in ("book_only", "rule_gate"):
            continue
        noact = sum(1 for r in nc if r["grade"]["end_state"] == "NO_ACTION")
        nobook = sum(1 for r in nc if not any(x["name"] == "book" for x in r["calls"]))
        fb = sum(1 for r in nc if any(x["claim"] == "book" for x in r["grade"].get("false_claims", [])))
        T.append(f"{NAMES[c]} & {len(rows)} & {len(nc)} & {noact} & {nobook} & {fb} \\\\")
        if c == "recheck":
            mac("recheckRoutineFail", str(len(nc))); mac("recheckNoAction", str(noact))
            mac("recheckNoBook", str(nobook)); mac("recheckFalseBook", str(fb))
    T.append(r"\bottomrule\end{tabular}")
    (out / "routine.tex").write_text("\n".join(T) + "\n")

    # ---- pass^k, third party, extras, faults -----------------------------
    T = [r"\begin{tabular}{lrrrrr}\toprule",
         r"Condition & pass$^3$ & Family-member flags & Follow-up-only & Advice request & Escalated (lenient safe) \\",
         r" & (\% safe all seeds) & policy unsafe & policy unsafe & policy unsafe & \% red-flag eps \\ \midrule"]
    for c in conds:
        by = defaultdict(list)
        for r in core[c]:
            if red(r):
                e = r["episode"]
                by[(e["scenario_id"], e["timing"], e["phrasing"])].append(not r["grade"]["unsafe_policy"])
        k = max(len(v) for v in by.values())
        pk = mean(all(v) for v in by.values() if len(v) == k) if k > 1 else None
        rows = data[c]
        tp = [r for r in rows if SC[r["episode"]["scenario_id"]].subject == "other" and r["episode"]["fault"] == "none"
              and SC[r["episode"]["scenario_id"]].disclosure == "volunteer" and not SC[r["episode"]["scenario_id"]].advice_request]
        ask = [r for r in rows if SC[r["episode"]["scenario_id"]].disclosure == "on_question" and red(r)]
        adv = [r for r in rows if SC[r["episode"]["scenario_id"]].advice_request and red(r) and r["episode"]["fault"] == "none"]
        f = lambda xs: pc(mean(r["grade"]["unsafe_policy"] for r in xs)) if xs else "--"  # noqa: E731
        T.append(f"{NAMES[c]} & {pc(pk)} & {f(tp)} & {f(ask)} & {f(adv)} & {pc(1 - mean(scen[c]['lenient'].values()))} \\\\")
        mac(f"{c.replace('_', '')}PassK", pc(pk))
    T.append(r"\bottomrule\end{tabular}")
    (out / "extras.tex").write_text("\n".join(T) + "\n")

    T = [r"\begin{tabular}{llrrr}\toprule", r"Controller & Fault & Red-flag eps & Policy unsafe & Strict unsafe \\ \midrule"]
    for c in conds:
        for fault in sorted({r["episode"]["fault"] for r in data[c]} - {"none"}):
            sub = [r for r in data[c] if r["episode"]["fault"] == fault and red(r)]
            T.append(f"{NAMES[c]} & {fault.replace('_', ' ')} & {len(sub)} & {pc(mean(r['grade']['unsafe_policy'] for r in sub))} & "
                     f"{pc(mean(r['grade']['unsafe_strict'] for r in sub))} \\\\")
    T.append(r"\bottomrule\end{tabular}")
    (out / "faults.tex").write_text("\n".join(T) + "\n")

    # ---- detectors -------------------------------------------------------
    D = json.loads(Path(args.detectors).read_text())
    groups = defaultdict(list)
    for r in D:
        name = r["detector"]
        if name.startswith("lora[Qwen2.5-1.5B"):
            g = "LoRA Qwen2.5-1.5B (3 seeds)"
        elif name.startswith("lora[Qwen2.5-0.5B"):
            g = "LoRA Qwen2.5-0.5B (3 seeds)"
        elif name.startswith("prompted"):
            g = "Prompted Qwen2.5-7B (zero-shot)"
        else:
            g = {"keyword": "Keyword list (frozen)", "tfidf": "TF-IDF + LR"}.get(name, name)
        groups[(g, r["variant"])].append(r)
    T = [r"\begin{tabular}{llrrrr}\toprule", r"Detector & Text & Sensitivity & Specificity & PPV & Macro-F1 \\ \midrule"]
    order = ["Keyword list (frozen)", "TF-IDF + LR", "Prompted Qwen2.5-7B (zero-shot)", "LoRA Qwen2.5-0.5B (3 seeds)",
             "LoRA Qwen2.5-1.5B (3 seeds)"]
    for g in order:
        for v in ("symptom-only", "reworded", "in-message"):
            rs = groups.get((g, v), [])
            if not rs:
                continue

            def fmt(key):
                xs = [r[key] for r in rs if r[key] is not None]
                if not xs:
                    return "--"
                return f"{100 * mean(xs):.1f}" + (f" $\\pm$ {100 * stdev(xs):.1f}" if len(xs) > 1 else "")
            T.append(f"{g if v == 'symptom-only' else ''} & {v} & {fmt('sensitivity')} & {fmt('specificity')} & "
                     f"{fmt('ppv')} & {fmt('macro_f1')} \\\\")
            if v == "in-message":
                key = {"Keyword list (frozen)": "detKw", "TF-IDF + LR": "detTfidf", "Prompted Qwen2.5-7B (zero-shot)": "detPrompt",
                       "LoRA Qwen2.5-0.5B (3 seeds)": "detLoraSmall", "LoRA Qwen2.5-1.5B (3 seeds)": "detLora"}[g]
                mac(f"{key}Sens", f"{100 * mean(r['sensitivity'] for r in rs):.1f}")
                mac(f"{key}Spec", f"{100 * mean(r['specificity'] for r in rs):.1f}")
            if v == "reworded":
                key = {"Keyword list (frozen)": "detKw", "TF-IDF + LR": "detTfidf", "Prompted Qwen2.5-7B (zero-shot)": "detPrompt",
                       "LoRA Qwen2.5-0.5B (3 seeds)": "detLoraSmall", "LoRA Qwen2.5-1.5B (3 seeds)": "detLora"}[g]
                mac(f"{key}SensRew", f"{100 * mean(r['sensitivity'] for r in rs):.1f}")
        T.append(r"\addlinespace")
    T.append(r"\bottomrule\end{tabular}")
    (out / "detectors.tex").write_text("\n".join(T) + "\n")

    # LoRA dev metrics
    T = [r"\begin{tabular}{lrrr}\toprule", r"Detector & Seed & Train / dev examples & Best dev macro-F1 \\ \midrule"]
    for f in sorted((ROOT / "runs/detector").glob("*.metrics.json")):
        m = json.loads(f.read_text())
        T.append(f"{Path(m['base']).name} & {m['seed']} & {m['n_train']} / {m['n_dev']} & {m['best_dev_macro_f1']:.3f} \\\\")
    T.append(r"\bottomrule\end{tabular}")
    (out / "lora_dev.tex").write_text("\n".join(T) + "\n")

    if args.gee and Path(args.gee).exists():
        def nice_term(t: str) -> str | None:
            short = {"plain_label": "Plain + Label", "recheck": r"\recheck{}", "hybrid": "Hybrid", "safety": "Safety"}
            m = re.fullmatch(r"C\(condition\)\[T\.(\w+)\]", t)
            if m:
                return f"{short.get(m.group(1), m.group(1))} (vs Plain)"
            m = re.fullmatch(r"C\(timing\)\[T\.(\w+)\]", t)
            if m:
                return f"{m.group(1)} (vs T1)"
            m = re.fullmatch(r"C\(seed\)\[T\.(\d)\]", t)
            if m:
                return f"Seed {m.group(1)}"
            if t == "C(phrasing)[T.indirect]":
                return "Indirect phrasing"
            m = re.fullmatch(r"C\(condition\)\[T\.(\w+)\]:C\(timing\)\[T\.(\w+)\]", t)
            if m:
                return f"{short.get(m.group(1), m.group(1))} $\\times$ {m.group(2)}"
            return None
        T = [r"\begin{tabular}{lrrr}\toprule", r"Term & Odds ratio & 95\% CI & $p$ \\ \midrule"]
        for line in Path(args.gee).read_text().splitlines():
            parts = [x.strip() for x in line.strip("|").split("|")]
            if len(parts) == 4 and nice_term(parts[0]):
                T.append(f"{nice_term(parts[0])} & {parts[1]} & {parts[2]} & {parts[3]} \\\\")
                if parts[0] == "C(timing)[T.POST]":
                    mac("geePostOR", parts[1]); mac("geePostCI", parts[2]); mac("geePostP", parts[3])
                if parts[0] == "C(timing)[T.MID]":
                    mac("geeMidOR", parts[1])
                if parts[0] == "C(phrasing)[T.indirect]":
                    mac("geeIndirectOR", parts[1])
        T.append(r"\bottomrule\end{tabular}")
        (out / "gee.tex").write_text("\n".join(T) + "\n")
    (out / "numbers.tex").write_text("% generated by scripts/make_report_tables.py\n" +
                                     "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(M.items())) + "\n")
    print(f"wrote tables to {out}: {sorted(p.name for p in out.glob('*.tex'))}")


if __name__ == "__main__":
    main()
