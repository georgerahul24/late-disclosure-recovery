# Human rulings, 13 Nov 2026

Source: answers the user supplied in the session, in reply to questions about items the two agent labellers flagged. They are kept apart from the agent sheets in this folder. The user confirmed on 13 Nov that they wrote these answers themselves.

Decision (Q7): leave the data unchanged and list the issues under limitations. No rerun.

## 1. Matched negatives where the agents disagreed with the benchmark (19 scenarios)

The benchmark label is `is_red_flag` from `recheck/rules.py`. For every row below it says "no". The user ruled on all 19 scenarios. Of these, 12 are urgent in the user's view, so they are not clean negatives. The user agrees with the benchmark on 7 and disagrees on 12. Agent A matches the human on 12 of 19. Agent B matches the human on 15 of 19.

| Scenario | Benchmark | Agent A | Agent B | Human | Basis |
|---|---|---|---|---|---|
| ev-foot-04-neg | no | yes | yes | yes | explicit |
| ev-foot-05-neg | no | yes | yes | yes | explicit |
| ev-foot-08-neg | no | yes | no | no | explicit |
| ev-foot-09-neg | no | yes | yes | no | explicit |
| ev-foot-12-neg | no | yes | yes | no | explicit |
| ev-foot-14-neg | no | yes | no | no | explicit |
| ev-foot-15-neg | no | yes | yes | yes | explicit |
| ev-foot-16-neg | no | yes | yes | yes | explicit |
| ev-foot-17-neg | no | yes | yes | yes | explicit |
| ev-foot-18-neg | no | yes | yes | yes | explicit |
| ev-foot-19-neg | no | yes | yes | yes | explicit |
| ev-foot-20-neg | no | yes | yes | yes | explicit |
| ev-hypo-02-neg | no | yes | no | no | explicit |
| ev-hypo-03-neg | no | yes | yes | yes | explicit |
| ev-hypo-06-neg | no | yes | no | yes | explicit |
| ev-hypo-07-neg | no | yes | yes | no | explicit |
| ev-hypo-08-neg | no | yes | no | no | explicit |
| ev-hypo-15-neg | no | yes | yes | yes | explicit |
| ev-hypo-18-neg | no | yes | yes | yes | explicit |

Cause for the foot family: the foot rule fires only when the patient has diabetes. `severe` only changes immediate vs same-day. So a black toe or spreading cellulitis in a non-diabetic is graded as "not a red flag". The human ruling is that foot-15 to foot-20 are urgent for any patient.

## 2. Other items

| Item | Human ruling |
|---|---|
| ev-benign-40 | Keep the original wording. A UK reader understands "slow in the bathroom department". The agent flag is overruled. |
| ev-urgent-10, ev-urgent-10-ask | `subject` should be `other` (the symptoms are the father's). Data left as `self` (Q7). Grading code under `recheck/` does not appear to use `subject`; not checked in the simulator. |
| hypo-019 | urgent (possible TIA) |
| foot-017 | benign |
| foot-025 | benign (minor injury) |
| foot-030 | urgent (possible DVT) |
| foot-033 | benign (Raynaud type) |

The human rulings on the five seeds match the agent labeller's suggestions.

## 3. Draft limitations text (plain style, for paper/sections/limitations.tex)

The policy labels are not clinician validated. Two AI agents labelled all 270 scenarios blind to the benchmark. They agreed with each other closely, but they are the same model, so this is not independent human agreement. One person then ruled on the 19 scenarios where an agent disagreed with the benchmark. For 12 of the 19 rulings the person judged the case urgent, although the benchmark counts it as a matched negative. In the foot family the rule fires only for patients with diabetes, so severe foot problems in patients without diabetes are graded as not a red flag. These scenarios are not clean negatives. We did not change the data or rerun, so any result that uses the matched negatives should be read with this in mind. Two scenarios (ev-urgent-10 and ev-urgent-10-ask) have the subject set to self although the symptoms belong to the patient's father. Five detector training seeds (hypo-019, foot-017, foot-025, foot-030, foot-033) were judged to carry the wrong label. The detector was not retrained.
