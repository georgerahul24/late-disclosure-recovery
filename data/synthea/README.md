# data/synthea/ (real Synthea patients used in every reported experiment)

These files are made on the cluster and brought back with `cluster/sync.sh pull`. `push` never touches this folder.

| File | What |
|---|---|
| `PROVENANCE.txt` | How the population was made: Synthea v3.3.0 (jar sha256), seed 20261026, clinician seed 20261026, 6000 alive people in Massachusetts (6961 total including deaths), full history, Java 17, generation time and node, and the line count plus sha256 of each raw CSV. |
| `patients.json` | Selected patients converted into our `PatientRecord` schema (`scripts/synthea_to_records.py`). |
| `pools.json` | Patient ids per pool: head_pos/neg, hypo_pos/neg, foot_pos/neg, general. Membership is decided by `recheck/rules.py`, so pools and grading always agree. |
| `conversion_report.md` | Counts per pool, plus every risk-relevant drug description found and the class we gave it. **Check this table** whenever the drug classes change. |

## How to rebuild

```bash
# on the cluster, inside the holder job (raw CSVs are node-local, about 5 GB)
srun --jobid=<hold> --overlap -n 1 -c 12 --mem=40G bash cluster/run_synthea.sh
srun --jobid=<hold> --overlap -n 1 -c 2 --mem=24G .venv/bin/python scripts/synthea_to_records.py \
     --csv /ssd_scratch/gr/lma/synthea/out-20261026/csv --out data/synthea
```

The same release, seed and population size give the same people. The CSV checksums in `PROVENANCE.txt` let you confirm this.

## Conversion choices (size limits, written down so they can be reported)

- **Eligible people:** alive, and aged 18 to 90 on the reference date (2026-11-02).
- **Medications:** all of them. Repeated prescriptions of the same drug are merged into one interval. A drug is *active* if any of its prescriptions has no stop date. Stopped drugs are kept as distractors.
- **Conditions:** all of them, including Synthea's social "findings".
- **Encounters:** the 80 most recent.
- **Observations:** the 120 most recent from the last 5 years.
- **Names:** Synthea adds digits to names; these are removed.

## Known limits

- Synthea records are cleaner and more regular than real records (Chen et al. 2019, BMC Med Inform Decis Mak 19:44; see papers.md section 7). Report this as a limitation.
