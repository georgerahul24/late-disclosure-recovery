# Hand-label results

Made by `scripts/score_labels.py` from `labelling/`.

## 1. Action policy (two labellers, blind to the benchmark labels)

Scenarios labelled by both: 270 of 270

- Red flag, A vs B: agreement 0.98, Cohen's kappa 0.96
- Red flag, A vs benchmark: agreement 0.93, kappa 0.86
- Red flag, B vs benchmark: agreement 0.95, kappa 0.90

| End state acceptable | kappa A vs B | A vs benchmark | B vs benchmark |
|---|---|---|---|
| CANCEL_ESCALATE | 0.96 | 0.86 | 0.90 |
| CONVERT_URGENT | 0.50 | 0.86 | 0.38 |
| KEEP_ESCALATE | 0.97 | 0.32 | 0.33 |
| HANDOVER | 0.96 | 0.86 | 0.90 |
| ROUTINE_BOOKED | 0.96 | 0.86 | 0.90 |
| NO_ACTION | 0.97 | 0.00 | 0.00 |

Scenarios where a labeller disagrees with the benchmark on red flag: ev-foot-04-neg, ev-foot-05-neg, ev-foot-08-neg, ev-foot-09-neg, ev-foot-12-neg, ev-foot-14-neg, ev-foot-15-neg, ev-foot-16-neg, ev-foot-17-neg, ev-foot-18-neg, ev-foot-19-neg, ev-foot-20-neg, ev-hypo-02-neg, ev-hypo-03-neg, ev-hypo-06-neg, ev-hypo-07-neg, ev-hypo-08-neg, ev-hypo-15-neg, ev-hypo-18-neg

## 2. Stage check (human vs automatic first-failed stage)

Episodes labelled: 50
- Agreement 0.54, Cohen's kappa 0.42
- Confusions (human, auto): {('2', '4'): 7, ('2', '5'): 3, ('2', '1'): 3, ('1', '4'): 1, ('4', '3'): 3, ('3', '1'): 2, ('3', '5'): 3, ('2', '3'): 1}

## 3. Advice judge vs human

Replies labelled: 60
- Human advice = yes: 18; no: 42
- In the sample: PPV 0.60, NPV 1.00, kappa 0.60
- Reweighted to all judged turns (judge flags 18.53%): sensitivity 1.00, specificity 0.92, estimated human advice rate 11.12%

## Eval text review

Reviewed 270 of 270; marked not OK: 3
IDs: ev-benign-40, ev-urgent-10, ev-urgent-10-ask

## Detector seeds review

Reviewed 229 of 229; marked not OK: 5
IDs: hypo-019, foot-017, foot-025, foot-030, foot-033
