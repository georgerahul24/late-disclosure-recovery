# TODO

The live task list. Read `handoff.md` first for context, and `instructions.md` for the standing rules (commit per feature, push every commit, no fake data, cluster how-to).

Status tags:
- `[ ]` open
- `[~]` in progress
- `[x]` done
- `[!]` blocked or needs a human

Owners:
- **G** = George
- **A** = Arihant
- **P** = Aditya
- **agent** = any coding agent

## Phase 0. Project setup
- [x] Private GitHub repo, folder READMEs, handoff, todo, instructions (agent)
- [x] Literature review `papers.md` (3 parallel searches, about 85 items) (agent)
- [x] Cluster access, node holder job, Ollama per GPU (agent). See instructions.md.

## Phase 1. Benchmark harness (code)
- [x] Mock backend with fault injection (`recheck/backend.py`)
- [x] Tool harness: allow-list, authority, ledger, call log (`recheck/tools.py`)
- [x] Rule-based, event-triggered patient simulator (`recheck/simulator.py`)
- [x] Grader: policy (primary), strict, lenient; stages 1-5; unsafe actions (`recheck/grader.py`)
- [x] Scenario-clustered bootstrap analysis plus contrast consistency (`recheck/analysis.py`)
- [x] Scripted pilot controllers plus DSC; pilot runner with sanity checks
- [x] Tests (29 passing)
- [x] **Follow-up-only red flags**: the symptom is revealed only when the agent asks "anything else?". The proposal lists this as an extra episode type. Add a simulator mode and a scenario flag.
- [x] **Medical-advice-request episodes**: the patient asks "should I take paracetamol?". The agent must route to a clinician. Needs a scenario flag and simulator line.
- [~] Replace the regex advice check with the **LLM judge** (`recheck/judge.py`, `scripts/judge_runs.py`; judge model llama3.1:8b, a different family from the agent). Still needed: Use a different model family from the agent (papers.md section 7, DeLucia 2026). Validate on about 60 human labels and report per-class sensitivity and specificity. [!] The human labels need G/A/P.
- [ ] **Tool-call accuracy metrics**: a reference list of required and forbidden state-changing calls per episode; precision and recall; argument accuracy; schema-valid call rate; recovery rate after injected errors (proposal section 7).
- [x] Schema-valid tool-call rate and false-claim count in LLM summaries (smoke: 100% valid, so no 14B fallback).
- [ ] **pass^k across seeds** (papers.md: tau-bench).
- [ ] Surface perturbations (typos, tone, family downplaying the symptom) as robustness variants (papers.md 4: Gourabathina 2025).
- [ ] A "status-correct use" retrieval metric: did the agent treat a stopped medicine as stopped?
- [ ] Decisive-fact recall@k and citation support (proposal Table 1).
- [x] Model-based timing analysis: a GEE logistic model in place of the GLMM (docs/design.md section 11). Original task: mixed-effects logistic model (`unsafe ~ condition * timing + seed + (1|scenario) + (1|patient)`), Holm correction over the 5 confirmatory comparisons, TOST at ±10 points. Needs statsmodels.

## Phase 2. Real data (no dummy data in any reported result)
- [x] Generate a Synthea population on the cluster: pinned v3.3.0, seed 20261026, 6000 people, Massachusetts (`cluster/run_synthea.sh`). Provenance goes in `data/synthea/PROVENANCE.txt`.
- [x] Convert it to records and pools (`scripts/synthea_to_records.py`). Commit `data/synthea/patients.json`, `pools.json` and `conversion_report.md`. Check that the drug descriptions in the report are classed correctly.
- [x] Clinical sources for every rule and red flag, verified (`docs/clinical_sources.md`, made by a research agent). Update `rules.py` and the policy passages if anything disagrees.
- [x] Detector training seeds v1: 240 seeds written blind to the eval set (`data/detector/seeds_v1.json`, made by a separate agent).
- [x] **Evaluation scenarios v1** (`data/eval/`): about 120 red-flag (60 universal + 60 record-dependent), 60 matched negatives and 60 benign including near-misses, each with direct and indirect phrasing, built on real Synthea patients from the pools. Matched pairs share the same words and are matched on sex and age band.
  - [!] The proposal says A and P write these by hand. If an agent drafts them, mark `author` honestly (for example "claude-drafted") and get A/P to review and edit before they are final. Never claim human authorship for agent-written text.
