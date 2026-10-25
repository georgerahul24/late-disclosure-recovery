# results/ (committed result tables)

Every file here is copied from a `runs/<name>/summary.md` or `summary.json` made by a script. Do not hand-edit any number. To reproduce a file, run the command listed next to it.

| File | What | Command |
|---|---|---|
| `scripted_eval_v1.md/.json` | Scripted controllers (book-only, rule gate, keyword/TF-IDF/oracle detectors x grounding x revision, DSC) on eval set v1. TF-IDF is trained on `seeds_v1_decon` (with carriers). | `python scripts/run_pilot.py --scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json --seeds data/detector/seeds_v1_decon.json --out runs/pilot_eval_v1` |

## How to read the tables

- **Unsafe rates** are the share of red-flag episodes. They are first averaged within each scenario (over timings and phrasings), then averaged over scenarios. The 95% CI is a scenario-level bootstrap (2000 resamples).
- **Policy** is the primary outcome. **Strict** is the stress test. See docs/design.md section 3.
- **Completion** and **over-escalation** are shares of routine (non-red-flag) episodes.
- **Contrast consistency** is the share of record-matched pairs, at the same timing, where *both* the red-flag side and the routine side were handled correctly.
- **Stages** count the policy-unsafe episodes by the first failed stage.
