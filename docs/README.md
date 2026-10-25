# docs/

Source documents and design notes. Nothing here is code.

| File | What it is |
|---|---|
| `proposal.pdf` | The submitted project proposal (7 pages). This is the source of truth for the research plan: research questions, hypotheses, benchmark design, RECHECK method, baselines, metrics, compute and timeline. There is no LaTeX source in this repo yet. |
| `pointers.txt` | Reviewer-style feedback on the proposal. Summary below. |
| `design.md` | How the proposal maps onto the code, and every design decision we made that the proposal did not pin down. Read this before changing grading or the simulator. |

## Summary of the proposal

- **RQ1 (diagnosis).** When a red flag is disclosed late, how often do tool-using LLM agents end in an unsafe state, and at which of 5 stages does recovery fail? H1: the unsafe rate rises at least 10 points from T1 to POST for Plain and Safety-prompt agents.
- **RQ2 (method).** Does RECHECK lower the unsafe rate, and which parts carry the effect? H2: RECHECK beats Plain by at least 15 points with routine completion dropping no more than 10 points. H2b: beats Plain + Label by at least 10 points. H2c: each ablation hurts the stage it targets. Equivalence with the deterministic controller (DSC) is tested with TOST at plus or minus 10 points.
- **Timings.** T1 = symptom in the first message. MID = after availability check, before booking. POST = after a confirmed booking.
- **Symptom kinds.** Universal (urgent for anyone), record-dependent (urgent only given a record fact), benign (including near-misses).
- **Planned size.** About 120 red-flag scenarios, 60 record-matched negatives and 60 benign scenarios, each at 3 timings. About 720 episodes.
- **Failure stages.** (1) detection, (2) context, (3) earlier action not recognised as wrong, (4) correction attempted but failed, (5) escalation not completed.
- **Models.** Detector: Qwen2.5-1.5B-Instruct and Qwen2.5-0.5B with LoRA (r=16, alpha=32, dropout 0.05, lr 2e-4, 3 epochs, batch 16, 3 seeds). Orchestrator: frozen Qwen2.5-7B-Instruct in a ReAct loop via vLLM.
- **Pilot (already done in the proposal).** Scripted controllers, 60 patients, 213 episodes, 53 scenarios. DSC got 16.2% strict unsafe with 99.1% completion. The pilot code was not in this folder, so `scripts/run_pilot.py` rebuilds it.

## What the reviewer pointers say (docs/pointers.txt)

1. **Main issue: the strict metric clashes with the clinician policy.** The policy allows "keep and escalate" for some scenarios, but strict grading calls any leftover routine booking unsafe. Our code fixes this by grading against the per-scenario clinician policy as the primary outcome and reporting strict as a separate stress test. See `design.md`. The proposal text still needs to be updated (see `todo.md`).
2. Lead with the benchmark. Present RECHECK as a targeted baseline, not the main breakthrough.
3. Do not claim "first" until the literature search supports it. See `papers.md`.
4. The pilot is feasibility evidence only.
