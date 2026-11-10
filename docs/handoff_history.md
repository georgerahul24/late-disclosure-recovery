# Handoff

Last updated: 2026-10-29. Update this file whenever the state changes.

## 1. What this project is

A course research project (LMA) by George R., Arihant R. and Aditya P. It has two parts:
- **The benchmark.** Can a clinic booking agent notice that a symptom disclosed late makes its *own earlier booking* unsafe, then repair it, escalate, and confirm the fix? Grading uses the final backend state.
- **RECHECK.** A detector plus a frozen LLM with record retrieval, an action ledger re-check, repair and read-back.

The plan is in `docs/proposal.pdf`. The review feedback is in `docs/pointers.txt`. Related work is in `papers.md`. Clinical grounding is in `docs/clinical_sources.md`.

## 2. Read in this order

1. `instructions.md`: George's standing rules. Commit per feature, push every commit, **no fake or dummy data in any result**, back every claim with literature. It also has the cluster how-to.
2. `todo.md`: what is done and what is next.
3. `docs/design.md`: how the proposal maps to code, and every decision we made.
4. The `README.md` in each folder you touch.

## 3. Current state

**Code (35 tests pass):**
- **Episode loop:** backend with faults (cancel fails, slot taken, lost booking response), tool harness (allow-list, authority, ledger), simulator, runner, grader and analysis.
- **Simulator:** event-triggered. It supports follow-up-only disclosure and advice requests, and it answers medication questions from the record.
- **Grader:** policy (primary), strict, lenient, stages 1-5, unsafe actions, false claims and schema-valid call rate.
- **Agents:** scripted controllers plus the DSC, and LLM agents for 12 conditions.
- **Advice judge:** an LLM judge (UNVALIDATED until human labels exist).
- **Detectors:** keyword, TF-IDF, oracle and LoRA (`recheck/detectors/lora.py`).

**Data (all real or verified, with provenance):**
- **Synthea population:** v3.3.0, seed 20261026, 6000 alive people. See `data/synthea/PROVENANCE.txt`, `pools.json` and `conversion_report.md`. The full `patients.json` (51 MB) is git-ignored; rebuild it with the commands in `data/synthea/README.md`.
- **Clinical sources:** `docs/clinical_sources.md`, verified by a research agent. The rules in `recheck/rules.py` follow it (table D).
- **Clinic policy v1:** `data/policy/clinic_policy_v1.json`, 40 passages, each with a source.
- **Detector seeds:** `data/detector/seeds_v1.json`, 240 seeds written by an agent blind to the eval set. `seeds_v1_decon.json` has 229 after dropping those that shared 6+ words with eval text.
- **Eval set v1:** `data/eval/`, 270 scenarios on 240 Synthea patients. The phrasings were **agent-written, blind to the seeds, and are pending team review**. See `data/eval/README.md` and `BUILD_REPORT.md`.
- `data/dev/` is for unit tests only.

**Results so far:**
- `results/scripted_eval_v1.md`: scripted controllers on eval v1.
  - The rule gate is 97.6% unsafe.
  - The DSC with TF-IDF is 23.5% unsafe at 95.4% completion. All of its failures are detection misses.
  - The oracle with no revision is 33.3% strict-unsafe, all of it stale POST bookings.
- **LLM smoke test (24 episodes, not a result):**
  - The pipeline works and 100% of tool calls are schema-valid.
  - The model sometimes claims to have booked without calling `book`.
  - RECHECK often searches conditions instead of medications (a stage 2 failure).

