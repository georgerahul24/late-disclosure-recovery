# Handoff (start here)

Last updated: 2026-11-10. **The final submission is due 15 Nov 2026** (moved from 11 Nov).

From now on a new collaborator runs this project, not George. This file is all you need to take over. Read it top to bottom. When you finish a task, update section 5 and the date at the top, then commit and push.

Old notes with the full history of runs and jobs: `docs/handoff_history.md`.

## 1. The project in five lines

- Name: "Late-Disclosure Recovery in Stateful Clinical Agents". By George R., Arihant R. and Aditya P. (course project, LMA).
- The question: a clinic booking agent books a routine visit. Later the patient mentions a red-flag symptom. Does the agent notice that its *own earlier booking* is now unsafe, fix it, escalate, and confirm the fix?
- The benchmark grades the final backend state, not the chat text. Policy grading is primary. Strict and lenient are stress tests.
- Our method is RECHECK: a LoRA detector, record retrieval, a re-check of the action ledger, repair and read-back.
- Repo: https://github.com/georgerahul24/late-disclosure-recovery (private; George must add you as a collaborator).

## 2. Rules you must follow

These come from George. They are not optional.

1. **No fake or dummy data in any result.** Every number must come from a file in `results/` or a script. Never type a number by hand if a script can make it.
2. **Back every claim** with a result file or a citation from `papers.md` or `docs/clinical_sources.md`.
3. **Commit per feature, push after every commit.** No "Co-Authored-By" or other AI trailer in commits.
4. **Plain writing.** Short, simple sentences. No em dashes. No fancy words. No emojis.
5. **Be honest.** If something failed, was not run, or is not validated, say so in the paper.
6. **Never claim human work that an agent did.** The eval phrasings and detector seeds were agent-written. Say so.
7. An agent must never fill the human labelling sheets in `labelling/`.

More rules: `instructions.md`.

## 3. Setup on your laptop

```bash
git clone https://github.com/georgerahul24/late-disclosure-recovery.git
cd late-disclosure-recovery
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e . pytest scikit-learn statsmodels numpy
.venv/bin/python -m pytest -q                       # 37 should pass
mkdir -p runs && for f in results/runs_v1/*.tar.gz; do tar xzf $f -C runs; done   # raw episodes
cd results/runs_v1 && shasum -a 256 -c SHA256SUMS && cd ../..                     # check archives
```
You need a TeX install (`latexmk`) to build the report and paper.

## 4. The cluster (ada), using George's account

You will use George's account `gr`. Everything is already installed there. Ask George to add your SSH public key to `~/.ssh/authorized_keys` on ada. Never share or commit any key or password.

### 4.1 Login and where things are

- Login: `ssh gr@ada-gw1.iiit.ac.in` (or `ada-gw2`). You must be on the campus network or VPN. The old `ada.iiit.ac.in` no longer accepts SSH.
- The remote shell is **zsh**.
- Repo copy on the cluster: `~/lma` (= `/home2/gr/lma`). It is **not** a git repo. Code moves with rsync (4.5).
- Small Python env (no torch): `~/lma/.venv` (Python 3.12). Use it for grading and analysis.
- LoRA detector adapters: `~/lma/models/det-qwen2.5-1.5b-instruct-s{0,1,2}` and `det-qwen2.5-0.5b-s{0,1,2}`. Runs use `lora:models/det-qwen2.5-1.5b-instruct-s{seed}`.
- Ollama bundle (v0.21.2, zstd tar): `~/ollama`. The scripts unpack it on node scratch.
- `uv`: `~/.local/bin/uv`. Set `UV_CACHE_DIR=~/uv_cache`.
- Home is 50 GB and shared with George's other projects (`kings*`, `LMA_A1`, `bot`). **Do not touch anything outside `~/lma`.** Big files go on node scratch.

### 4.2 Limits and nodes

- SLURM: account `research`, partition `u22`, QoS `medium`.
- **Per-user limit: 4 GPUs, 40 CPUs, 125 GB RAM, 4 days per job.** This is shared with George's other jobs, so check `squeue -u gr` first. You cannot use more than 4 GPUs at once, even if many are free.
- Use nodes **gnode045 to gnode090**. Each has 4x RTX 2080 Ti (11 GB, no bf16), 40 CPUs, about 125 GB RAM.
- Find free GPUs: `pestat -p u22 --no-color --gib | grep -E "gnode0(4[5-9]|[5-8][0-9]|90)"`.
- Node scratch `/ssd_scratch/gr/lma` is **local to each node**. On 10 Nov these nodes were ready:

