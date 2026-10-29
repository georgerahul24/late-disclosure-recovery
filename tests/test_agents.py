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


def test_judge_parse_and_skip_empty():
    from recheck.judge import AdviceJudge, parse
    assert parse('{"advice": true, "quote": "put ice on it"}') == {"advice": True, "quote": "put ice on it"}
    assert parse("no json") is None and parse('{"advice": "yes"}') is None

    class C:
        def chat(self, messages, tools=None):
            return ChatResult('```json\n{"advice": false, "quote": ""}\n```')
    j = AdviceJudge(C())
    assert j.judge("hi", "")["advice"] is False
    assert j.judge("I hit my head", "A clinician will call you today.") == {"advice": False, "quote": "", "parse_ok": True}



NOTE = '\nNOTE: {"detected": %s, "family": "%s", "urgent": %s, "cited_facts": [], "ledger": []}'


class ClaimingClient:
    """Says "you're booked" without calling book. Calls book only after a harness check."""

    def chat(self, messages, tools=None):
        last = messages[-1]
        if last["role"] == "user" and last["content"].startswith("[Harness check]"):
            return ChatResult("", [{"id": "b", "name": "book", "arguments": {"slot_id": "S-R1", "visit_type": "routine"}}])
        return ChatResult("Great, you're booked." + NOTE % ("false", "benign", "null"))


class RepairNoEscalateClient(FakeClient):
    """Like FakeClient, but after a red flag it cancels and stops without escalating,
    unless a harness check asks it to escalate."""

    def chat(self, messages, tools=None):
        last = messages[-1]
        if last["role"] == "user" and "have not escalated" in last["content"]:
            return ChatResult("", [{"id": "e", "name": "escalate_to_clinician",
                                    "arguments": {"reason": "head injury", "urgency": "same_day", "summary": "x"}}])
        if last["role"] == "tool" and last["name"] == "escalate_to_clinician":
            return ChatResult("A clinician will call you." + NOTE % ("true", "head", "true"))
        user = next(m for m in reversed(messages) if m["role"] == "user")["content"]
        done = {m["name"] for m in messages[messages.index(next(m for m in reversed(messages) if m["role"] == "user")):]
                if m["role"] == "tool"}
        if "label=head" in user and "B-" in user:
            if "cancel" not in done:
                bid = user.split("book ")[1].split()[0]
                return ChatResult("", [{"id": "c", "name": "cancel", "arguments": {"booking_id": bid}}])
            return ChatResult("I've cancelled that booking." + NOTE % ("true", "head", "true"))
        return super().chat(messages, tools)


def _run(condition, client, sid, timing):
    P, S, pol = load_patients(DATA / "patients.json"), load_scenarios(DATA / "scenarios.json"), load_policy(DATA / "policy.json")
    sc = S[sid]
    agent = LLMAgent(condition, client, detector=OracleDetector())
    agent.detector.set_context(sc, Episode(sid, timing))
    return agent, run_episode(Episode(sid, timing), sc, P[sc.patient_id], pol, agent)


def test_v2_claim_check_makes_the_model_call_the_tool():
    sid = next(k for k, v in load_scenarios(DATA / "scenarios.json").items() if v.kind == "benign")
    agent, r = _run("recheck_v2", ClaimingClient(), sid, "T1")
    assert agent.harness_feedback >= 1
    assert any(c["name"] == "book" and c["ok"] for c in r.calls)
    agent, r = _run("recheck", ClaimingClient(), sid, "T1")  # no check: the false claim stands
    assert agent.harness_feedback == 0 and not any(c["name"] == "book" for c in r.calls)
    assert r.grade["false_claims"]


def test_v2_escalate_after_repair():
    agent, r = _run("recheck", RepairNoEscalateClient(), "dev-head-00", "POST")
    assert r.grade["end_state"] != "CANCEL_ESCALATE"  # repaired but not escalated
    agent, r = _run("recheck_v2", RepairNoEscalateClient(), "dev-head-00", "POST")
    assert agent.harness_feedback >= 1
    assert r.grade["end_state"] == "CANCEL_ESCALATE", r.grade
