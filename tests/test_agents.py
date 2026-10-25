"""LLM agent plumbing tests with a fake chat client (no server needed)."""

from pathlib import Path

from recheck.agents import CONDITIONS, LLMAgent, parse_note
from recheck.agents.client import ChatResult
from recheck.detectors import OracleDetector
from recheck.policy import load_policy
from recheck.records import load_patients
from recheck.runner import run_episode
from recheck.scenarios import Episode, load_scenarios

DATA = Path(__file__).resolve().parents[1] / "data" / "dev"


class FakeClient:
    """Follows a tiny script: check availability, book, and on a red-flag
    detector line cancel the ledger booking, escalate and read back."""

    def __init__(self):
        self.n_calls = 0

    def chat(self, messages, tools=None):
        self.n_calls += 1
        last_user = next(m for m in reversed(messages) if m["role"] == "user")["content"]
        since_user = messages[messages.index(next(m for m in reversed(messages) if m["role"] == "user")):]
        done = {m["name"] for m in since_user if m["role"] == "tool"}
        note = 'NOTE: {"detected": %s, "family": "head", "urgent": %s, "cited_facts": [], "ledger": []}'
        if "label=head" in last_user or "label=urgent" in last_user:
            if "B-" in last_user and "cancel" not in done:
                bid = last_user.split("book ")[1].split()[0]
                return ChatResult("", [{"id": "1", "name": "cancel", "arguments": {"booking_id": bid}}])
            if "escalate_to_clinician" not in done:
                return ChatResult("", [{"id": "2", "name": "escalate_to_clinician",
                                        "arguments": {"reason": "head injury", "urgency": "same_day", "summary": "x"}}])
            if "list_bookings" not in done:
                return ChatResult("", [{"id": "3", "name": "list_bookings", "arguments": {}}])
            return ChatResult("I've passed this to the clinician.\n" + note % ("true", "true"))
        if "book it" in last_user and "book" not in done:
            return ChatResult("", [{"id": "4", "name": "book", "arguments": {"slot_id": "S-R1", "visit_type": "routine", "date": "x"}}])
        if "free" in last_user and "check_availability" not in done:
            return ChatResult("", [{"id": "5", "name": "check_availability", "arguments": {}}])
        return ChatResult("Okay.\n" + note % ("false", "null"))


def test_parse_note():
    text, note = parse_note('Hello there.\nNOTE: {"detected": true, "family": "head"}')
    assert text == "Hello there." and note["detected"] is True
    assert parse_note("no note")[1] is None


def test_all_conditions_construct():
    for c in CONDITIONS:
        LLMAgent(c, FakeClient(), detector=OracleDetector())


def test_recheck_with_fake_client_repairs_post_booking():
    P, S, pol = load_patients(DATA / "patients.json"), load_scenarios(DATA / "scenarios.json"), load_policy(DATA / "policy.json")
    sc = S["dev-head-00"]
    agent = LLMAgent("recheck", FakeClient(), detector=OracleDetector())
    agent.detector.set_context(sc, Episode("dev-head-00", "POST"))
    r = run_episode(Episode("dev-head-00", "POST"), sc, P[sc.patient_id], pol, agent)
    assert r.grade["end_state"] == "CANCEL_ESCALATE", r.grade
    assert not r.grade["unsafe_strict"]
    assert any(c["dropped_args"] == {"date": "x"} for c in r.calls if c["name"] == "book")
    assert all("NOTE:" not in t["text"] for t in r.transcript)
