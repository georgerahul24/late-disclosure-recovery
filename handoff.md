# Handoff

Last updated: 2026-10-26. Update this file whenever the state changes.

## 1. What this project is

A course research project (LMA) by George R., Arihant R. and Aditya P. It has two parts:
- **The benchmark.** Can a clinic booking agent notice that a symptom disclosed late makes its *own earlier booking* unsafe, then repair it, escalate, and confirm the fix? Grading uses the final backend state.
- **RECHECK.** A detector plus a frozen LLM with record retrieval, an action ledger re-check, repair and read-back.

The plan is in `docs/proposal.pdf`. The review feedback is in `docs/pointers.txt`. Related work is in `papers.md`.

## 2. Read in this order

1. `instructions.md`: standing rules from George (commit per feature, push after each commit, no fake data, cluster how-to).
2. `todo.md`: what is done and what is next.
3. `docs/design.md`: how the proposal maps to code, and every decision we made.
4. The `README.md` in each folder you touch.

## 3. Current state

**Code (done, tested, 29 tests pass):**
- The full episode loop: backend, tool harness, simulator, runner, grader and analysis.
- Scripted controllers, including the DSC.
- LLM agents for all 12 conditions (5 main + 7 ablations), talking to any OpenAI-compatible server.
- Cluster scripts: rsync, env setup, a 4-day node holder with one Ollama server per GPU, and an `srun --overlap` runner.

**Grading choice that differs from the proposal text:**
- The primary outcome is **policy** grading, against the clinician-acceptable end states.
- **Strict** is reported as a stress test.
- This fixes the main reviewer pointer. The proposal text has not been updated yet.

**Data:**
- `data/dev/` holds hand-made fixtures. **They are for unit tests only. Never report results on them.** George asked for no dummy data in any result.
- Real data is in progress:
  - The Synthea population is being generated on the cluster.
  - A research agent is verifying clinical sources (`docs/clinical_sources.md`).
  - A separate agent is writing detector seeds blind to the eval set (`data/detector/seeds_v1.json`).
- The evaluation scenarios (`data/eval/`) do not exist yet.

**Pilot on the dev fixtures (smoke test only, not a finding):**
- Oracle gets 0% unsafe and 100% completion. Book-only gets 100% unsafe. The sanity checks pass.
- The DSC with the TF-IDF stand-in gets 27.8% policy-unsafe and 98.3% completion. Every miss is a detection miss, because the dev seed set is tiny.

## 4. Cluster state (check before you start)

- **Holder job 39713** runs on **gnode089**: 4x RTX 2080 Ti, 36 CPUs, 100 GB RAM, 4-day limit. It started 2026-10-26 about 03:40 IST.
  - When it is ready, it writes `~/lma/logs/hold-39713.env` with the Ollama URLs.
  - Check it with `squeue -u gr` and `cat ~/lma/logs/lma-hold-39713.out`.
- **Run things inside it:**
  - LLM runs: `cluster/run_in_hold.sh 39713 scripts/run_llm.py ...`
  - Anything else: `srun --jobid=39713 --overlap -n 1 -c <k> --mem=<m> <cmd>`
  - **Always pass `-n 1`.** Without it srun starts several copies; this already corrupted a download once.
- **Node-local files** live in `/ssd_scratch/gr/lma` on gnode089: the Ollama binary, the models, the JDK, the Synthea jar and the raw Synthea CSVs. If the holder moves to another node, all of this must be rebuilt. The scripts do this automatically.
- **When the holder ends** (about 2026-10-30), submit a new one with `sbatch -w <node> cluster/hold_node.sbatch` on a node from gnode045 to gnode090 that has 4 free GPUs.

## 5. Known issues and traps

- **`sbatch --test-only` gives false start times on this cluster.** Submit for real instead.
- **Requests for 3 or more GPUs can sit as "ReqNodeNotAvail, reserved"** on half-used nodes. Fully free nodes (gnode072, gnode089 that day) start at once.
- **Home quota is nearly full** (about 4 GB free). Put big things on node scratch.
- **The 2080 Ti has no bf16.** We use the q8_0 Ollama model and fp16 for LoRA. This is a deviation from the proposal and must be reported.
- **TF-IDF needs carrier augmentation.** Without it, it flags every booking message. This is fixed, and `augment_with_carriers` must be used.
- **Read-back result differs from the proposal's pilot.** Because the DSC invariant retries a failed cancel, `cancel_fails_once` does not hurt the DSC. The lost-response fault is the case that shows read-back matters. See docs/design.md section 6.

## 6. Decisions that need a human (G/A/P)

- **Evaluation scenarios.** If they are agent-drafted, A and P must review them, and the `author` field must say who wrote them.
- **Clinical action policy per scenario**, with Cohen's kappa between two members.
- **Human labels:** about 60 for the advice judge, and 50 traces for the stage 1/2 check.
- **The second-member check** of the LLM paraphrases.

## 7. Repo

https://github.com/georgerahul24/late-disclosure-recovery (private). Code reaches the cluster by `cluster/sync.sh push`, because the cluster has no GitHub credentials.