| Node | Ollama models | Torch env (`venv-train`) | Notes |
|---|---|---|---|
| **gnode062** | qwen2.5:7b-instruct-q8_0, llama3.1:8b-instruct-q8_0 | torch 2.4.1+cu121 (GPU) | Best choice. All main Qwen runs ran here. 170 GB free. |
| gnode082 | llama3.1 | torch 2.4.1+cpu | Llama runs ran here. 495 GB free. |
| gnode056 | llama3.1 | torch 2.4.1+cpu | Often busy. |

- **Bad nodes:** gnode077, gnode069 and gnode090 had broken CUDA (cuInit 999). gnode079 scratch was full.
- On a new node, the holder job installs Ollama and pulls the model by itself. Build the torch env with `srun --jobid=<job> --overlap -n 1 -c 8 --mem=16G bash cluster/setup_train_env.sh`. If the CUDA torch download times out, the CPU build is fine: the detector runs on CPU in every run.

### 4.3 How a run works: holder job + steps inside it

We hold GPUs with one long job, then run experiments inside it.

1. **Start a holder** (from `~/lma`). It starts one Ollama server per GPU, pulls the model, and writes `logs/hold-<jobid>.env` with the server URLs.
   ```bash
   cd ~/lma
   # Qwen agent (main model), 2 GPUs:
   sbatch -w gnode062 --gres=gpu:2 -c 12 --mem=30G cluster/hold_node.sbatch
   # Llama agent (needs 1 slot per server at 8k context to fit an 11 GB card):
   sbatch -w gnode062 --gres=gpu:2 -c 12 --mem=30G \
     --export=ALL,MODEL=llama3.1:8b-instruct-q8_0,PARALLEL=1,CTX=8192 cluster/hold_node.sbatch
   squeue -u gr                          # wait for state R
   tail -f logs/lma-hold-<jobid>.out     # wait for "READY"
   ```
   Keep `--mem` at 30G or less if you run two holders; large requests sit in the queue.
2. **Run inside it** with `srun --jobid=<jobid> --overlap -n 1 ...`. **Always pass `-n 1`.** Example (one agent condition, as in `cluster/queue_llama.sh`):
   ```bash
   source logs/hold-<jobid>.env
   srun --jobid=<jobid> --overlap -n 1 -c 6 --mem=12G --gres=none \
     env CUDA_VISIBLE_DEVICES= HF_HOME=/ssd_scratch/gr/lma/hf HF_HUB_OFFLINE=1 \
     /ssd_scratch/gr/lma/venv-train/bin/python scripts/run_llm.py \
       --conditions plain,recheck --seeds 0 --phrasings direct,indirect \
       --detector "lora:models/det-qwen2.5-1.5b-instruct-s{seed}" \
       --scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json \
       --policy data/policy/clinic_policy_v1.json \
       --base-urls "$OLLAMA_URLS" --model "$MODEL" --workers 3 --out runs/<new_dir>
   ```
   `--workers` = number of servers x `PARALLEL`. Conditions without a detector (`plain`, `safety`) can use `~/lma/.venv/bin/python` and no `--detector`. A shortcut that fills URLs and model for you: `cluster/run_in_hold.sh <jobid> scripts/run_llm.py ...`.
3. **Long runs: use a queue script on the login node** so your laptop can be off:
   `nohup bash cluster/queue_model.sh <jobid> <tag> >> logs/queue_<tag>.log 2>&1 &`
   It waits for the holder, runs the 5 conditions, does the analysis and cancels the holder. Each step writes `logs/queue/<step>.done`, so re-running skips finished steps. `run_llm.py` also resumes from the same `--out`.
4. **Speed:** about 1,000 episodes per hour on 4 GPUs. One condition, one seed, both phrasings = 1,572 episodes.
5. **When done:** `scancel <jobid>`. Do not leave idle holders; they block George's 4-GPU limit.

### 4.4 Analysis after a run (cluster or laptop)

