# Scripted controllers

Scenarios: `data/eval/scenarios_v1.json`; detector seeds: `data/detector/seeds_v1_decon.json`.

1440 episodes per controller (720 red-flag, 720 routine) from 270 scenarios. Unsafe rates are % of red-flag episodes, averaged within scenario, 95% scenario-bootstrap CI. Completion and over-escalation are % of routine episodes.

| Controller | Policy unsafe [CI] | Strict unsafe [CI] | Lenient | POST policy | Completion | Over-esc | Contrast cons. | Stages (policy) |
|---|---|---|---|---|---|---|---|---|
| book_only | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 | {1: 720} |
| rule_gate |  97.6 [ 95.7,  99.3] |  98.1 [ 96.7,  99.4] | 97.1 | 98.8 | 100.0 | 0.0 | 0.0 | {1: 684, 2: 15, 3: 4} |
| keyword/record/cancel |  95.0 [ 92.1,  97.5] |  95.0 [ 92.1,  97.5] | 95.0 | 95.0 | 100.0 | 0.0 | 0.0 | {1: 684} |
| tfidf/ignore/cancel |  63.5 [ 56.1,  70.8] |  63.5 [ 56.1,  70.8] | 63.5 | 61.7 | 96.0 | 4.0 | 0.0 | {1: 174, 2: 283} |
| tfidf/always/cancel |  17.8 [ 13.5,  22.4] |  17.8 [ 13.5,  22.4] | 17.8 | 12.9 | 49.6 | 50.4 | 0.0 | {1: 128} |
| tfidf/record/none |  37.6 [ 32.6,  42.6] |  48.6 [ 44.7,  52.4] | 23.5 | 62.1 | 96.2 | 4.6 | 56.1 | {1: 169, 3: 102} |
| tfidf/record/cancel |  23.5 [ 18.3,  28.7] |  23.5 [ 18.3,  28.7] | 23.5 | 19.6 | 95.4 | 4.6 | 65.6 | {1: 169} |
| dsc[tfidf] |  23.5 [ 18.3,  28.7] |  23.5 [ 18.3,  28.7] | 23.5 | 19.6 | 95.4 | 4.6 | 65.6 | {1: 169} |
| oracle/ignore/cancel |  50.0 [ 40.8,  59.2] |  50.0 [ 40.8,  59.2] | 50.0 | 50.0 | 100.0 | 0.0 | 0.0 | {2: 360} |
| oracle/always/cancel |   0.0 [  0.0,   0.0] |   0.0 [  0.0,   0.0] | 0.0 | 0.0 | 50.0 | 50.0 | 0.0 | {} |
| oracle/record/none |  19.4 [ 16.7,  22.5] |  33.3 [ 33.3,  33.3] | 0.0 | 58.3 | 100.0 | 0.0 | 85.6 | {3: 140} |
| oracle/record/cancel |   0.0 [  0.0,   0.0] |   0.0 [  0.0,   0.0] | 0.0 | 0.0 | 100.0 | 0.0 | 100.0 | {} |
| oracle/record/convert |   0.0 [  0.0,   0.0] |   0.0 [  0.0,   0.0] | 0.0 | 0.0 | 100.0 | 0.0 | 100.0 | {} |

Tool-fault episodes (red-flag scenarios only, direct phrasing):

| Controller | Fault | Policy unsafe | Strict unsafe | Stages |
|---|---|---|---|---|
| oracle/record/cancel (no rb) | cancel_fails_once | 58.3 | 100.0 | {4: 70} |
| oracle/record/cancel (no rb) | book_lost_response | 19.4 | 33.3 | {3: 70} |
| oracle/record/cancel (no rb) | slot_taken | 0.0 | 0.0 | {} |
| dsc[oracle/no-rb] | cancel_fails_once | 0.0 | 0.0 | {} |
| dsc[oracle/no-rb] | book_lost_response | 19.4 | 33.3 | {3: 70} |
| dsc[oracle/no-rb] | slot_taken | 0.0 | 0.0 | {} |
| dsc[oracle] | cancel_fails_once | 0.0 | 0.0 | {} |
| dsc[oracle] | book_lost_response | 0.0 | 0.0 | {} |
| dsc[oracle] | slot_taken | 0.0 | 0.0 | {} |

Extra episode types (follow-up-only `-ask`, advice request `-adv`):

| Controller | Type | n episodes | Policy unsafe | Not elicited |
|---|---|---|---|---|
| dsc[tfidf] | ask | 12 | 100.0 | 12 |
| dsc[tfidf] | adv | 54 | 8.3 | 0 |
| oracle/record/cancel | ask | 12 | 100.0 | 12 |
| oracle/record/cancel | adv | 54 | 0.0 | 0 |
