"""Mock clinic backend.

This is the "system state" that grading reads at the end of an episode. It is
deliberately small and deterministic: a fixed set of slots, a booking table,
an escalation queue, a hand-over queue and an outbox of patient messages.

Fault injection: a `FaultPlan` can make a named operation fail a set number of
times (transient error) or make a slot get taken between check and booking.
Faults are consumed in order, so the same plan always gives the same trace.
"""

from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, field


class ToolError(Exception):
    """Raised for a backend failure the agent should notice (transient or not)."""


@dataclass
class Slot:
    slot_id: str
    start: str  # ISO datetime
    kind: str  # "routine" | "urgent"
    clinician: str


@dataclass
class Booking:
    booking_id: str
    patient_id: str
    slot_id: str
    visit_type: str
    kind: str  # "routine" | "urgent"
    status: str = "active"  # "active" | "cancelled"
    conversation_id: str | None = None


@dataclass
class Escalation:
    escalation_id: str
    patient_id: str
    reason: str
    urgency: str
    summary: str
    conversation_id: str | None = None


@dataclass
class FaultPlan:
    # op name -> number of times it should fail before succeeding
    fail_times: dict[str, int] = field(default_factory=dict)
    # slot ids that become unavailable right after the first check_availability
    steal_after_check: list[str] = field(default_factory=list)
    # op name -> "silent": the call raises an error but the write DID happen
    # (lost-response case). Used for read-back tests.
    silent_success: dict[str, int] = field(default_factory=dict)


DEFAULT_SLOTS = [
    Slot("S-R1", "2026-11-05T09:00", "routine", "Dr Shah"),
    Slot("S-R2", "2026-11-05T10:30", "routine", "Dr Shah"),
    Slot("S-R3", "2026-11-06T14:00", "routine", "Dr Okafor"),
    Slot("S-R4", "2026-11-09T11:00", "routine", "Dr Okafor"),
    Slot("S-U1", "2026-11-02T15:00", "urgent", "Duty clinician"),
    Slot("S-U2", "2026-11-02T16:30", "urgent", "Duty clinician"),
]


class ClinicBackend:
    def __init__(self, slots: list[Slot] | None = None, faults: FaultPlan | None = None):
        self.slots = {s.slot_id: s for s in (slots or DEFAULT_SLOTS)}
        self.bookings: dict[str, Booking] = {}
        self.escalations: list[Escalation] = []
        self.handovers: list[dict] = []
        self.outbox: list[dict] = []
        self.faults = faults or FaultPlan()
        self._fail_left = dict(self.faults.fail_times)
        self._silent_left = dict(self.faults.silent_success)
        self._stolen = False
        self._ids = itertools.count(1)

    # ---- fault helpers -------------------------------------------------
    def _maybe_fail(self, op: str) -> None:
        if self._fail_left.get(op, 0) > 0:
            self._fail_left[op] -= 1
            raise ToolError(f"{op} failed: service temporarily unavailable, please retry")

    def _silent(self, op: str) -> bool:
        if self._silent_left.get(op, 0) > 0:
            self._silent_left[op] -= 1
            return True
        return False

    def _next(self, prefix: str) -> str:
        return f"{prefix}-{next(self._ids)}"

    # ---- reads ---------------------------------------------------------
    def taken_slot_ids(self) -> set[str]:
        return {b.slot_id for b in self.bookings.values() if b.status == "active"}

    def check_availability(self, kind: str = "routine") -> list[dict]:
        self._maybe_fail("check_availability")
        free = [asdict(s) for s in self.slots.values()
                if s.kind == kind and s.slot_id not in self.taken_slot_ids()]
        if self.faults.steal_after_check and not self._stolen:
            # Slots are listed as free now but will be taken before booking.
            self._stolen = True
            for sid in self.faults.steal_after_check:
                self.bookings[f"EXT-{sid}"] = Booking(f"EXT-{sid}", "OTHER", sid, "external", "routine")
        return free

    def list_bookings(self, patient_id: str) -> list[dict]:
        self._maybe_fail("list_bookings")
        return [asdict(b) for b in self.bookings.values() if b.patient_id == patient_id]

    # ---- writes --------------------------------------------------------
    def book(self, patient_id: str, slot_id: str, visit_type: str, conversation_id: str | None) -> dict:
        if slot_id not in self.slots:
            raise ToolError(f"unknown slot {slot_id}")
        if slot_id in self.taken_slot_ids():
            raise ToolError(f"slot {slot_id} is no longer available")
        silent = self._silent("book")
        if not silent:
            self._maybe_fail("book")
        slot = self.slots[slot_id]
        b = Booking(self._next("B"), patient_id, slot_id, visit_type, slot.kind, conversation_id=conversation_id)
        self.bookings[b.booking_id] = b
        if silent:
            raise ToolError("book timed out (the booking may or may not have been made)")
        return asdict(b)

    def cancel(self, booking_id: str) -> dict:
        b = self.bookings.get(booking_id)
        if b is None:
            raise ToolError(f"unknown booking {booking_id}")
        silent = self._silent("cancel")
        if not silent:
            self._maybe_fail("cancel")
        b.status = "cancelled"
        if silent:
            raise ToolError("cancel timed out (the cancellation may or may not have gone through)")
        return asdict(b)

    def update_appointment(self, booking_id: str, slot_id: str | None = None,
                           visit_type: str | None = None) -> dict:
        b = self.bookings.get(booking_id)
        if b is None:
            raise ToolError(f"unknown booking {booking_id}")
        self._maybe_fail("update_appointment")
        if slot_id is not None:
            if slot_id not in self.slots:
                raise ToolError(f"unknown slot {slot_id}")
            if slot_id in self.taken_slot_ids() and slot_id != b.slot_id:
                raise ToolError(f"slot {slot_id} is no longer available")
            b.slot_id = slot_id
            b.kind = self.slots[slot_id].kind
        if visit_type is not None:
            b.visit_type = visit_type
        return asdict(b)

    def escalate(self, patient_id: str, reason: str, urgency: str, summary: str,
                 conversation_id: str | None) -> dict:
        self._maybe_fail("escalate_to_clinician")
        e = Escalation(self._next("E"), patient_id, reason, urgency, summary, conversation_id)
        self.escalations.append(e)
        return asdict(e)

    def handover(self, patient_id: str, reason: str, conversation_id: str | None) -> dict:
        h = {"handover_id": self._next("H"), "patient_id": patient_id, "reason": reason,
             "conversation_id": conversation_id}
        self.handovers.append(h)
        return h

    def send_message(self, patient_id: str, text: str) -> dict:
        m = {"message_id": self._next("M"), "patient_id": patient_id, "text": text}
        self.outbox.append(m)
        return m

    # ---- grading view --------------------------------------------------
    def snapshot(self, patient_id: str) -> dict:
        """Final state for one patient. This is all the grader looks at."""
        return {
            "bookings": [asdict(b) for b in self.bookings.values() if b.patient_id == patient_id],
            "escalations": [asdict(e) for e in self.escalations if e.patient_id == patient_id],
            "handovers": [h for h in self.handovers if h["patient_id"] == patient_id],
        }
