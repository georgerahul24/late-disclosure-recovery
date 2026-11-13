# Who made these labels

The six sheets in this folder (`advice_labels.csv`, `stage_check.csv`, `policy_review_A.csv`, `policy_review_B.csv`, `eval_text_review.csv`, `seeds_review.csv`) were filled by AI agents (Claude), on the instructor's instruction to use an agent for the labelling. They are not human labels. This replaces the old rule 7 in `handoff.md` for these sheets.

How it was done, 13 Nov 2026:
- Each sheet was split into chunks. Each chunk went to a separate agent that saw only its own chunk.
- Policy labeller A and policy labeller B were different agents and never saw each other's work.
- Columns that give away the answer were removed first: `severe`, `auto_stage`, `judge_advice`, the run name, and the scenario IDs (replaced by row numbers). IDs were mapped back after labelling.
- The agents were told to read every row and not to use keyword rules.
- All six agent types are the same model, so A vs B agreement is not independent human agreement.
- Policy B chunk 3 was written with a script that gave each group of rows the same end states. Per-scenario end-state agreement there is coarse.

Human rulings are in `human_rulings_20261113.md`. They cover the 19 policy scenarios where an agent disagreed with the benchmark, `ev-benign-40`, `ev-urgent-10` and the five flagged seeds. They are kept apart from the agent sheets.

Scores: `results/labels_v1.md`, made by `scripts/score_labels.py`.