- [ ] Clinical action policy per scenario. The proposal wants a clinician or two members with Cohen's kappa. [!] Needs G/A/P. Agent defaults are guideline-derived and recorded per scenario.
- [x] Clinic policy document: expand from 20 to about 40 passages, each tied to a source in `docs/clinical_sources.md`.

## Phase 2b. Done since the first handoff (2026-10-26)
- [x] Simulator answers medication questions with the patient's active medicines (docs/design.md section 2).
- [x] Slots carry the weekday (the model invented wrong weekdays).
- [x] Decontamination: 11 seeds dropped for sharing 6+ words with eval text (`scripts/decontaminate.py`). Run it on the paraphrases too, giving `paraphrases_v1_decon.json`.
- [x] Scripted controllers on eval v1: `results/scripted_eval_v1.md`.
- [ ] Re-run `scripts/build_eval.py` if the rules or pools change, and re-check BUILD_REPORT.

## Phase 3. Detector
- [x] LLM paraphrases: 763 kept of ~916 asked (93 dropped by the label check), 756 after decontamination. A spot-check shows some drift (extra symptoms added, e.g. 'headache ever since' on a head bump), so the human check matters. Original task: 4 per seed with the orchestrator model (allowed for training only), automatic label check, ~3,600 examples with carriers. Second-member check: [!] A/P.
- [ ] LoRA training: Qwen2.5-1.5B-Instruct and Qwen2.5-0.5B, 5-way head, r=16, alpha=32, dropout 0.05, attention projections, lr 2e-4, 3 epochs, batch 16, 3 seeds, fp16 (the 2080 Ti has no bf16). Split 85/15 grouped by seed. Training venv goes on node scratch (home is full).
- [x] `recheck/detectors/lora.py` with `LoraDetector(adapter_dir).predict`.
- [ ] Detector comparison: keyword vs TF-IDF vs prompted large model vs both LoRA models, on symptom-only, in-message and reworded text. Report max n-gram overlap between train and test.

## Phase 4. Main runs (proposal sections 6, 9, 10)
**Running on holder 39713 (gnode089):**
- Plain and Safety, 3 seeds, both phrasings, go to `runs/llm_main` (started 2026-10-26 04:15 IST, about 10 h).
- The LoRA detectors are training on GPU 3 (`logs/train.out`).
- `cluster/queue_main.sh` starts by itself when training ends, and runs:
  1. the detector comparison,
  2. the scripted baselines with the LoRA detector,
  3. plain_label, recheck and hybrid (3 seeds),
  4. the 7 ablations (seed 0, direct phrasing),
  5. the faults.
- Check progress with `cat logs/queue.log` and `ls logs/queue/*.done`.
- After the queue ends: **first re-run each `run_llm.py` command with the same `--out` (resume pass)** so that episodes dropped by crashes are filled in. Check that every `<cond>_s<seed>.jsonl` has all its episodes. Then unload qwen, run `scripts/judge_runs.py` with llama3.1:8b, then `cluster/sync.sh pull`, `scripts/summarize_runs.py`, `scripts/timing_model.py` and `scripts/make_tables.py`.
- [x] Smoke test LLM conditions on gnode089 (holder job). Check the valid tool-call rate. If it is under 90%, use the fallback: 14B model (proposal Table 4).
- [ ] 5 main conditions x 3 seeds: plain, safety, plain_label, recheck, hybrid.
- [ ] Rule gate (scripted) and DSC on the same eval set.
- [ ] 7 ablations x 1 seed.
- [ ] Tool-fault episodes: cancel_fails_once, book_lost_response, slot_taken.
- [ ] H1: POST minus T1 difference for plain and safety. H2/H2b/H2c with scenario-paired bootstrap. TOST recheck vs DSC.
- [ ] Failure analysis: sample 30 failed episodes per main condition, assign stage plus sub-cause, two annotated traces per stage.
- [ ] Stage 1/2 note check against 50 hand-labelled traces. [!] Needs a human labeller.

## Phase 5. Paper
- [ ] Update the proposal claims as the reviewer pointers ask: policy grading primary, strict as a stress test; lead with the benchmark; no "first" (papers.md section 1 has the safe sentence).
- [ ] Related work rewrite with the new closest work (papers.md section 10, items 1-3).
- [ ] Write `paper/` (LaTeX) with results tables generated from `runs/` summaries (no hand-typed numbers).
- [ ] Limitations: Synthea realism (Chen 2019), agent-drafted scenarios (if not replaced), q8 quantised model instead of bf16, single model family, rule-based simulator.
- [ ] Fix the citation errors listed in papers.md section 9.
