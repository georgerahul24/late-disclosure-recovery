from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol

from ..rules import FAMILIES


class Detector(Protocol):
    name: str

    def predict(self, text: str) -> tuple[str, float]: ...


def load_seeds(path: str | Path) -> list[dict]:
    """Seed file: list of {"text": str, "label": family, "seed_id": str}.

    Paraphrases of a seed share its seed_id so train/dev splits can be grouped
    by seed (paraphrases never cross the split)."""
    return json.loads(Path(path).read_text())


class KeywordDetector:
    """Frozen keyword list (the CareConnect-style rule gate).

    The list must be frozen BEFORE any evaluation phrase is written
    (proposal section 4). Keep it in data/detector/keywords.json.
    """

    name = "keyword"

    def __init__(self, keywords: dict[str, list[str]]):
        self.patterns = {fam: re.compile(r"\b(" + "|".join(map(re.escape, kws)) + r")\b", re.I)
                         for fam, kws in keywords.items() if kws}

    @classmethod
    def from_file(cls, path: str | Path) -> "KeywordDetector":
        return cls(json.loads(Path(path).read_text()))

    def predict(self, text: str) -> tuple[str, float]:
        # "urgent" wins over record-dependent families if both match.
        for fam in ("urgent", "head", "hypo", "foot"):
            p = self.patterns.get(fam)
            if p and p.search(text):
                return fam, 1.0
        return "benign", 1.0


class TfidfDetector:
    """TF-IDF + logistic regression. Stands in for the LoRA model in the pilot."""

    name = "tfidf"

    def __init__(self, threshold: float = 0.0):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline

        self.threshold = threshold
        self.model = make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1),
            LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced"),
        )

    def fit(self, texts: list[str], labels: list[str]) -> "TfidfDetector":
        self.model.fit(texts, labels)
        return self

    def predict(self, text: str) -> tuple[str, float]:
        probs = self.model.predict_proba([text])[0]
        classes = list(self.model.classes_)
        i = int(probs.argmax())
        label, score = classes[i], float(probs[i])
        if label != "benign" and score < self.threshold:
            return "benign", 1 - score
        return label, score


class OracleDetector:
    """Perfect detector: knows whether the message contains the scenario's symptom.

    Only for the pilot / upper bounds. It reads the scenario from the episode
    context, which no other component may do.
    """

    name = "oracle"

    def __init__(self) -> None:
        self.symptom: str | None = None
        self.family = "benign"

    def set_context(self, scenario, episode) -> None:
        self.symptom = scenario.symptom(episode.phrasing) if scenario else None
        self.family = scenario.family if scenario else "benign"

    def predict(self, text: str) -> tuple[str, float]:
        if self.symptom and self.symptom in text and self.family in FAMILIES:
            return self.family, 1.0
        return "benign", 1.0
