# Late-Disclosure Recovery in Stateful Clinical Agents

This repo holds the code, data, raw results and docs for the LMA course project by George R., Arihant R. and Aditya P. (team "LEs & Arihant").

This README explains how to reproduce **everything**: the patients, the evaluation set, the detectors, every experiment, every analysis file in `results/`, the report and the paper.

## The idea in one paragraph

A clinic chat agent books, changes and cancels appointments with tools. Sometimes a patient mentions a worrying symptom only after the agent has already booked a routine slot. For example: "Thanks, see you Thursday. One more thing, I hit my head yesterday." If that patient takes a blood thinner, the routine booking is now wrong. The agent has to notice the symptom, check the record, see that its own booking is now wrong, fix it, escalate to a clinician, and confirm the fix worked.

We build:
1. a **benchmark** that tests this, graded on the final backend state;
2. a method called **RECHECK** that tries to do it well.

## Contents

1. [What is in the repo](#1-what-is-in-the-repo)
2. [Requirements](#2-requirements)
3. [Path A: check every number from the raw archives (no GPU, about 30 min)](#3-path-a-check-every-number-from-the-raw-archives)
4. [Path B: rebuild everything from scratch](#4-path-b-rebuild-everything-from-scratch)
5. [Human labelling](#5-human-labelling)
6. [Report and paper](#6-report-and-paper)
7. [What is and is not bit-exact](#7-what-is-and-is-not-bit-exact)
8. [Where to read more](#8-where-to-read-more)

---

## 1. What is in the repo

```
recheck/        the Python package: backend, tool harness, simulator, grader, analysis,
                detectors, scripted controllers, LLM agents, advice judge
scripts/        every command line step (data build, runs, analysis, tables)
cluster/        SLURM + Ollama scripts for the IIIT "ada" cluster (holder jobs, queues)
data/           patients, evaluation set, clinic policy, detector seeds and paraphrases
results/        every reported number (made by scripts) and the raw episode archives
results/runs_v1 raw episodes behind every number (*.tar.gz + SHA256SUMS)
labelling/      sheets for the human labelling steps (section 5)
ai report/      mid-submission report (LaTeX; tables are generated)
paper/          final paper draft (LaTeX)
docs/           proposal, reviewer pointers, design decisions, verified clinical sources
tests/          pytest tests (37)
papers.md       literature review
handoff.md      current state, cluster how-to, traps we hit
```

Every folder has its own `README.md` with the details and the rules for changing it.

**Experiments that were run.** One condition, one seed, both phrasings = 1,572 episodes.

| Run folder | What | Size |
|---|---|---|
| `detector_eval` | keyword vs TF-IDF vs 6 LoRA detectors vs a prompted 7B model, on the eval text | 9 detectors |
| `scripted_main` | book-only, rule gate, DSC (no LLM), 3 seeds | 9 x 1,572 |
| `scripted_faults` | DSC under 3 injected tool faults | 1,704 |
| `llm_main` | Qwen2.5 7B: Plain, Safety prompt, Plain + Label, RECHECK, Hybrid, 3 seeds | 15 x 1,572 |
| `llm_ablate` | 7 RECHECK ablations, seed 0, direct phrasing | 7 x 786 |
| `llm_faults` | Plain, RECHECK, Hybrid, RECHECK without read-back under 3 tool faults | 4 x 1,704 |
| `llm_v2` | RECHECK v2 (exploratory, designed after the main results), 3 seeds | 3 x 1,572 |
| `advice_judge` | advice judge (Llama 3.1 8B) over all Qwen 7B runs | judge files |
| `llm_llama` | second agent model: Llama 3.1 8B, 5 conditions, seed 0 | 5 x 1,572 |
| `llm_qwen14b` | third agent model: Qwen2.5 14B, 5 conditions, seed 0 | 5 x 1,572 |

---

## 2. Requirements

**For Path A (laptop only):**
- Python 3.12, `uv`.
- About 3 GB of disk.
- A TeX install (`latexmk`), only if you want to rebuild the report or paper.

**For Path B (full rebuild), also:**
- A SLURM cluster with GPUs. We used IIIT "ada": RTX 2080 Ti cards (11 GB, no bf16), 4 GPUs per user. All cluster scripts assume this layout. See section 4.0.
- Internet on the compute nodes, to download Synthea, a JDK, Ollama models and Hugging Face models.

**Install (both paths):**

```bash
git clone https://github.com/georgerahul24/late-disclosure-recovery.git
cd late-disclosure-recovery
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[ml,dev,stats]"
.venv/bin/python -m pytest -q          # 37 tests should pass
```

The torch packages for detector training are installed only on the cluster (`cluster/setup_train_env.sh`).

---

## 3. Path A: check every number from the raw archives

This path needs no GPU. It unpacks the stored episodes, re-grades every one, and re-makes every analysis file.

### 3.1 Unpack and check the archives

```bash
cd results/runs_v1 && shasum -a 256 -c SHA256SUMS && cd ../..     # all 10 must say OK
mkdir -p runs && for f in results/runs_v1/*.tar.gz; do tar xzf "$f" -C runs; done
```

### 3.2 Re-grade every stored episode with the current grader

```bash
.venv/bin/python scripts/regrade_check.py --runs runs/llm_main runs/llm_v2 runs/llm_ablate \
    runs/llm_faults runs/scripted_main runs/scripted_faults runs/llm_llama runs/llm_qwen14b
```
It exits with code 1 if any stored grade differs from a fresh grade. It should report that all grades match.

### 3.3 Re-make every analysis file

Each command writes one file in `results/`. Compare it with the committed version (`git diff results/`).

```bash
PY=.venv/bin/python
MAIN="runs/llm_main runs/llm_v2 runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults"

# Main results: core table, H1, H2/H2b/H2c, Hybrid vs DSC (Holm), TOST, pass^k, extras, faults
$PY scripts/summarize_runs.py --runs $MAIN --out results/final_v1.md

# GEE logistic timing model (policy-unsafe)
$PY scripts/timing_model.py --runs runs/llm_main --scenarios data/eval/scenarios_v1.json \
    --conditions plain,plain_label,safety,recheck,hybrid --metric unsafe_policy --out results/final_timing_policy.md

# Extra counts and failure breakdown
$PY scripts/extra_facts.py --runs $MAIN --out results/extra_facts_v1.md
$PY scripts/failure_breakdown.py --runs runs/llm_main runs/llm_v2 runs/scripted_main --out results/failure_breakdown_v1.md

# Advice judge summary (unvalidated until the human labels in section 5 are scored)
$PY scripts/summarize_advice.py --runs runs/llm_main runs/llm_v2 runs/llm_ablate runs/llm_faults \
    --out results/advice_v1.md

# Second agent model (Llama 3.1 8B) and third (Qwen2.5 14B)
for m in llama qwen14b; do
  $PY scripts/summarize_runs.py   --runs runs/llm_$m --out results/${m}_v1.md
  $PY scripts/extra_facts.py      --runs runs/llm_$m --out results/${m}_extra_facts.md
  $PY scripts/failure_breakdown.py --runs runs/llm_$m --out results/${m}_failure_breakdown.md
done

# Scripted controllers on the eval set (CPU, about 1 minute, no archive needed)
$PY scripts/run_pilot.py --scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json \
    --policy data/policy/clinic_policy_v1.json --seeds data/detector/seeds_v1_decon.json --out runs/pilot_eval_v1
cp runs/pilot_eval_v1/summary.md results/scripted_eval_v1.md
cp runs/pilot_eval_v1/summary.json results/scripted_eval_v1.json

# Detector comparison: copied from the detector_eval archive
cp runs/detector_eval/summary.md results/detectors_eval_v1.md
cp runs/detector_eval/results_keyword_tfidf_lora_lora_lora_lora_lora_lora_prompted.json results/detectors_eval_v1.json
```

Notes:
- The JSON files written next to the `.md` files hold the same numbers in machine-readable form.
- Re-made files are identical to the committed ones, except for the scenario path stored inside the JSON when you run from a different folder.
- `results/lora_dev/*.metrics.json` are the LoRA training metrics, copied from each trained adapter (section 4.6).
- `results/README.md` lists every results file and the command behind it.

---

## 4. Path B: rebuild everything from scratch

The steps below are in the order we ran them. Steps 4.1 to 4.6 build the data and detectors. Steps 4.7 to 4.11 run the experiments. Rough GPU times are for 4 RTX 2080 Ti.

### 4.0 Cluster setup (once)

All cluster work runs inside a long **holder job**. It holds the GPUs for up to 4 days and starts one Ollama server per GPU. Experiments run inside it as `srun --overlap` steps, and the queue scripts do this for you.

```bash
# laptop, repo root: copy code to ~/lma on the cluster (the cluster has no GitHub access)
cluster/sync.sh push

# cluster login node
ssh gr@ada-gw1.iiit.ac.in
cd ~/lma && bash cluster/setup_env.sh            # small CPU venv in ~/lma/.venv, runs the tests

# start a holder (Qwen2.5 7B q8_0, the main agent model); pick a free node from gnode045-gnode090
pestat -p u22 --no-color --gib | grep -E "gnode0(4[5-9]|[5-8][0-9]|90)"
sbatch -w <node> cluster/hold_node.sbatch        # 4 GPUs, 16 CPUs, 64 GB, 4 days
squeue -u gr; tail -f logs/lma-hold-<jobid>.out  # wait for "READY"

# torch env for the LoRA detector, on node scratch (inside the holder)
srun --jobid=<jobid> --overlap -n 1 -c 8 --mem=16G \
    bash cluster/setup_train_env.sh > logs/setup-<jobid>.log 2>&1 && echo SETUP_OK >> logs/setup-<jobid>.log
```

Details:
- `hold_node.sbatch` takes `MODEL`, `PARALLEL` (requests per server) and `CTX` (context length) from the environment. Pass them with `--export=ALL,MODEL=...`.
- It unpacks Ollama from `~/ollama` (v0.21.2) onto node scratch and pulls the model.
- It writes `logs/hold-<jobid>.env` with the server URLs.
- **Always pass `-n 1` to `srun --overlap`.** Without it, srun starts several copies of your command.
- Cluster traps we hit are listed in `handoff.md` section 4.6 and `cluster/README.md`.

### 4.1 Patients: Synthea population

```bash
# inside the holder: JDK 17 + Synthea v3.3.0 on node scratch, seed 20261026, 6000 alive people, Massachusetts
srun --jobid=<jobid> --overlap -n 1 -c 12 --mem=40G --gres=none bash cluster/run_synthea.sh

# convert the CSVs into our record format and build the rule-based patient pools
srun --jobid=<jobid> --overlap -n 1 -c 2 --mem=24G --gres=none .venv/bin/python scripts/synthea_to_records.py \
    --csv /ssd_scratch/gr/lma/synthea/out-20261026/csv --out data/synthea
```

Outputs:
- `data/synthea/PROVENANCE.txt`: Synthea version, jar SHA256, and the line counts and SHA256 of every CSV. Compare yours with the committed file.
- `data/synthea/patients.json`: full converted records. Git-ignored, because it is 51 MB.
- `data/synthea/pools.json` and `conversion_report.md`: committed.

Bring the files back to the laptop with `cluster/sync.sh pull`.

### 4.2 Clinical rules and clinic policy (fixed files)

These are written by hand from verified guidelines. Nothing generates them.
- `docs/clinical_sources.md`: the source and recommendation number behind every rule.
- `recheck/rules.py`: the record rules (head, hypo, foot) and the matched-negative exclusions.
- `data/policy/clinic_policy_v1.json`: the 40 clinic policy passages, each with a `source`.

### 4.3 Fixed text inputs

These files are inputs, not generated. Use them as committed:

| File | What |
|---|---|
| `data/eval/phrasings_v1.json` | 180 symptom items (direct and indirect phrasing, advice question) and 24 openings |
| `data/detector/seeds_v1.json` | 240 detector training seeds, written separately from the eval text |
| `data/detector/keywords.json` | frozen keyword list for the rule gate. It was frozen before the eval text existed (made by `scripts/make_dev_data.py`, which never overwrites it) |

### 4.4 Decontaminate the seeds and build the evaluation set (laptop, seconds)

```bash
# drop training seeds that share 6+ consecutive words with any eval text
.venv/bin/python scripts/decontaminate.py --train data/detector/seeds_v1.json --out data/detector/seeds_v1_decon.json

# 270 scenarios on 240 Synthea patients: matched pairs, extra episode types, leakage report
.venv/bin/python scripts/build_eval.py
```

Outputs:
- `data/eval/scenarios_v1.json` and `patients_v1.json`.
- `data/eval/BUILD_REPORT.md`, which reports pair quality and the largest n-gram overlap with the seeds (5 words).

`build_eval.py` uses seed 20261026. It needs `data/synthea/patients.json` from 4.1.

### 4.5 Detector training paraphrases (cluster, about 10 min)

```bash
cluster/run_in_hold.sh <jobid> scripts/paraphrase_seeds.py \
    --seeds data/detector/seeds_v1_decon.json --out data/detector/paraphrases_v1.json
cluster/sync.sh pull
.venv/bin/python scripts/decontaminate.py --train data/detector/paraphrases_v1.json \
    --out data/detector/paraphrases_v1_decon.json
```

How it works:
- The model is Qwen2.5 7B at temperature 0.8.
- It asks for 4 paraphrases per seed.
- A filter, then a label-check call, drops paraphrases that change the label.
- The paraphrases are used **for training only**.

### 4.6 Train the LoRA detectors (cluster, one free GPU, about 30 min)

```bash
# free one GPU: unload the Ollama model from that GPU's server (example: GPU 3 = port 11437)
srun --jobid=<jobid> --overlap -n 1 -c 1 --mem=1G --gres=none \
    curl -s 127.0.0.1:11437/api/generate -d '{"model":"qwen2.5:7b-instruct-q8_0","keep_alive":0}'
# train Qwen2.5-1.5B-Instruct and Qwen2.5-0.5B, seeds 0, 1, 2
srun --jobid=<jobid> --overlap -n 1 -c 8 --mem=32G --gres=gpu:4 env GPU=3 bash cluster/train_detectors.sh
```

Settings:
- LoRA r=16, alpha=32, dropout 0.05 on q/k/v/o.
- Learning rate 2e-4, 3 epochs, batch 16.
- 85/15 split, grouped by seed.
- fp16 base, fp32 trainable weights.

Outputs:
- `models/det-*`: the adapters, git-ignored.
- `runs/detector/*.metrics.json`: the training metrics. Copy these to `results/lora_dev/`.

### 4.7 Main experiments (cluster, about 2 days on 4 GPUs)

One queue script runs the detector comparison, the scripted baselines, the five Qwen 7B conditions (3 seeds), the 7 ablations and the tool faults. Each step leaves a marker, so re-running skips finished steps and `run_llm.py` resumes half-finished ones.

```bash
nohup bash cluster/queue_main.sh <jobid> >> logs/queue.log 2>&1 &
tail -f logs/queue.log
```

Steps, in order (see the script for the exact flags):

| Step | Script | Output |
|---|---|---|
| `detectors` | `scripts/eval_detectors.py` | `runs/detector_eval` |
| `scripted` | `scripts/run_scripted.py` (book-only, rule gate, DSC; 3 seeds; seed-matched LoRA detector) | `runs/scripted_main` |
| `scripted_faults` | `scripts/run_scripted.py --faults ...` | `runs/scripted_faults` |
| `llm_main_recheck`, `llm_main_rest` | `scripts/run_llm.py` for 5 conditions x seeds 0,1,2, both phrasings | `runs/llm_main` |
| `llm_ablate_conf`, `llm_ablate` | 7 ablations, seed 0, direct phrasing | `runs/llm_ablate` |
| `llm_faults` | 4 conditions under `cancel_fails_once`, `book_lost_response`, `slot_taken` | `runs/llm_faults` |

Shared settings for every LLM run:
- Agent model `qwen2.5:7b-instruct-q8_0`, temperature 0, 8k context.
- LoRA detector `lora:models/det-qwen2.5-1.5b-instruct-s{seed}`. Detector seed i is paired with LLM seed i.
- Eval files `data/eval/scenarios_v1.json`, `patients_v1.json`, and the policy `data/policy/clinic_policy_v1.json`.

### 4.8 RECHECK v2, the advice judge and the main analysis (cluster)

These need a second holder: the judge job, serving Llama 3.1 8B (a different model family from the agent):

```bash
sbatch -w <node> --gres=gpu:2 -c 12 --mem=16G \
    --export=ALL,MODEL=llama3.1:8b-instruct-q8_0,PARALLEL=6,CTX=1536 cluster/hold_node.sbatch
nohup bash cluster/queue_final.sh <main_holder_jobid> <judge_jobid> >> logs/queue_final.log 2>&1 &
```

`queue_final.sh` does the following:
- runs `recheck_v2` (3 seeds, both phrasings) into `runs/llm_v2`;
- runs `scripts/judge_runs.py` over `llm_main`, `llm_v2`, `llm_ablate` and `llm_faults`, which also exports the 60-turn advice label sample;
- runs every analysis in section 3.3, writing to `runs/final_analysis/`.

### 4.9 Second agent model: Llama 3.1 8B (cluster, about 10 h)

Two holders, each with one request slot per server so Llama fits an 11 GB card at 8k context:

```bash
for i in 1 2; do sbatch -w <node> --gres=gpu:2 -c 12 --mem=30G \
    --export=ALL,MODEL=llama3.1:8b-instruct-q8_0,PARALLEL=1,CTX=8192 cluster/hold_node.sbatch; done
# build the torch env in each holder (section 4.0, it must write SETUP_OK to logs/setup-<jobid>.log)
nohup bash cluster/queue_llama.sh <job_A> <job_B> >> logs/queue_llama.log 2>&1 &
```

What it runs:
- Seed 0, both phrasings: Plain, Safety and Plain + Label on job A; RECHECK and RECHECK v2 on job B.
- It writes to `runs/llm_llama`, then regrades and analyses.
- Same prompts, tools, eval set and seed-0 LoRA detector as the Qwen runs.
- Do not run the advice judge on these runs: the judge is the same Llama model.

### 4.10 Third agent model: Qwen2.5 14B (cluster, about 18 h)

Settings needed to fit an 11 GB card: 4-bit weights, flash attention, an 8-bit KV cache, and one slot per server:

```bash
sbatch -w <node> \
    --export=ALL,MODEL=qwen2.5:14b-instruct-q4_K_M,PARALLEL=1,CTX=8192,OLLAMA_FLASH_ATTENTION=1,OLLAMA_KV_CACHE_TYPE=q8_0 \
    cluster/hold_node.sbatch
# build the torch env (section 4.0), then:
nohup bash cluster/queue_model.sh <jobid> qwen14b >> logs/queue_qwen14b.log 2>&1 &
```

`queue_model.sh` works for any Ollama agent model:
- it runs the 5 conditions (Plain, Safety, Plain + Label, RECHECK, RECHECK v2), seed 0, both phrasings, into `runs/llm_<tag>`;
- then it regrades, analyses, and cancels the holder.

Check that the model is fully on the GPU (`size_vram` equals `size` in `curl -s localhost:11434/api/ps`) before a long run. A model partly on the CPU is about 5 times slower.

### 4.11 Bring results back and archive them

```bash
cluster/sync.sh pull                                     # runs/, logs/, data/synthea/, paraphrases
.venv/bin/python scripts/regrade_check.py --runs runs/<dir>
tar czf results/runs_v1/<dir>.tar.gz -C runs <dir>       # then add its hash to results/runs_v1/SHA256SUMS
```

Then re-make the analysis files with the commands in section 3.3 and commit them.

---

## 5. Human labelling

These steps **must be done by human labellers**. The sheets are in `labelling/`, and how to fill them is in `labelling/README.md`.

1. Make the sheets:
   ```bash
   .venv/bin/python scripts/export_labelling.py --out labelling     # policy x2, stage check, eval text, seeds
   ```
   The advice sheet (`advice_labels.csv`, 60 turns) comes from the judge sample (section 4.8, made by `summarize_advice.py --label-sample ... --label-out labelling`).
2. Fill the sheets:
   - `advice_labels.csv`: did the agent give medical advice?
   - `stage_check.csv`: check the automatic first-failed stage on 50 failed episodes.
   - `policy_review_A.csv` and `policy_review_B.csv`: acceptable end states per scenario. Two people, each working alone.
   - `eval_text_review.csv` and `seeds_review.csv`: are the texts realistic and correctly labelled?
3. Score them:
   ```bash
   .venv/bin/python scripts/score_labels.py --dir labelling --out results/labels_v1.md
   ```
   This gives Cohen's kappa for the action policy, stage-check agreement, the advice judge's sensitivity and specificity, and the review counts.

---

## 6. Report and paper

```bash
# mid-submission report: generate all tables and number macros, then build
.venv/bin/python scripts/make_report_tables.py \
    --runs runs/llm_main runs/llm_v2 runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults \
    --detectors results/detectors_eval_v1.json --gee results/final_timing_policy.md --out "ai report/tables"
cd "ai report" && latexmk -pdf report.tex && cd ..

# paper
cd paper && latexmk -pdf main.tex
```

Never type a result number by hand: tables and macros come from `make_report_tables.py` and `make_tables.py`. The report as submitted at mid-term is git tag `midsem`.

---

## 7. What is and is not bit-exact

- **Exact (deterministic code, fixed seeds):**
  - Synthea people (check the CSV hashes in `PROVENANCE.txt`);
  - pools and the evaluation set;
  - decontamination;
  - the scripted controllers;
  - grading, re-grading and all analysis from the raw episodes (bootstrap seeds are fixed).
- **Close, but not bit-exact:**
  - LLM episodes. They run at temperature 0 with a fixed seed, but Ollama on GPUs is not exactly deterministic across batch sizes. That is why the main conditions use 3 seeds and report scenario-level confidence intervals.
  - LoRA training (GPU nondeterminism).
- **Not regenerable by script:**
  - the paraphrases (sampled at temperature 0.8);
  - the authored text files in 4.3.

  Use the committed files. The raw episode archives in `results/runs_v1/` are the ground truth for every reported number.

---

## 8. Where to read more

| If you want... | Read |
|---|---|
| Current state, cluster how-to, traps | [`handoff.md`](handoff.md), [`instructions.md`](instructions.md), [`cluster/README.md`](cluster/README.md) |
| Every results file and its command | [`results/README.md`](results/README.md) |
| Design decisions (grading, stages, faults, statistics) | [`docs/design.md`](docs/design.md) |
| The research plan and reviewer feedback | [`docs/proposal.pdf`](docs/proposal.pdf), [`docs/pointers.txt`](docs/pointers.txt) |
| Clinical grounding | [`docs/clinical_sources.md`](docs/clinical_sources.md) |
| Related work | [`papers.md`](papers.md) |
| Code | [`recheck/README.md`](recheck/README.md), [`scripts/README.md`](scripts/README.md) |
| Data | [`data/README.md`](data/README.md), [`data/eval/README.md`](data/eval/README.md), [`data/synthea/README.md`](data/synthea/README.md) |
