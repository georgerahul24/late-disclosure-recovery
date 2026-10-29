# results/ (committed result tables)

Every file here is copied from a `runs/<name>/summary.md` or `summary.json` made by a script. Do not hand-edit any number. To reproduce a file, run the command listed next to it.

| File | What | Command |
|---|---|---|
| `final_v1.md/.json` | **Final results for all runs** (29 Oct 2026): core table, H1, H2/H2b/H2c/Hybrid-DSC with Holm, exploratory ablations, TOST, pass^k, family-member flags, extra episode types, tool faults. Paired tests use only the (seed, phrasing) cells both conditions ran. | `python scripts/summarize_runs.py --runs runs/llm_main runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults --out results/final_v1.md` |
| `final_timing_policy.md` | GEE logistic timing model, policy-unsafe, Plain / Plain + Label / Safety / RECHECK / Hybrid (9,360 red-flag core episodes, 104 scenario clusters). | `python scripts/timing_model.py --runs runs/llm_main --scenarios data/eval/scenarios_v1.json --conditions plain,plain_label,safety,recheck,hybrid --metric unsafe_policy --out results/final_timing_policy.md` |
| `runs_v1/*.tar.gz` | **The raw episode files** behind every number (one JSON line per episode: transcript, tool calls, ledger, final backend state, grade). `SHA256SUMS` checks them. Unpack with `mkdir -p runs && for f in results/runs_v1/*.tar.gz; do tar xzf $f -C runs; done`. | made with `tar czf` from `runs/` |
| `mid_v1.md/.json`, `mid_timing_policy.md` | Older mid-point snapshot (28 Oct, before Safety, ablations and LLM faults finished). Superseded by `final_v1`. | as above |
| `detectors_eval_v1.md/.json` | Detector comparison on eval text. | `scripts/eval_detectors.py` (see `cluster/queue_main.sh`, step `detectors`) |
| `lora_dev/` | LoRA detector training metrics (dev split). | `scripts/train_detector.py` |
| `scripted_eval_v1.md/.json` | Scripted controllers (book-only, rule gate, keyword/TF-IDF/oracle detectors x grounding x revision, DSC) on eval set v1. TF-IDF is trained on `seeds_v1_decon` (with carriers). | `python scripts/run_pilot.py --scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json --seeds data/detector/seeds_v1_decon.json --out runs/pilot_eval_v1` |

## How to read the tables

- **Unsafe rates** are the share of red-flag episodes. They are first averaged within each scenario (over timings and phrasings), then averaged over scenarios. The 95% CI is a scenario-level bootstrap (10,000 resamples in `final_v1`; the older `scripted_eval_v1` used 2,000).
- **Policy** is the primary outcome. **Strict** is the stress test. See docs/design.md section 3.
- **Completion** and **over-escalation** are shares of routine (non-red-flag) episodes.
- **Contrast consistency** is the share of record-matched pairs, at the same timing, where *both* the red-flag side and the routine side were handled correctly.
- **Stages** count the policy-unsafe episodes by the first failed stage.