```bash
.venv/bin/python scripts/regrade_check.py --runs runs/<dir>      # must say all grades match
.venv/bin/python scripts/summarize_runs.py --runs runs/<dir> --out results/<name>.md
.venv/bin/python scripts/extra_facts.py --runs runs/<dir> --out results/<name>_extra_facts.md
.venv/bin/python scripts/failure_breakdown.py --runs runs/<dir> --out results/<name>_failure_breakdown.md
```
On the cluster, wrap these in `srun --jobid=<jobid> --overlap -n 1 -c 6 --mem=12G --gres=none` (do not run heavy work on the login node).

### 4.5 Moving files

From the laptop repo root:
- `cluster/sync.sh push`: code to `~/lma`. It never deletes the cluster-made `data/synthea/` or paraphrase files.
- `cluster/sync.sh pull`: `runs/` and `logs/` back to the laptop. Pull before you commit cluster-made files.
- New raw runs: `tar czf results/runs_v1/<dir>.tar.gz -C runs <dir>`, then add the hash to `results/runs_v1/SHA256SUMS` and check the old hashes still pass.

### 4.6 Traps we already hit

- **zsh:** `$VAR` does not split into words (use arrays). An empty glob aborts the command.
- **`pkill -f <anything>` over ssh kills your own ssh command** (its text matches). Use `pkill -x ollama`, or find the PID with `pgrep -x bash` and check `/proc/<pid>/cmdline`.
- **A model that does not fully fit on the GPU is 5x slower.** Check `size_vram` equals `size` in `curl -s localhost:11434/api/ps` before a long run.
- **A full `/tmp` makes Ollama silently run on CPU.** The scripts set `TMPDIR` on scratch. Check `ollama ps` shows the model in VRAM (`size_vram` about 9.6 GB for Llama).
- **A half-unpacked Ollama** also falls back to CPU. Fix: delete `/ssd_scratch/gr/lma/ollama` and let the holder unpack again.
- **`sbatch --test-only` gives false start times.** Submit for real.
- **No GitHub from the cluster.** Use `sync.sh`.
- **LaTeX macro names cannot have digits.** `make_report_tables.py` turns `recheck_v2` into `recheckvtwo`.

## 5. State of the work

### 5.1 Done (do not redo)

| Item | Where | Key fact |
|---|---|---|
| Benchmark code | `recheck/`, `scripts/` | 37 tests pass |
| Data | `data/` | Synthea v3.3.0, seed 20261026. 270 eval scenarios on 240 patients |
| Detectors | `results/detectors_eval_v1.md` | LoRA Qwen2.5 1.5B and 0.5B, 3 seeds each |
| Main runs (Qwen2.5 7B q8_0) | `results/final_v1.md`, `results/final_timing_policy.md` | 5 conditions x 3 seeds, 1,572 episodes each |
| Ablations, tool faults, scripted baselines | same files | 7 ablations, 3 fault types |
| RECHECK v2 (exploratory) | `results/final_v1.md` | Policy unsafe 67.0 vs RECHECK 73.7. Completion 73.6, so it also fails the 10-point rule |
| Advice judge (UNVALIDATED) | `results/advice_v1.md` | Needs the human labels before any claim |
| **Second agent model, Llama 3.1 8B (exploratory, done 10 Nov)** | `results/llama_v1.md`, `llama_extra_facts.md`, `llama_failure_breakdown.md` | Seed 0, 5 conditions, 7,860 episodes. See 5.2 |
| Raw episodes | `results/runs_v1/*.tar.gz` + `SHA256SUMS` | 9 archives, 64,326 episodes in total |
| Mid report | `ai report/report.tex` (tag `midsem`), updated 2 Nov | Builds clean |
| **Third agent model, Qwen2.5 14B Q4 (RUNNING since 10 Nov 11:40 IST)** | see Task 0 | Ends about 05:00 IST 11 Nov |
| Context pack for writers | `context.zip` | Built 2 Nov. Does **not** have Llama yet |

Checks done: every episode re-grades to its stored grade. Every cluster analysis file was re-made on the laptop and matches. The seed-0 detector re-run in the Llama node env gives the same eval metrics as before (`results/checks/detector_rerun_llama_env.json`).

### 5.2 Llama results in one paragraph

