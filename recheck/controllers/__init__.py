"""Scripted (non-LLM) controllers used in the feasibility pilot, plus the DSC.

    ScriptedController(detector, grounding, revision, readback, invariant)

Switches (proposal section 8):
    detector   any Detector (keyword / tfidf / oracle / lora later), or None
    grounding  "ignore"  record-dependent families are treated as benign
               "always"  record-dependent families are always treated as urgent
               "record"  check the record rules for this patient
    revision   "none" | "cancel" | "convert"  what to do with open routine bookings
    readback   after a repair, list_bookings; retry once; then hand over
    invariant  after every turn: if escalated, no routine booking may stay active

Named presets: book_only(), rule_gate(), dsc().
"""

from .scripted import ScriptedController, book_only, dsc, rule_gate

__all__ = ["ScriptedController", "book_only", "dsc", "rule_gate"]
