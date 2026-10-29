# Timing model: GEE logistic, metric=unsafe_policy

Episodes: 9360 red-flag core episodes; scenarios (clusters): 104; reference: condition=plain, timing=T1, seed=0, phrasing=direct.

| Term | Odds ratio | 95% CI | p |
|---|---|---|---|
| Intercept | 13.16 | [7.35, 23.55] | 0.0000 |
| C(condition)[T.hybrid] | 0.20 | [0.10, 0.39] | 0.0000 |
| C(condition)[T.plain_label] | 1.95 | [0.93, 4.09] | 0.0791 |
| C(condition)[T.recheck] | 0.42 | [0.21, 0.82] | 0.0112 |
| C(condition)[T.safety] | 0.48 | [0.30, 0.77] | 0.0024 |
| C(timing)[T.MID] | 0.18 | [0.10, 0.32] | 0.0000 |
| C(timing)[T.POST] | 3.55 | [1.29, 9.78] | 0.0141 |
| C(seed)[T.1] | 1.03 | [0.93, 1.15] | 0.5263 |
| C(seed)[T.2] | 0.98 | [0.89, 1.08] | 0.7025 |
| C(phrasing)[T.indirect] | 1.88 | [1.61, 2.20] | 0.0000 |
| C(condition)[T.hybrid]:C(timing)[T.MID] | 2.28 | [1.21, 4.29] | 0.0105 |
| C(condition)[T.plain_label]:C(timing)[T.MID] | 0.37 | [0.15, 0.90] | 0.0281 |
| C(condition)[T.recheck]:C(timing)[T.MID] | 1.07 | [0.54, 2.10] | 0.8509 |
| C(condition)[T.safety]:C(timing)[T.MID] | 1.52 | [0.90, 2.58] | 0.1171 |
| C(condition)[T.hybrid]:C(timing)[T.POST] | 0.19 | [0.06, 0.58] | 0.0035 |
| C(condition)[T.plain_label]:C(timing)[T.POST] | 1.30 | [0.31, 5.38] | 0.7175 |
| C(condition)[T.recheck]:C(timing)[T.POST] | 0.11 | [0.04, 0.31] | 0.0000 |
| C(condition)[T.safety]:C(timing)[T.POST] | 0.24 | [0.11, 0.56] | 0.0008 |

Working correlation (exchangeable): The correlation between two observations in the same cluster is 0.081
