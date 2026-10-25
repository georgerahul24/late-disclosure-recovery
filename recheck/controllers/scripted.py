from __future__ import annotations

from .. import rules
from ..runner import AgentTurn, EpisodeContext
from ..tools import ToolHarness


class ScriptedController:
    def __init__(self, detector=None, grounding: str = "record", revision: str = "cancel",
                 readback: bool = False, invariant: bool = False, name: str | None = None):
        assert grounding in ("ignore", "always", "record")
        assert revision in ("none", "cancel", "convert")
        self.detector = detector
        self.grounding = grounding
        self.revision = revision
        self.readback = readback
        self.invariant = invariant
        det = getattr(detector, "name", "none")
        self.name = name or f"scripted[{det}/{grounding}/{revision}{'/rb' if readback else ''}{'/inv' if invariant else ''}]"

    # ------------------------------------------------------------------
    def reset(self, ctx: EpisodeContext) -> None:
        self.ctx = ctx
        self.flagged = False  # an urgent red flag has been established
        self.offered: list[str] = []
        if hasattr(self.detector, "set_context"):
            self.detector.set_context(ctx.oracle_scenario, ctx.episode)

    def _is_urgent(self, family: str, tools: ToolHarness) -> tuple[bool, list[str]]:
        if family == "urgent":
            return True, []
        if family == "benign":
            return False, []
        if self.grounding == "ignore":
            return False, []
        if self.grounding == "always":
            return True, []
        tools.call("search_record", query="current medications", fact_type="medication")
        tools.call("search_record", query="conditions diabetes seizure", fact_type="condition")
        r = rules.evaluate(family, tools.privileged_record())
        return r.urgent, r.decisive_fact_ids

    def _repair(self, tools: ToolHarness) -> list[str]:
        """Repair open routine bookings. Returns the booking ids it tried."""
        tried = []
        for b in tools.ledger.open_bookings():
            if b.get("kind", "routine") != "routine":
                continue
            tried.append(b["booking_id"])
            if self.revision == "cancel":
                tools.call("cancel", booking_id=b["booking_id"])
            elif self.revision == "convert":
                tools.call("update_appointment", booking_id=b["booking_id"], priority="urgent")
        return tried

    def _verify(self, tools: ToolHarness) -> None:
        """Read back; retry once; else hand over. Also catches bookings that
        exist in the backend but are missing from the ledger (lost response)."""
        for attempt in range(2):
            res = tools.call("list_bookings")
            if not res["ok"]:
                continue
            stale = [b for b in res["result"] if b["status"] == "active" and b["kind"] == "routine"
                     and b.get("conversation_id") == tools.conversation_id]
            if not stale:
                return
            if attempt == 0:
                for b in stale:
                    if self.revision == "convert":
                        tools.call("update_appointment", booking_id=b["booking_id"], priority="urgent")
                    else:
                        tools.call("cancel", booking_id=b["booking_id"])
        tools.call("hand_over", reason="handover: could not confirm the routine booking was removed")

    def _enforce_invariant(self, tools: ToolHarness) -> None:
        # Works on the agent's own view (the ledger), not backend truth. So a
        # failed cancel gets retried here, but a booking hidden by a lost
        # response is only found by read-back (list_bookings).
        escalated = any(c.name in ("escalate_to_clinician", "hand_over") and c.ok for c in tools.calls)
        if not escalated:
            return
        for b in tools.ledger.open_bookings():
            if b.get("kind", "routine") == "routine":
                tools.call("cancel", booking_id=b["booking_id"])

    # ------------------------------------------------------------------
    def respond(self, message: str, tools: ToolHarness) -> AgentTurn:
        note = {"detected": False, "family": "benign", "urgent": None, "cited_facts": [], "ledger": []}
        reply = []
        if self.detector is not None:
            fam, score = self.detector.predict(message)
            note["family"] = fam
            if fam != "benign":
                note["detected"] = True
                urgent, facts = self._is_urgent(fam, tools)
                note["urgent"] = urgent
                note["cited_facts"] = facts
                if urgent:
                    first = not self.flagged
                    self.flagged = True
                    note["ledger"] = [{"booking_id": b["booking_id"], "still_appropriate": False}
                                      for b in tools.ledger.open_bookings()]
                    if self.revision != "none":
                        self._repair(tools)
                    if first:
                        tools.call("escalate_to_clinician", reason=f"red flag ({fam}) reported by patient",
                                   urgency="same_day" if fam != "urgent" else "immediate",
                                   summary=f"Patient said: {message[:200]}")
                    if self.readback and self.revision != "none":
                        self._verify(tools)
                    reply.append("Thank you for telling me. I have passed this to the duty clinician, "
                                 "who will contact you today.")

        if not self.flagged:
            lower = message.lower()
            if "book" in lower and self.offered:
                for sid in self.offered:
                    r = tools.call("book", slot_id=sid, visit_type="routine")
                    if r["ok"]:
                        reply.append(f"You're booked in for slot {sid}.")
                        break
                    if "no longer available" not in (r.get("error") or ""):
                        reply.append("Sorry, something went wrong with the booking.")
                        break
                    # slot taken: refresh and try the next free slot
                    fresh = tools.call("check_availability")
                    if fresh["ok"]:
                        self.offered = [s["slot_id"] for s in fresh["result"]]
            elif "free" in lower or "check" in lower or "available" in lower or not self.offered:
                r = tools.call("check_availability")
                if r["ok"]:
                    self.offered = [s["slot_id"] for s in r["result"]]
                    reply.append("These times are free: " + ", ".join(self.offered[:3]) + ".")
        if self.invariant:
            self._enforce_invariant(tools)
        return AgentTurn(" ".join(reply) or "Okay.", note)


def book_only() -> ScriptedController:
    return ScriptedController(detector=None, grounding="ignore", revision="none", name="book_only")


def rule_gate(keyword_detector) -> ScriptedController:
    # Keyword gate that blocks the next action but never revisits earlier ones,
    # and does not use the record (CareConnect pattern).
    return ScriptedController(keyword_detector, grounding="ignore", revision="none", name="rule_gate")


def dsc(detector, readback: bool = True) -> ScriptedController:
    """Deterministic state-aware controller: detector + record rules + cancel
    + invariant + read-back. The strong non-LLM baseline."""
    return ScriptedController(detector, grounding="record", revision="cancel", readback=readback,
                              invariant=True, name=f"dsc[{getattr(detector, 'name', 'none')}{'' if readback else '/no-rb'}]")
