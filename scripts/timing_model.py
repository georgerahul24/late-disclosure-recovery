"""Model-based timing analysis (proposal section 9).

The proposal planned a mixed-effects logistic model
    unsafe ~ condition x timing + seed + (1|scenario) + (1|patient).
Each core scenario here has its own patient, so (1|patient) is the same
grouping as (1|scenario). We fit a binomial GEE with an exchangeable working
correlation, clustered by scenario (statsmodels). It gives population-average
odds ratios with cluster-robust standard errors. This is a documented
deviation: no frequentist GLMM (lme4) is available in this Python stack.

    python scripts/timing_model.py --runs runs/llm_main --scenarios data/eval/scenarios_v1.json \
        --conditions plain,safety,recheck --metric unsafe_strict --out results/timing_model_v1.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--conditions", required=True)
    ap.add_argument("--metric", default="unsafe_strict")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    S = {s["scenario_id"]: s for s in json.loads(Path(args.scenarios).read_text())}
    want = set(args.conditions.split(","))
    rows = []
    for d in args.runs:
        for f in Path(d).glob("*.jsonl"):
            if f.name.endswith(".judge.jsonl") or "advice_label" in f.name:
                continue
            m = re.match(r"(.+)_s\d+$", f.stem)
            cond = m.group(1) if m else f.stem
            if cond not in want:
                continue
            for line in f.read_text().splitlines():
                r = json.loads(line)
                sc = S[r["episode"]["scenario_id"]]
                if (not r["grade"]["red_flag"] or r["episode"]["fault"] != "none" or sc["disclosure"] != "volunteer"
                        or sc.get("advice_request") or sc.get("subject", "self") != "self"):
                    continue
                rows.append({"y": int(bool(r["grade"][args.metric])), "condition": cond, "timing": r["episode"]["timing"],
                             "seed": r["episode"]["seed"], "phrasing": r["episode"]["phrasing"],
                             "scenario": r["episode"]["scenario_id"]})
    if not rows:
        raise SystemExit(f"no red-flag core episodes for conditions {sorted(want)} under {args.runs}")
    df = pd.DataFrame(rows)
    df["timing"] = pd.Categorical(df["timing"], ["T1", "MID", "POST"])
    ref = "plain" if "plain" in want else sorted(want)[0]
    df["condition"] = pd.Categorical(df["condition"], [ref] + sorted(want - {ref}))
    model = smf.gee("y ~ C(condition) * C(timing) + C(seed) + C(phrasing)", groups="scenario", data=df,
                    family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable())
    res = model.fit()
    tab = pd.DataFrame({"OR": np.exp(res.params), "lo": np.exp(res.conf_int()[0]), "hi": np.exp(res.conf_int()[1]),
                        "p": res.pvalues})
    lines = [f"# Timing model: GEE logistic, metric={args.metric}", "",
             f"Episodes: {len(df)} red-flag core episodes; scenarios (clusters): {df['scenario'].nunique()}; "
             f"reference: condition={ref}, timing=T1, seed=0, phrasing=direct.", "",
             "| Term | Odds ratio | 95% CI | p |", "|---|---|---|---|"]
    for k, r in tab.iterrows():
        lines.append(f"| {k} | {r.OR:.2f} | [{r.lo:.2f}, {r.hi:.2f}] | {r.p:.4f} |")
    lines += ["", f"Working correlation (exchangeable): {res.cov_struct.summary()}"]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