**SECOND-MODEL RUN STARTED (2026-11-02 03:01 IST, no laptop needed).** Llama 3.1 8B Instruct q8_0 as the agent, same prompts/tools/eval set/LoRA detector, nothing tuned for it; seed 0, both phrasings; plain, safety, plain_label (job 52643, gnode082) and recheck, recheck_v2 (job 52644, gnode056), 2 GPUs each, `OLLAMA_NUM_PARALLEL=1` (llama's KV cache does not fit 2 slots on 11 GB). `cluster/queue_llama.sh` on the login node (`logs/queue_llama.log`), output `runs/llm_llama`, analysis `runs/llama_analysis/`, end marker `logs/queue/llama.done`; it cancels both jobs when done. ETA about 11:00-12:00 IST on 2 Nov. Exploratory generality check: do not pool with the qwen runs.
- Traps: gnode077/069/090 were idle because CUDA fails there (cuInit 999); gnode079 scratch is full; gnode056 first had a half-unpacked Ollama (GPU libs missing, ran on CPU); the CUDA torch wheel timed out, so the detector env on these nodes uses torch 2.4.1+cpu (the detector ran on CPU in all runs anyway).

**ALL CLUSTER WORK FINISHED (final stage done 2026-10-30 15:43 IST; pulled and checked 2026-11-02).** No jobs are running; the judge job 46988 was cancelled after it sat idle.
- RECHECK v2 (3 seeds, 4,716 episodes): policy unsafe 67.0 vs RECHECK 73.7 (-6.7 [-9.2, -4.3]); completion 73.6 (+7.2 vs RECHECK, -24.3 vs Plain, so it also fails the 10-point rule); false-claim episodes 255 vs 890. Exploratory. In `results/final_v1.md` and report Section "RECHECK v2".
- Advice judge ran on every LLM run (`results/advice_v1.md`). UNVALIDATED: 60-turn sheet `labelling/advice_labels.csv` must be labelled and scored first.
- Checks: all 56,466 episodes re-grade to their stored grade; every cluster analysis file re-made on the laptop byte for byte; context.zip `verify/reproduce.sh` passes from the archives alone; 37/37 tests.
- Raw files: `results/runs_v1/llm_v2.tar.gz` and `advice_judge.tar.gz` added; the first 6 archives are unchanged.
- Only human work is left: the `labelling/` sheets, then `scripts/score_labels.py`, then the paper.

**Earlier: final stage as it was launched (2026-10-29 22:06 IST).** `cluster/queue_final.sh 41206 46988` runs on the ada login node (`logs/queue_final*.log`, step markers in `logs/queue/`):
- holder 41206 (gnode062, 2 GPUs, qwen): RECHECK v2 on eval v1, 3 seeds, both phrasings -> `runs/llm_v2` (ETA about 07:15 IST on 30 Oct); then its GPUs become llama judge servers and judge `llm_faults`, `llm_v2`, `llm_ablate`.
- judge job 46988 (gnode082, 2 GPUs, llama3.1:8b q8_0, ctx 1536, 6 parallel): judges `llm_main` (ETA about 06:40 IST on 30 Oct) and exports the 60-turn advice label sample.
- then all analysis goes into `runs/final_analysis/` (regrade check, summary with v2, GEE, extra facts, failure breakdown, advice summary + `labelling/advice_labels.csv`, report tables). Expected done around 16:00-17:00 IST on 30 Oct. `logs/queue/final.done` marks the end.
- After it ends: `cluster/sync.sh pull`, copy `runs/final_analysis/*` into `results/` and `ai report/tables/`, `runs/final_analysis/labelling/advice_labels*` into `labelling/`, update the report and `context.zip`, commit.
- RECHECK v2 dev check (`runs/v2_dev`, dev fixtures only, seed 0): policy unsafe 71.3 vs RECHECK 78.7, completion 76.7 vs 69.2. The method was fixed before this run and not tuned on eval.
- Traps found today: `/tmp` full on gnode082 made Ollama silently use CPU (fixed: TMPDIR on scratch); a llama judge needs ctx 1536 x 6 parallel to fit fully on one 2080 Ti; JSON mode stops trailing explanations; the cluster `.venv` needed statsmodels.

**ALL MAIN RUNS FINISHED (2026-10-29 03:27 IST).** 51,750 graded episodes. Final numbers are in `results/final_v1.md` and `results/final_timing_policy.md`; raw episodes are in `results/runs_v1/*.tar.gz`. The mid-submission report (`ai report/report.pdf`) uses all of them and is tagged `midsem` in git. Left: the advice judge, RECHECK v2, the human labelling items, and the paper.

**Older queue status (2026-10-26 05:06 IST).**
- The LoRA detectors are trained. There are 6 in `models/det-*` (git-ignored), and their metrics are in `runs/detector/*.metrics.json`. Dev macro-F1 is 0.975-0.990 for 1.5B and 0.957-0.978 for 0.5B.
- `cluster/queue_main.sh` was restarted after a LoRA OOM fix. It is now on the detector comparison step. Progress is in `logs/queue.log`, and finished steps leave `logs/queue/*.done` markers. Re-running the queue is safe.
- Plain and Safety (`runs/llm_main`) run separately, as step 39713.33.

**Earlier notes (some steps above are now done):**
- Seed paraphrasing on the cluster: `data/detector/paraphrases_v1.json`, made on the cluster and pulled back with `cluster/sync.sh pull`.
- **Next steps:**
  1. Decontaminate the paraphrases.
  2. Free GPU 3 and train the LoRA detectors (`cluster/train_detectors.sh`).
  3. Run `plain` and `safety` (they need no detector) on the other 3 servers.
  4. Then run `plain_label`, `recheck`, `hybrid` and the ablations with the best LoRA detector.

## 4. Cluster state (check before you start)

**UPDATE 2026-10-27.**
- Holder 39713 (gnode089) was **cancelled on 2026-10-26 at 14:50** (SLURM state CANCELLED). Everything running in it stopped, and the queue then "finished" because every step failed at once. The queue now stops by itself if its holder disappears.
- The new holder is **job 41206 on gnode062**, with 2 GPUs (2 Ollama servers), 24 CPUs and 96 GB. It has only 2 GPUs because George's `kings_server` (job 40463) uses the other 2 of the 4-GPU QoS.
- The LoRA detector now runs on CPU (`DET_GPU` empty in `cluster/queue_main.sh`). The torch env was rebuilt on gnode062 (`logs/train_env_062.out`).
- **Done before the cancel:** the detector comparison, the scripted baselines and DSC faults, Plain (3 seeds) and Plain + Label (3 seeds, a few episodes missing).
- **Left:** RECHECK, Hybrid, Safety, the ablations and the faults. After those, the judge and the analysis.

**Older notes:**

- **Holder job 39713** runs on **gnode089**: 4x RTX 2080 Ti, 36 CPUs, 100 GB RAM. It started 2026-10-26 about 03:40 IST and has a 4-day limit, so it ends around 2026-10-30.
  - It runs 4 Ollama servers (ports 11434-11437) with `qwen2.5:7b-instruct-q8_0` loaded. Details are in `~/lma/logs/hold-39713.env`.
  - A watchdog restarts any server that dies.
- **How to run things inside it:**
  - LLM scripts: `cluster/run_in_hold.sh 39713 <script> <args>`. It adds `--base-urls`, `--model` and `--workers` for you.
  - Anything else: `srun --jobid=39713 --overlap -n 1 -c <k> --mem=<m> --gres=none <cmd>`. **Always pass `-n 1`.** Use `--gres=gpu:4` plus `CUDA_VISIBLE_DEVICES=<i>` to use one GPU.
- **Node-local files** (`/ssd_scratch/gr/lma` on gnode089):
  - the Ollama install (from `~/ollama`, v0.21.2) and models
  - JDK 17
  - the Synthea jar and the raw CSVs (`synthea/out-20261026/csv`)
  - the GPU training venv (`venv-train`: torch 2.4.1+cu121, transformers 4.44.2, peft 0.12.0)
  - the HF cache
- **Moving to a new node:** if the holder moves, re-run `cluster/run_synthea.sh` (same seed, same people) and `cluster/setup_train_env.sh`.
- **Code sync:** `cluster/sync.sh push`, then `pull`. Push never deletes the cluster-made `data/synthea/` or `data/detector/paraphrases_*`. **Pull before you commit those.**

## 5. Known issues and traps

- **`sbatch --test-only` gives false start times** here. Submit for real.
- **Big GPU requests can wait.** Requests for 3 or more GPUs on half-used nodes can sit as "reserved"; fully free nodes start at once.
- **Home quota is nearly full.** Big things go on node scratch.
- **`~/ollama` is a zstd tar.** Only compute nodes have `zstd`.
- **Node DNS sometimes times out**, so model pulls retry.
- **Ollama servers sharing one models dir race at startup.** This is fixed in `cluster/ollama_lib.sh`: the dirs are created first and `OLLAMA_NOPRUNE=1` is set.
- **The 2080 Ti has no bf16.** We use the q8_0 Ollama model and fp16 autocast for LoRA. **Report this as a deviation from the proposal.**
- **Read-back result differs from the proposal's pilot.** With the DSC invariant, a failed cancel gets retried. The lost-response fault is the case that shows read-back matters (docs/design.md section 6).
- **Two independent agents converged on common clinical wording.** This is why the decontamination step exists.

## 6. Decisions that need a human (G/A/P)

- **Eval phrasings:** review `data/eval/phrasings_v1.json`. It is agent-written, and the proposal wanted A and P to write it.
- **Action policy:** two-member review with Cohen's kappa.
- **Human labels:**
  - about 60 for the advice judge (`runs/<x>/advice_label_sample.jsonl` is exported for this),
  - 50 traces for the stage 1/2 check,
  - the second-member check of the paraphrases.
- **Detector seeds:** George to review `seeds_v1.json`.

## 7. Repo

https://github.com/georgerahul24/late-disclosure-recovery (private).
