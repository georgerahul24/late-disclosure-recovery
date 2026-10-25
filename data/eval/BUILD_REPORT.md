# Evaluation set v1: build report

- Scenarios: 270 (240 core, 30 extra-type copies)
- Distinct patients: 240 (all from the Synthea population, see data/synthea/PROVENANCE.txt)

| kind | core/extra | n |
|---|---|---|
| benign | core | 60 |
| benign | extra | 6 |
| matched_negative | core | 60 |
| record_dependent | core | 60 |
| record_dependent | extra | 16 |
| universal | core | 60 |
| universal | extra | 8 |

## Matched pairs
- Pairs: 60; same sex in 60 pairs
- Mean |age gap|: 2.5 years

## Leakage checks (proposal section 5)
- Max shared n-gram between any eval phrasing and any detector seed: 5 words (distribution: {0: 10, 2: 172, 3: 126, 4: 32, 5: 20})
- Frozen keyword list hits on red-flag items: direct 10%, indirect 0%

## Provenance
- Phrasings: written by a Claude subagent that was told not to read data/, scripts/ or tests/ (so it never saw the detector seeds or the dev text). Pending review by the team.
- Patients, pairing, action policy: this script, seed 20261026.
- Action policy is guideline-derived (see docs/clinical_sources.md) and pending two-member review with Cohen's kappa.
- Third-party red flags (symptom belongs to a family member; KEEP_ESCALATE accepted): 21 scenarios. Report them separately.
- Openings used: 22 (skipped ['op-03', 'op-13']).
