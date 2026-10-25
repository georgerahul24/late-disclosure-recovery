# recheck/detectors/ (symptom detectors)

Interface: `predict(text) -> (label, score)`. The label is one of `urgent, head, hypo, foot, benign`.

| Detector | Status | Notes |
|---|---|---|
| `KeywordDetector` | done | Frozen list `data/detector/keywords.json`. Used for the rule gate (the CareConnect pattern). **Never edit the list after evaluation phrases are written.** |
| `TfidfDetector` | done | TF-IDF (1-2 grams) plus balanced logistic regression. The pilot's stand-in for LoRA. Train it on `augment_with_carriers(seeds)`. |
| `OracleDetector` | done | Knows the scenario symptom. Upper bounds only. `set_context()` is called in `reset()`. |
| `LoraDetector` | done (`lora.py`) | Qwen2.5-1.5B-Instruct (main) and Qwen2.5-0.5B (small) with a 5-way classification head. LoRA r=16, alpha=32, dropout 0.05 on the attention projections, lr 2e-4, 3 epochs, batch 16, 3 seeds, model selection on dev macro-F1. Use it with `scripts/run_llm.py --detector "lora:models/det-qwen2.5-1.5b-instruct-s{seed}"` ({seed} pairs the detector seed with the LLM seed). It needs the torch venv (`PY=/ssd_scratch/gr/lma/venv-train/bin/python`). |
| `PromptedDetector` | done (in `scripts/eval_detectors.py`) | The orchestrator model (Qwen2.5-7B), prompted zero-shot. The proposal named a large API model; none is available here, so the 7B stands in. |

## Training data rules (from the proposal and papers.md)

- **Who writes the seeds:** George writes 240 seeds (40 per red-flag family, 80 benign including near-misses). `data/detector/dev_seeds.json` is only a 56-item dev stand-in.
- **Paraphrases:** 4 LLM paraphrases per seed, checked by a second member. Paraphrases are for training only, never for evaluation phrases.
- **Carriers:** each seed goes into pre- and post-booking carrier messages (`augment_with_carriers`).
- **Split:** 85/15 train/dev **grouped by `seed_id`**, so paraphrases never cross the split.
- **Test set:** the evaluation scenarios written by Arihant and Aditya. Report the maximum n-gram overlap between train and test.
- **Report:** sensitivity at a fixed high recall, PPV, alert burden, and macro-F1. Use these text variants: symptom-only, in-message, and reworded.
