"""Run episodes: patient simulator <-> agent <-> tool harness <-> backend.

Agent interface (scripted controllers and LLM agents both implement it):

    class Agent(Protocol):
        name: str
        def reset(self, ctx: EpisodeContext) -> None: ...
        def respond(self, message: str, tools: ToolHarness) -> AgentTurn: ...

`respond` may call any number of tools through `tools.call(...)` and must
return the text reply plus an optional structured note. The note is how the
grader attributes stage 1 (detection) and stage 2 (context) failures:

    note = {
      "detected": bool,            # did you see a possible red flag in this message?
      "family": str | None,        # urgent/head/hypo/foot/benign
      "urgent": bool | None,       # after checking the record, is it urgent for THIS patient?
      "cited_facts": [fact_id],    # record facts used
      "cited_policy": [passage_id],
      "ledger": [{"booking_id": str, "still_appropriate": bool}],
    }
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from .backend import ClinicBackend, FaultPlan
from .grader import grade_episode
from .policy import PolicyPassage
from .records import PatientRecord
from .scenarios import Episode, Scenario
from .simulator import PatientSimulator
from .tools import ToolHarness


@dataclass
class AgentTurn:
    text: str
    note: dict | None = None


@dataclass
class EpisodeContext:
    episode: Episode
    patient_id: str
    conversation_id: str
    # Only the oracle detector may read this. Everyone else must ignore it.
    oracle_scenario: Scenario | None = None


class Agent(Protocol):
    name: str

    def reset(self, ctx: EpisodeContext) -> None: ...

    def respond(self, message: str, tools: ToolHarness) -> AgentTurn: ...


def fault_plan(name: str) -> FaultPlan:
    if name == "none":
        return FaultPlan()
    if name == "cancel_fails_once":
        return FaultPlan(fail_times={"cancel": 1})
    if name == "slot_taken":
        # The first routine slot is taken between check_availability and book.
        return FaultPlan(steal_after_check=["S-R1"])
    if name == "book_lost_response":
        # book succeeds but reports a timeout. The booking exists in the backend
        # but not in the agent's ledger. A blind retry creates a duplicate; an
        # agent that trusts the error never repairs the hidden booking.
        # Only list_bookings (read-back) reveals it.
        return FaultPlan(silent_success={"book": 1})
    raise ValueError(f"unknown fault {name}")


@dataclass
class EpisodeResult:
    episode: dict
    agent: str
    scenario: dict
    transcript: list[dict] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    ledger: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    final_state: dict = field(default_factory=dict)
    disclosed_turn: int | None = None
    timing_violated: bool = False
    grade: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


def run_episode(episode: Episode, scenario: Scenario, patient: PatientRecord, policy: list[PolicyPassage],
                agent: Agent, max_turns: int = 8, allow_full_record: bool = False) -> EpisodeResult:
    backend = ClinicBackend(faults=fault_plan(episode.fault))
    conv_id = f"C-{episode.episode_id}"
    harness = ToolHarness(backend, patient, policy, conv_id, allow_full_record=allow_full_record)
    sim = PatientSimulator(scenario, episode)
    agent.reset(EpisodeContext(episode, patient.patient_id, conv_id, oracle_scenario=scenario))

    res = EpisodeResult(asdict(episode), agent.name, {"scenario_id": scenario.scenario_id,
                                                       "family": scenario.family, "kind": scenario.kind,
                                                       "pair_id": scenario.pair_id})
    for turn in range(max_turns):
        msg = sim.next_message(turn, harness)
        if msg is None:
            break
        harness.turn = turn
        res.transcript.append({"turn": turn, "role": "patient", "text": msg})
        out = agent.respond(msg, harness)
        res.transcript.append({"turn": turn, "role": "agent", "text": out.text})
        if out.note is not None:
            res.notes.append({"turn": turn, **out.note})

    res.calls = [asdict(c) for c in harness.calls]
    res.ledger = harness.ledger.to_list()
    res.final_state = backend.snapshot(patient.patient_id)
    res.disclosed_turn = sim.state.disclosed_turn
    res.timing_violated = sim.state.timing_violated
    res.grade = grade_episode(res, scenario, patient)
    return res


def run_suite(episodes: list[Episode], scenarios: dict[str, Scenario], patients: dict[str, PatientRecord],
              policy: list[PolicyPassage], agent: Agent, out_path: str | Path | None = None,
              **kw) -> list[EpisodeResult]:
    results = []
    fh = open(out_path, "w") if out_path else None
    try:
        for ep in episodes:
            sc = scenarios[ep.scenario_id]
            r = run_episode(ep, sc, patients[sc.patient_id], policy, agent, **kw)
            results.append(r)
            if fh:
                fh.write(r.to_json() + "\n")
    finally:
        if fh:
            fh.close()
    return results
