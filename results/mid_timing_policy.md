# Timing model: GEE logistic, metric=unsafe_policy

Episodes: 3737 red-flag core episodes; scenarios (clusters): 104; reference: condition=plain, timing=T1, seed=0, phrasing=direct.

| Term | Odds ratio | 95% CI | p |
|---|---|---|---|
| Intercept | 13.72 | [7.12, 26.42] | 0.0000 |
| C(condition)[T.plain_label] | 2.02 | [0.88, 4.63] | 0.0972 |
| C(timing)[T.MID] | 0.17 | [0.09, 0.32] | 0.0000 |
| C(timing)[T.POST] | 3.86 | [1.20, 12.42] | 0.0233 |
| C(seed)[T.1] | 0.90 | [0.77, 1.06] | 0.2181 |
| C(seed)[T.2] | 0.96 | [0.81, 1.14] | 0.6559 |
| C(phrasing)[T.indirect] | 2.63 | [1.92, 3.60] | 0.0000 |
| C(condition)[T.plain_label]:C(timing)[T.MID] | 0.35 | [0.13, 0.95] | 0.0383 |
| C(condition)[T.plain_label]:C(timing)[T.POST] | 1.39 | [0.24, 8.03] | 0.7156 |

Working correlation (exchangeable): The correlation between two observations in the same cluster is 0.108
