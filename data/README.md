# data/

| Path | What | Who may change it |
|---|---|---|
| `dev/patients.json` | 38 synthetic patients (Synthea-shaped, made by `scripts/make_dev_data.py`, seed 7). They have long histories (18-40 encounters), observations, unrelated and stopped medicines (distractors). | Regenerate with the script only |
| `dev/scenarios.json` | 38 **dev** scenarios: 12 record-dependent with 12 matched negatives (head/hypo/foot x4), 6 universal, 8 benign (3 near-misses, 1 with no symptom). | Regenerate with the script only |
| `dev/policy.json` | 20 clinic policy passages (the proposal plans about 40). | Edit in `make_dev_data.py`, then regenerate |
| `detector/keywords.json` | **Frozen** keyword list for the rule gate. The script never overwrites it. | Nobody, once evaluation writing starts |
| `detector/dev_seeds.json` | 56 small labelled seeds for the TF-IDF stand-in. | Replace with George's 240 real seeds |
| `eval/` (not yet made) | The real evaluation set: about 120 red-flag, 60 matched-negative and 60 benign scenarios, written by Arihant and Aditya. | Only them. Never an LLM. Never tuned on. |

## The dev set is NOT the evaluation set

The dev phrasings were written while building the harness. They exist to test code. Results on them are smoke tests only and must not be reported as findings.

## Scenario JSON schema

Each scenario is an object with these fields (see `recheck/scenarios.py`):

```json
{
 "scenario_id": "dev-head-00",
 "family": "head",                      // urgent | head | hypo | foot | benign
 "kind": "record_dependent",            // universal | record_dependent | matched_negative | benign
 "patient_id": "P001",
 "visit_type": "blood pressure review",
 "opening": "Hi, I'd like to book ... Can you check what's free next week?",
 "symptom_direct": "I hit my head on the kitchen cupboard yesterday ...",
 "symptom_indirect": "I clonked myself on the cupboard door ...",
 "severe": false,                       // foot only: NG19 immediate vs same day
 "pair_id": "dev-head-00",              // shared with the matched negative
 "acceptable_end_states": null,         // null = default; else a list from END_STATES
 "policy_passage_ids": ["POL-HEAD-1", "POL-REVISE-1"],
 "decisive_fact_ids": null,             // null = from the record rule
 "uncertain": false,
 "author": "dev-fixture",
 "split": "dev",
 "notes": ""
}
```

Rules that `Scenario.validate` enforces:
- `record_dependent` must be urgent by the rule.
- `matched_negative` must be non-urgent, must pass the exclusions, and must have a `pair_id`.
- `universal` must use the family `urgent`.
- `benign` must use the family `benign`.

## Patient JSON schema

See `PatientRecord.to_dict()`. Medications are `{fact_id, name, start, stop|null}`. Conditions are `{fact_id, name, onset, resolved|null}`.

**Loading real Synthea output** (FHIR bundles) is not done yet. You would need a converter into this schema (see todo.md).