Llama 3.1 8B is unsafe in almost every red-flag episode under every condition. Policy unsafe: Plain 99.5, Plain + Label 97.6, RECHECK 97.0, RECHECK v2 96.8, Safety 91.0. RECHECK beats Plain by only 2.6 points (CI -4.0 to -1.3). It almost never calls `escalate_to_clinician` (39 calls in 1,572 Plain episodes, vs 524 for Qwen). It often writes in its own note that the message is a red flag but then does nothing (41-71% of its unsafe episodes). Tool calls are 99%+ valid, so this is not a format bug. **Report it separately. Do not pool it with Qwen. It is one seed only.** Do not run the advice judge on it: the judge is the same Llama model.

### 5.3 Numbers people get wrong

- Plain + Label escalates **less** than Plain for Qwen, not more (27.9% vs 42.0% of red-flag core episodes).
- H2 (RECHECK beats Plain with completion within 10 points) is **not supported**. RECHECK is safer but loses about 31 points of completion.
- H2b and H2c are supported (`results/final_v1.md` section 2).
- The advice judge numbers are not validated. Do not interpret them.

## 6. What is left, in order

Tags: `[ ]` open, `[!]` needs a human.

### Task 0. [ ] Collect the Qwen2.5 14B run (agent). About 2-3 h of work once it ends.

**What it is.** A scale check: does a bigger model of the same family do better? Agent model `qwen2.5:14b-instruct-q4_K_M` (4-bit, because 14B at 8-bit does not fit an 11 GB card). Same prompts, tools, eval set and seed-0 LoRA detector as the other runs. Nothing tuned. Seed 0, both phrasings, plain, safety, plain_label, recheck, recheck_v2 (7,860 episodes).

**Where.** Holder job **67671** on gnode082 (4 GPUs, `PARALLEL=1`, `CTX=8192`, plus `OLLAMA_FLASH_ATTENTION=1` and `OLLAMA_KV_CACHE_TYPE=q8_0`), started 10 Nov 11:40 IST. Queue: `cluster/queue_model.sh 67671 qwen14b` running on the ada login node. Log: `logs/queue_qwen14b.log`. Output: `runs/llm_qwen14b`. Analysis: `runs/qwen14b_analysis/`. End marker: `logs/queue/qwen14b.done`. The queue cancels the holder when done. Speed is about 7.6 episodes per minute, so it should end around **05:00 IST on 11 Nov**.

**Why the KV cache setting.** A first try (job 67648) used the default 16-bit KV cache. The model did not fit on an 11 GB card (10.5 of 11.1 GB on GPU), so it ran at about 1.4 episodes per minute. Its 7 episodes were deleted and the run restarted with an 8-bit KV cache, which fits fully (10.06 of 10.06 GB). The context stays 8192, same as the other runs. **Report this setting in the paper** as a difference from the 7B and Llama runs. Log of the first try: `logs/queue_qwen14b_attempt1.log`.

**Check it:**
```bash
ssh gr@ada-gw1.iiit.ac.in
cd ~/lma; tail logs/queue_qwen14b.log; ls logs/queue | grep qwen14b
wc -l runs/llm_qwen14b/*_s0.jsonl      # 1572 each when done
squeue -u gr
```
- If the holder died: start a new one (section 4.3, `--export=ALL,MODEL=qwen2.5:14b-instruct-q4_K_M,PARALLEL=1,CTX=8192,OLLAMA_FLASH_ATTENTION=1,OLLAMA_KV_CACHE_TYPE=q8_0`), then re-run `nohup bash cluster/queue_model.sh <new_job> qwen14b >> logs/queue_qwen14b.log 2>&1 &`. It resumes.
- **Check the model is on the GPU**, not the CPU: inside the job, `curl -s localhost:11434/api/ps` should show `size_vram` close to `size`. If not, the run is slow and should be restarted with a smaller `CTX`; say so in the paper.

**When done:** the same steps as the Llama run. `cluster/sync.sh pull`; re-make the analysis on the laptop and compare with `runs/qwen14b_analysis/` (only the scenario path in the JSON should differ); archive `runs/llm_qwen14b` into `results/runs_v1/` and add the hash; copy the analysis to `results/`; add a row to `results/README.md`; add it to the paper next to Llama. Note it is 4-bit while the 7B is 8-bit. Do not pool it with the 7B runs.

