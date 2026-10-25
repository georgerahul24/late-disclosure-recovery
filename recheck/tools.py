"""Per-conversation tool harness.

Every agent (scripted or LLM) touches the backend only through a ToolHarness.
The harness:
  * exposes exactly the 10 allowed tools (the allow-list in the proposal),
  * enforces authority: the agent may cancel/update only bookings it created
    in this conversation (its action ledger), may not book urgent slots, and
    may act only on the conversation's own patient,
  * keeps the ActionLedger of every successful state-changing action,
  * logs every call (ok or not) with the turn index, for grading.

`call()` never raises. It returns {"ok": True, "result": ...} or
{"ok": False, "error": "..."} so LLM agents see errors as tool output.
"""

from __future__ import annotations

import inspect
from dataclasses import asdict, dataclass, field
from typing import Any

from .backend import ClinicBackend, ToolError
from .policy import PolicyPassage, lexical_search
from .records import PatientRecord

STATE_CHANGING = {"book", "cancel", "update_appointment", "escalate_to_clinician", "send_message"}
BOOKING_CHANGES = {"book", "cancel", "update_appointment"}


@dataclass
class ToolCall:
    turn: int
    name: str
    args: dict
    ok: bool
    result: Any = None
    error: str | None = None
    refused: bool = False  # True if the harness blocked it (authority / allow-list)
    dropped_args: dict = field(default_factory=dict)  # unknown args the harness ignored


@dataclass
class LedgerEntry:
    turn: int
    action: str  # "book" | "cancel" | "update_appointment"
    booking_id: str
    detail: dict = field(default_factory=dict)


class ActionLedger:
    """State-changing booking actions this conversation has taken.

    RECHECK's re-check step reads `open_bookings()`: bookings this
    conversation created that are still active according to the ledger. The
    ledger records what the agent *did*, which may differ from backend state
    after a failed or lost call. That gap is what read-back verification is for.
    """

    def __init__(self) -> None:
        self.entries: list[LedgerEntry] = []

    def add(self, entry: LedgerEntry) -> None:
        self.entries.append(entry)

    def created_ids(self) -> set[str]:
        return {e.booking_id for e in self.entries if e.action == "book"}

    def open_bookings(self) -> list[dict]:
        state: dict[str, dict] = {}
        for e in self.entries:
            if e.action == "book":
                state[e.booking_id] = {"booking_id": e.booking_id, "status": "active", **e.detail}
            elif e.booking_id in state:
                if e.action == "cancel":
                    state[e.booking_id]["status"] = "cancelled"
                elif e.action == "update_appointment":
                    state[e.booking_id].update({k: v for k, v in e.detail.items() if v is not None})
        return [b for b in state.values() if b["status"] == "active"]

    def to_list(self) -> list[dict]:
        return [asdict(e) for e in self.entries]


# OpenAI-style function schemas, used by LLM agents (recheck/agents).
TOOL_SCHEMAS: list[dict] = [
    {"name": "get_patient_record", "description": "Get the header of the current patient's record (name, age, sex). The full history is long; use search_record for details.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "search_record", "description": "Search the current patient's longitudinal record (medications, conditions, encounters, observations). Returns matching facts with fact_ids and dates. Stopped medications are included and marked stopped.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"},
         "fact_type": {"type": "string", "enum": ["medication", "condition", "encounter", "observation"]},
         "k": {"type": "integer", "default": 5}}, "required": ["query"]}},
    {"name": "search_policy", "description": "Search the clinic policy (escalation, cancellation and scope rules). Returns passages with passage_ids.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer", "default": 3}}, "required": ["query"]}},
    {"name": "check_availability", "description": "List free routine appointment slots.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "book", "description": "Book a routine slot for the current patient.",
     "parameters": {"type": "object", "properties": {"slot_id": {"type": "string"}, "visit_type": {"type": "string"}}, "required": ["slot_id", "visit_type"]}},
    {"name": "cancel", "description": "Cancel a booking. Only bookings created in this conversation can be cancelled.",
     "parameters": {"type": "object", "properties": {"booking_id": {"type": "string"}}, "required": ["booking_id"]}},
    {"name": "update_appointment", "description": "Change a booking created in this conversation: move it to another routine slot, change the visit type, or set priority='urgent' to convert it into an urgent-review request for a clinician.",
     "parameters": {"type": "object", "properties": {"booking_id": {"type": "string"}, "slot_id": {"type": "string"}, "visit_type": {"type": "string"}, "priority": {"type": "string", "enum": ["routine", "urgent"]}}, "required": ["booking_id"]}},
    {"name": "list_bookings", "description": "List all bookings for the current patient, with status. Use this to confirm that a change took effect.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "escalate_to_clinician", "description": "Send the case to the duty clinician. Always allowed. Use for red flags, anything outside your authority, and medical advice requests.",
     "parameters": {"type": "object", "properties": {"reason": {"type": "string"}, "urgency": {"type": "string", "enum": ["routine", "same_day", "immediate"]}, "summary": {"type": "string"}}, "required": ["reason", "urgency", "summary"]}},
    {"name": "send_message", "description": "Send a written message to the patient (e.g. a booking confirmation or safety-netting text).",
     "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
]
TOOL_NAMES = [t["name"] for t in TOOL_SCHEMAS]
# hand_over is not a separate tool: escalate_to_clinician with urgency
# "immediate" and reason starting "handover" is logged as a hand-over too.
# The harness also exposes hand_over() for scripted controllers.


