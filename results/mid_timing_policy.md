# Timing model: GEE logistic, metric=unsafe_policy

Episodes: 7481 red-flag core episodes; scenarios (clusters): 104; reference: condition=plain, timing=T1, seed=0, phrasing=direct.

| Term | Odds ratio | 95% CI | p |
|---|---|---|---|
| Intercept | 13.31 | [7.48, 23.67] | 0.0000 |
| C(condition)[T.hybrid] | 0.20 | [0.10, 0.39] | 0.0000 |
| C(condition)[T.plain_label] | 1.94 | [0.92, 4.09] | 0.0797 |
| C(condition)[T.recheck] | 0.42 | [0.21, 0.82] | 0.0112 |
| C(timing)[T.MID] | 0.18 | [0.10, 0.32] | 0.0000 |
| C(timing)[T.POST] | 3.56 | [1.29, 9.85] | 0.0145 |
| C(seed)[T.1] | 1.01 | [0.90, 1.14] | 0.8478 |
| C(seed)[T.2] | 0.96 | [0.86, 1.08] | 0.5195 |
| C(phrasing)[T.indirect] | 1.89 | [1.61, 2.23] | 0.0000 |
| C(condition)[T.hybrid]:C(timing)[T.MID] | 2.28 | [1.22, 4.29] | 0.0103 |
| C(condition)[T.plain_label]:C(timing)[T.MID] | 0.37 | [0.15, 0.90] | 0.0294 |
| C(condition)[T.recheck]:C(timing)[T.MID] | 1.07 | [0.54, 2.10] | 0.8486 |
| C(condition)[T.hybrid]:C(timing)[T.POST] | 0.19 | [0.06, 0.58] | 0.0036 |
| C(condition)[T.plain_label]:C(timing)[T.POST] | 1.30 | [0.31, 5.39] | 0.7180 |
| C(condition)[T.recheck]:C(timing)[T.POST] | 0.11 | [0.04, 0.31] | 0.0001 |

Working correlation (exchangeable): The correlation between two observations in the same cluster is 0.058