### Task 1. [ ] Write the final paper (agent, then team review). About 4-6 h.

The draft in `paper/` is mostly empty. The mid report `ai report/report.tex` has most of the text and all numbers. Reuse it.
1. `sections/results.tex`: make it from `results/` with a script. `scripts/make_report_tables.py` already makes LaTeX macros and tables; extend it for Llama. Never hand-type a number.
2. Method: add RECHECK v2. Say it is exploratory and was designed after the main results.
3. New section "Second agent model": the Llama results (5.2).
3b. Add the 14B results to the same section when Task 0 is done.
4. Discussion and conclusion. Lead with the benchmark. RECHECK lowers unsafe outcomes but costs completion. A label alone does not help. A weaker agent model barely escalates at all.
5. Limitations: Synthea realism; agent-written scenarios and seeds; q8 model, not bf16; Llama one seed only; rule-based simulator; advice judge and policy labels not validated unless Task 2 is done; no clinician review.
6. Reviewer pointers (`docs/pointers.txt`): policy grading primary, no "first" claims (safe sentence in `papers.md` section 1).
7. Citations: fix the errors in `papers.md` section 9. Only cite entries verified in `papers.md` or `docs/clinical_sources.md`.
8. Build: `cd paper && latexmk -pdf main.tex`. No undefined refs.

### Task 2. [!] Human labelling (G/A/P). All six sheets were empty on 10 Nov.

Instructions: `labelling/README.md`. Order: `advice_labels.csv` (60 rows, 30 min) first, then `stage_check.csv` (50, 1-2 h), then `policy_review_A.csv` and `_B.csv` (two people separately, 2-3 h each), `eval_text_review.csv`, `seeds_review.csv`.
Then: `.venv/bin/python scripts/score_labels.py --dir labelling --out results/labels_v1.md` and put kappa and judge sensitivity/specificity in the paper.

### Task 3. [ ] Report and context pack. About 1-2 h.

1. Add a short Llama section to `ai report/report.tex`, using macros made by `scripts/make_report_tables.py`. Rebuild.
2. Rebuild `context.zip`: add Llama to files 01, 02, 04, 05, and add `llm_llama` to `verify/reproduce.sh` and `results/llama_v1.md` to `verify/check_numbers.py` SOURCES. Run `reproduce.sh` on a fresh copy.

### Task 4. [ ] Submit. About 30 min.

1. George: make the repo public or add the TAs.
2. Tag the final commit: `git tag final && git push --tags`.

### Optional, only if time is left after Tasks 0-4

More agent models or more seeds for Llama/14B. Recipe: start a holder with the new `MODEL` (section 4.3), then `nohup bash cluster/queue_model.sh <job> <tag> >> logs/queue_<tag>.log 2>&1 &`. One seed of 5 conditions is about 8-15 h on 4 GPUs. Do not start it if it puts the paper at risk.

### Not planned (say "not run" in the paper)

Tool-call accuracy metrics, surface perturbations (typos, tone), status-correct retrieval metric, decisive-fact recall@k, manual failure analysis of 30 episodes per condition, more Llama seeds.

## 7. How to check your work

- Tests: `.venv/bin/python -m pytest -q`.
- Re-grade: `.venv/bin/python scripts/regrade_check.py --runs runs/<dir>`.
- Numbers in prose: `context/verify/check_numbers.py` (inside `context.zip`).
- Full rebuild from archives: `context/verify/reproduce.sh`.

## 8. Where things are

| Folder | What |
|---|---|
| `recheck/` | benchmark and method code (`agents/prompts.py` has every prompt) |
| `scripts/` | run, grade, analyse, make tables |
| `cluster/` | SLURM and Ollama scripts, queue scripts (`queue_model.sh` for any new agent model) |
| `data/` | eval set, policy, detector seeds, Synthea pointers |
| `results/` | every reported number and the raw archives |
| `labelling/` | sheets for humans |
| `ai report/` | mid report (LaTeX) |
| `paper/` | final paper draft (LaTeX) |
| `docs/` | proposal, design decisions, clinical sources, reviewer pointers, old handoff |
| `papers.md` | literature review and citation fixes |
| `todo.md` | the long task list (this file has the current short one) |
