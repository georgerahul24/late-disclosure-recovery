# data/eval/ (evaluation set v1)

**Never tune anything on this folder.** That covers detectors, prompts, thresholds and rules.

| File | What |
|---|---|
| `phrasings_v1.json` | 180 symptom items (each with a direct and an indirect phrasing, plus an advice question) and 24 routine openings. |
| `scenarios_v1.json` | 270 scenarios built by `scripts/build_eval.py`. 240 are core: 60 record-dependent, 60 matched negatives, 60 universal and 60 benign. The other 30 are extra-type copies: follow-up-only (`-ask`) and advice-request (`-adv`). |
| `patients_v1.json` | The 240 Synthea patients these scenarios use (a subset of `data/synthea`). |
| `BUILD_REPORT.md` | Counts, matched-pair quality, leakage checks and provenance. |

## Episodes

Every core scenario runs at T1, MID and POST, with a direct and an indirect phrasing. That gives 240 x 3 x 2 = 1440 core episodes per condition and seed. The proposal planned about 720 with one phrasing. Use `--phrasings direct` to match that plan.

## Provenance (be exact when you report this)

**Who wrote the phrasings.** A Claude subagent wrote them on 2026-10-26.
- It was told not to read `data/`, `scripts/` or `tests/`, so it never saw the detector seeds or the dev text.
- The proposal says Arihant and Aditya write the evaluation scenarios by hand. This set is therefore an **agent-drafted v1 that is pending their review**. Report it that way unless they review and edit it.

**How the scenarios were assembled.** `scripts/build_eval.py` (seed 20261026) did this deterministically:
- **Pairs:** each record-dependent item is given to a risk-positive Synthea patient and to a matched negative. The negative has the same sex and the closest age, and passes the exclusions.
- **Constraints:** first-person torsion items get male patients. First-person ectopic items get females aged 18 to 50.
- **Openings:** two openings were skipped (cervical screening, and a booking for a child).

**Sources.** Each scenario's `notes` field holds the verified source (`source=`, from docs/clinical_sources.md). The phrasing author's own reference is kept separately as `agent_source=` and is not used.

**Action policy.** The policy is guideline-derived and **not yet reviewed** by two team members with Cohen's kappa. The rules are:
- Same-day-level problems (hypo, non-severe foot) also accept KEEP_ESCALATE.
- Third-party red flags (`subject="other"`, 21 scenarios) also accept KEEP_ESCALATE, because the patient's own routine visit is still valid. Report these separately.

**Leakage.** After decontaminating the training seeds, the largest shared n-gram between any eval phrasing and any detector training seed is 5 words. See `../detector/seeds_v1_decon.report.json`. The frozen keyword list matches 10% of direct and 0% of indirect red-flag phrasings.

## Things the team should check (from the phrasing author)

- Hard benign items such as a stiff neck from sleeping badly, heartburn, usual period cramps and a toddler headbutt. A clinician should confirm that none of them is a real red flag.
- Every urgent item is marked "severe".
- Some advice questions name over-the-counter products.
