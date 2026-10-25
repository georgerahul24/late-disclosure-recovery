"""Symptom detectors. All share one interface:

    det.predict(text) -> (label, score)

label is one of rules.FAMILIES ("urgent", "head", "hypo", "foot", "benign").
score is the confidence of that label in [0, 1].

Implemented:  KeywordDetector, TfidfDetector, OracleDetector.
Planned:      LoraDetector (Qwen2.5-0.5B / 1.5B + LoRA, see detectors/README.md),
              PromptedDetector (large API model, zero-shot).
"""

from .base import Detector, KeywordDetector, OracleDetector, TfidfDetector, augment_with_carriers, load_seeds

__all__ = ["augment_with_carriers", "Detector", "KeywordDetector", "OracleDetector", "TfidfDetector", "load_seeds"]