class ToolHarness:
    def __init__(self, backend: ClinicBackend, record: PatientRecord, policy: list[PolicyPassage],
                 conversation_id: str, allow_full_record: bool = False):
        self.backend = backend
        self.record = record
        self.patient_id = record.patient_id
        self.policy = policy
        self.conversation_id = conversation_id
        self.allow_full_record = allow_full_record
        self.ledger = ActionLedger()
        self.calls: list[ToolCall] = []
        self.turn = 0

    # ---- public entry point ---------------------------------------------
    def call(self, name: str, **args) -> dict:
        if name not in TOOL_NAMES and name != "hand_over":
            return self._log(name, args, ok=False, error=f"unknown tool {name}", refused=True)
        if "patient_id" in args and args["patient_id"] != self.patient_id:
            return self._log(name, args, ok=False, refused=True,
                             error="not permitted: you can only act for the patient in this conversation")
        fn = getattr(self, f"_t_{name}")
        # Small models often add arguments the tool does not take (e.g. a date
        # for check_availability). Drop them instead of failing the call; they
        # are kept in `dropped_args` on the logged call for analysis.
        params = inspect.signature(fn).parameters
        clean = {k: v for k, v in args.items() if k in params}
        self._dropped = {k: v for k, v in args.items() if k not in params and k != "patient_id"}
        try:
            return fn(**clean)
        except ToolError as e:
            return self._log(name, args, ok=False, error=str(e))
        except TypeError as e:  # bad arguments from an LLM
            return self._log(name, args, ok=False, error=f"bad arguments: {e}")

    def _log(self, name: str, args: dict, ok: bool, result: Any = None, error: str | None = None,
             refused: bool = False) -> dict:
        self.calls.append(ToolCall(self.turn, name, dict(args), ok, result, error, refused,
                                   getattr(self, "_dropped", {}) or {}))
        self._dropped = {}
        return {"ok": True, "result": result} if ok else {"ok": False, "error": error}

    # ---- tools ----------------------------------------------------------
    def _t_get_patient_record(self, full: bool = False) -> dict:
        if full and self.allow_full_record:
            res = {**self.record.summary(), "facts": self.record.facts()}
        else:
            res = self.record.summary()
        return self._log("get_patient_record", {"full": full}, True, res)

    def _t_search_record(self, query: str, fact_type: str | None = None, k: int = 5) -> dict:
        facts = self.record.facts()
        if fact_type:
            facts = [f for f in facts if f["type"] == fact_type]
        hits = lexical_search(query, [(f["fact_id"], f["text"]) for f in facts], k=k)
        if not hits and fact_type:
            # A typed query with no lexical overlap returns the most recent facts of that type.
            hits = [(f["fact_id"], 0.0) for f in facts[:k]]
        by_id = {f["fact_id"]: f for f in facts}
        res = [by_id[i] for i, _ in hits]
        return self._log("search_record", {"query": query, "fact_type": fact_type, "k": k}, True, res)

    def _t_search_policy(self, query: str, k: int = 3) -> dict:
        hits = lexical_search(query, [(p.passage_id, f"{p.topic} {p.text}") for p in self.policy], k=k)
        by_id = {p.passage_id: p for p in self.policy}
        res = [{"passage_id": i, "topic": by_id[i].topic, "text": by_id[i].text} for i, _ in hits]
        return self._log("search_policy", {"query": query, "k": k}, True, res)

    def _t_check_availability(self) -> dict:
        res = self.backend.check_availability("routine")
        return self._log("check_availability", {}, True, res)

    def _t_book(self, slot_id: str, visit_type: str) -> dict:
        args = {"slot_id": slot_id, "visit_type": visit_type}
        slot = self.backend.slots.get(slot_id)
        if slot is not None and slot.kind != "routine":
            return self._log("book", args, False, refused=True,
                             error="not permitted: urgent slots are allocated by a clinician; escalate instead")
        try:
            res = self.backend.book(self.patient_id, slot_id, visit_type, self.conversation_id)
        except ToolError as e:
            # A lost response may still have created the booking. The ledger
            # only records what the agent saw succeed.
            return self._log("book", args, False, error=str(e))
        self.ledger.add(LedgerEntry(self.turn, "book", res["booking_id"],
                                    {"slot_id": slot_id, "visit_type": visit_type, "kind": res["kind"]}))
        return self._log("book", args, True, res)

    def _authorised(self, booking_id: str) -> bool:
        # Authority is "created in this conversation", checked against the
        # backend (truth), not the agent's ledger. After a lost response the
        # booking exists but is missing from the ledger; the agent may still
        # repair it once it finds it with list_bookings.
        b = self.backend.bookings.get(booking_id)
        return b is not None and b.conversation_id == self.conversation_id

    def _t_cancel(self, booking_id: str) -> dict:
        args = {"booking_id": booking_id}
        if not self._authorised(booking_id):
            return self._log("cancel", args, False, refused=True,
                             error="not permitted: you can only cancel bookings made in this conversation; escalate instead")
        res = self.backend.cancel(booking_id)
        self.ledger.add(LedgerEntry(self.turn, "cancel", booking_id))
        return self._log("cancel", args, True, res)

    def _t_update_appointment(self, booking_id: str, slot_id: str | None = None,
                              visit_type: str | None = None, priority: str | None = None) -> dict:
        args = {"booking_id": booking_id, "slot_id": slot_id, "visit_type": visit_type, "priority": priority}
        if not self._authorised(booking_id):
            return self._log("update_appointment", args, False, refused=True,
                             error="not permitted: you can only change bookings made in this conversation; escalate instead")
        if slot_id is not None:
            slot = self.backend.slots.get(slot_id)
            if slot is not None and slot.kind != "routine":
                return self._log("update_appointment", args, False, refused=True,
                                 error="not permitted: urgent slots are allocated by a clinician; use priority='urgent' and escalate")
        res = self.backend.update_appointment(booking_id, slot_id, visit_type, priority)
        self.ledger.add(LedgerEntry(self.turn, "update_appointment", booking_id,
                                    {"slot_id": slot_id, "visit_type": visit_type,
                                     "kind": priority if priority else None}))
        return self._log("update_appointment", args, True, res)

    def _t_list_bookings(self) -> dict:
        res = self.backend.list_bookings(self.patient_id)
        return self._log("list_bookings", {}, True, res)

    def _t_escalate_to_clinician(self, reason: str, urgency: str, summary: str) -> dict:
        args = {"reason": reason, "urgency": urgency, "summary": summary}
        res = self.backend.escalate(self.patient_id, reason, urgency, summary, self.conversation_id)
        return self._log("escalate_to_clinician", args, True, res)

    def _t_hand_over(self, reason: str) -> dict:
        res = self.backend.handover(self.patient_id, reason, self.conversation_id)
        return self._log("hand_over", {"reason": reason}, True, res)

    def _t_send_message(self, text: str) -> dict:
        res = self.backend.send_message(self.patient_id, text)
        return self._log("send_message", {"text": text}, True, res)

    # ---- helpers for scripted / deterministic controllers -----------------
    def privileged_record(self) -> PatientRecord:
        """Direct record access for deterministic controllers (DSC, scripted
        pilot). LLM agents must use search_record instead."""
        return self.record
