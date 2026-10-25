"""Scenarios and episodes.

A *scenario* is one piece of content: a patient, a routine request and one
symptom (or none). An *episode* is a scenario run under one condition:
a disclosure timing (T1 / MID / POST), a phrasing (direct / indirect) and an
optional tool fault. Every scenario is run at all three timings so timing
effects are measured on identical content.

The unit of analysis is the scenario, not the episode (see analysis.py).

Scenario kinds:
    universal          red flag for anyone (family "urgent")
    record_dependent   red flag only because of a record fact (head/hypo/foot)
    matched_negative   same words as a record_dependent scenario, given to a
                       patient without the risk fact; must be routine
    benign             not a red flag (includes near-misses)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import rules
from .records import PatientRecord

TIMINGS = ("T1", "MID", "POST")
ASK = "ASK"  # timing used for follow-up-only (on_question) scenarios
KINDS = ("universal", "record_dependent", "matched_negative", "benign")

# End states (see grader.classify_end_state)
END_STATES = ("CANCEL_ESCALATE", "CONVERT_URGENT", "KEEP_ESCALATE", "HANDOVER",
              "ROUTINE_BOOKED", "NO_ACTION")
DEFAULT_RED_FLAG_ACCEPTABLE = ["CANCEL_ESCALATE", "CONVERT_URGENT", "HANDOVER"]
DEFAULT_ROUTINE_ACCEPTABLE = ["ROUTINE_BOOKED"]

# Named fault variants. Each maps to a backend FaultPlan (see runner.py).
FAULTS = ("none", "cancel_fails_once", "slot_taken", "book_lost_response")


@dataclass
class Scenario:
    scenario_id: str
    family: str  # one of rules.FAMILIES
    kind: str  # one of KINDS
    patient_id: str
    visit_type: str
    opening: str  # routine request, without the symptom
    symptom_direct: str | None = None
    symptom_indirect: str | None = None
    severe: bool = False
    pair_id: str | None = None  # shared by a record_dependent scenario and its matched negative
    acceptable_end_states: list[str] | None = None  # clinician policy; None = default for red flag / routine
    policy_passage_ids: list[str] = field(default_factory=list)
    decisive_fact_ids: list[str] | None = None  # None = taken from the record rule
    uncertain: bool = False  # policy marked uncertain; reported separately
    disclosure: str = "volunteer"  # "volunteer" | "on_question" (follow-up-only red flag)
    advice_request: str | None = None  # e.g. "Should I take paracetamol for it?"
    author: str = "unknown"
    split: str = "dev"  # "dev" fixtures vs "eval" (team-written, never tuned on)
    notes: str = ""

    def symptom(self, phrasing: str) -> str | None:
        return self.symptom_direct if phrasing == "direct" else (self.symptom_indirect or self.symptom_direct)

    def rule(self, patient: PatientRecord) -> rules.RuleResult:
        return rules.evaluate(self.family, patient, self.severe)

    def is_red_flag(self, patient: PatientRecord) -> bool:
        return self.rule(patient).urgent

    def acceptable(self, patient: PatientRecord) -> list[str]:
        if self.acceptable_end_states is not None:
            return self.acceptable_end_states
        return DEFAULT_RED_FLAG_ACCEPTABLE if self.is_red_flag(patient) else DEFAULT_ROUTINE_ACCEPTABLE

    def decisive_facts(self, patient: PatientRecord) -> list[str]:
        if self.decisive_fact_ids is not None:
            return self.decisive_fact_ids
        return self.rule(patient).decisive_fact_ids

    def validate(self, patient: PatientRecord) -> list[str]:
        """Return a list of problems (empty = valid)."""
        errs = []
        if self.family not in rules.FAMILIES:
            errs.append(f"unknown family {self.family}")
        if self.kind not in KINDS:
            errs.append(f"unknown kind {self.kind}")
        if self.kind != "benign" and not self.symptom_direct:
            errs.append("missing symptom_direct")
        r = self.rule(patient)
        if self.kind == "universal" and self.family != "urgent":
            errs.append("universal scenarios must use family 'urgent'")
        if self.kind == "record_dependent":
            if self.family not in rules.RECORD_DEPENDENT:
                errs.append("record_dependent needs a head/hypo/foot family")
            elif not r.urgent:
                errs.append(f"record_dependent but rule says not urgent: {r.reason}")
        if self.kind == "matched_negative":
            if r.urgent:
                errs.append(f"matched_negative but rule says urgent: {r.reason}")
            elif not r.valid_negative:
                errs.append("matched_negative patient fails exclusion criteria")
            if not self.pair_id:
                errs.append("matched_negative needs pair_id")
        if self.kind == "benign" and self.family != "benign":
            errs.append("benign scenarios must use family 'benign'")
        if self.disclosure not in ("volunteer", "on_question"):
            errs.append(f"unknown disclosure {self.disclosure}")
        for s in self.acceptable_end_states or []:
            if s not in END_STATES:
                errs.append(f"unknown end state {s}")
        return errs


@dataclass(frozen=True)
class Episode:
    scenario_id: str
    timing: str
    phrasing: str = "direct"
    fault: str = "none"
    seed: int = 0

    @property
    def episode_id(self) -> str:
        return f"{self.scenario_id}|{self.timing}|{self.phrasing}|{self.fault}|s{self.seed}"


def load_scenarios(path: str | Path) -> dict[str, Scenario]:
    data = json.loads(Path(path).read_text())
    return {d["scenario_id"]: Scenario(**d) for d in data}


def save_scenarios(scenarios: list[Scenario], path: str | Path) -> None:
    Path(path).write_text(json.dumps([asdict(s) for s in scenarios], indent=1))


def expand_episodes(scenarios: dict[str, Scenario], timings=TIMINGS, phrasings=("direct",),
                    faults=("none",), seeds=(0,)) -> list[Episode]:
    """Cross every scenario with every timing/phrasing/fault/seed.

    Benign scenarios with no symptom only need one timing (they have nothing to
    disclose), so they are run at T1 only. Faults that need a booking to be
    cancelled are only applied to red-flag-capable scenarios at POST.
    """
    eps = []
    for sid, sc in scenarios.items():
        has_symptom = bool(sc.symptom_direct)
        if sc.disclosure == "on_question":
            ts = (ASK,)
        else:
            ts = timings if has_symptom else ("T1",)
        for t in ts:
            for ph in phrasings:
                if ph == "indirect" and not sc.symptom_indirect:
                    continue
                for f in faults:
                    if f.startswith("cancel_") and (t != "POST" or sc.kind in ("benign", "matched_negative")):
                        continue
                    for s in seeds:
                        eps.append(Episode(sid, t, ph, f, s))
    return eps
