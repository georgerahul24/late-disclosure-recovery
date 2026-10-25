"""Clinic policy document: short passages the agent can search.

The proposal plans about 40 passages covering escalation, cancellation and
scope rules. Each red-flag scenario names the passage(s) that justify its
action policy, so citation support can be checked.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "be", "with", "if",
         "it", "i", "my", "me", "at", "this", "that", "are", "was", "any", "by", "as", "not"}


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


@dataclass
class PolicyPassage:
    passage_id: str
    topic: str
    text: str


def load_policy(path: str | Path) -> list[PolicyPassage]:
    return [PolicyPassage(**d) for d in json.loads(Path(path).read_text())]


def lexical_search(query: str, docs: list[tuple[str, str]], k: int = 3) -> list[tuple[str, float]]:
    """Tiny bag-of-words scorer shared by policy and record search.

    `docs` is a list of (doc_id, text). Returns the top-k (doc_id, score) with
    score > 0. This is the *baseline* retriever. A dense retriever can replace
    it later without changing the tool interface (see todo.md).
    """
    q = set(tokens(query))
    if not q:
        return []
    scored = []
    for doc_id, text in docs:
        t = tokens(text)
        if not t:
            continue
        overlap = sum(1 for w in t if w in q)
        if overlap:
            scored.append((doc_id, overlap / (len(t) ** 0.5)))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored[:k]
