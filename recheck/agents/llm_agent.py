"""ReAct-style tool-calling LLM agent, configurable into every LLM condition.

One class, many configs (see CONDITIONS below and agents/README.md):

    plain          booking prompt only
    safety         + "escalate emergencies"
    plain_label    plain + detector label each turn (no ledger/retrieval/verify)
    recheck        detector label + ledger + ground/re-check/repair/verify procedure
    hybrid         recheck + deterministic invariant after every turn
    recheck_no_detector, recheck_detector_tool, recheck_no_retrieval,
    recheck_full_record, recheck_no_ledger, recheck_no_readback,
    recheck_single_pass                          (one ablation each)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..runner import AgentTurn, EpisodeContext
from ..tools import TOOL_SCHEMAS, ToolHarness
from . import prompts
from .client import ChatClient


@dataclass
class AgentConfig:
    system: str
    detector_label: bool = False  # inject [Detector] line each turn
    detector_tool: bool = False  # detector as an optional tool instead
    ledger: bool = False  # inject [Action ledger] each turn
    retrieval: bool = True  # search_record / search_policy available
    full_record: bool = False  # get_patient_record(full=True) allowed
    invariant: bool = False  # Hybrid: deterministic invariant after each turn
    single_pass: bool = False  # at most one tool-calling round per turn
    max_steps: int = 8  # model calls per patient turn


CONDITIONS: dict[str, AgentConfig] = {
    "plain": AgentConfig(prompts.PLAIN + prompts.NOTE_INSTRUCTION),
    "safety": AgentConfig(prompts.PLAIN + prompts.SAFETY + prompts.NOTE_INSTRUCTION),
    "plain_label": AgentConfig(prompts.PLAIN + prompts.LABEL + prompts.NOTE_INSTRUCTION, detector_label=True),
    "recheck": AgentConfig(prompts.PLAIN + prompts.RECHECK + prompts.NOTE_INSTRUCTION, detector_label=True, ledger=True),
    "hybrid": AgentConfig(prompts.PLAIN + prompts.RECHECK + prompts.NOTE_INSTRUCTION, detector_label=True, ledger=True,
                          invariant=True),
    "recheck_no_detector": AgentConfig(prompts.PLAIN + prompts.RECHECK.replace(
        "Each patient message comes with a [Detector] line from an automatic symptom screener (label: urgent, head, hypo, foot or benign, with a score), and an",
        "Each patient message comes with an") + prompts.NOTE_INSTRUCTION, ledger=True),
    "recheck_detector_tool": AgentConfig(prompts.PLAIN + prompts.RECHECK.replace(
        "Each patient message comes with a [Detector] line from an automatic symptom screener (label: urgent, head, hypo, foot or benign, with a score), and an",
        "You can run a symptom screener with the classify_message tool. Each patient message comes with an")
        + prompts.NOTE_INSTRUCTION, detector_tool=True, ledger=True),
    "recheck_no_retrieval": AgentConfig(prompts.PLAIN + prompts.RECHECK_NO_RETRIEVAL + prompts.NOTE_INSTRUCTION,
                                        detector_label=True, ledger=True, retrieval=False),
    "recheck_full_record": AgentConfig(prompts.PLAIN + prompts.RECHECK_FULL_RECORD + prompts.NOTE_INSTRUCTION,
                                       detector_label=True, ledger=True, retrieval=False, full_record=True),
    "recheck_no_ledger": AgentConfig(prompts.PLAIN + prompts.RECHECK_NO_LEDGER + prompts.NOTE_INSTRUCTION,
                                     detector_label=True, ledger=False),
    "recheck_no_readback": AgentConfig(prompts.PLAIN + prompts.RECHECK_NO_READBACK + prompts.NOTE_INSTRUCTION,
                                       detector_label=True, ledger=True),
    "recheck_single_pass": AgentConfig(prompts.PLAIN + prompts.RECHECK + prompts.NOTE_INSTRUCTION,
                                       detector_label=True, ledger=True, single_pass=True),
}

_NOTE = re.compile(r"^\s*NOTE:\s*(\{.*\})\s*$", re.M)


def parse_note(text: str) -> tuple[str, dict | None]:
    """Split the reply into (patient-visible text, note dict or None)."""
    m = None
    for m in _NOTE.finditer(text):
        pass
    if m is None:
        return text.strip(), None
    visible = (text[:m.start()] + text[m.end():]).strip()
    try:
        note = json.loads(m.group(1))
        return visible, note if isinstance(note, dict) else None
    except json.JSONDecodeError:
        return visible, None


class LLMAgent:
    def __init__(self, condition: str, client: ChatClient, detector=None, name: str | None = None):
        self.condition = condition
        self.cfg = CONDITIONS[condition]
        self.client = client
        self.detector = detector
        self.name = name or f"llm[{condition}]"
        if (self.cfg.detector_label or self.cfg.detector_tool) and detector is None:
            raise ValueError(f"{condition} needs a detector")

    def reset(self, ctx: EpisodeContext) -> None:
        self.ctx = ctx
        if hasattr(self.detector, "set_context"):  # oracle detector only
            self.detector.set_context(ctx.oracle_scenario, ctx.episode)
        self.messages: list[dict] = [{"role": "system", "content": self.cfg.system}]
        self.n_model_calls = 0
        self.parse_failures = 0

    def _tools(self) -> list[dict]:
        tools = []
        for t in TOOL_SCHEMAS:
            if not self.cfg.retrieval and t["name"] in ("search_record",):
                continue
            if t["name"] == "get_patient_record" and self.cfg.full_record:
                tools.append(prompts.FULL_RECORD_TOOL)
                continue
            tools.append(t)
        if self.cfg.detector_tool:
            tools.append(prompts.DETECTOR_TOOL)
        return tools

    def _user_content(self, message: str, tools: ToolHarness) -> str:
        parts = [f"Patient: {message}"]
        if self.cfg.detector_label:
            label, score = self.detector.predict(message)
            parts.append(f"[Detector] label={label} score={score:.2f}")
        if self.cfg.ledger:
            entries = tools.ledger.to_list()
            if entries:
                lines = [f"- turn {e['turn']}: {e['action']} {e['booking_id']} {json.dumps(e['detail'])}" for e in entries]
                parts.append("[Action ledger]\n" + "\n".join(lines))
            else:
                parts.append("[Action ledger] (no booking actions yet)")
        return "\n".join(parts)

    def _exec(self, call: dict, tools: ToolHarness) -> dict:
        name, args = call["name"], dict(call["arguments"] or {})
        if name == "classify_message" and self.cfg.detector_tool:
            label, score = self.detector.predict(args.get("text", ""))
            return {"ok": True, "result": {"label": label, "score": round(score, 3)}}
        if name == "search_record" and not self.cfg.retrieval:
            return {"ok": False, "error": "tool not available"}
        if "__unparsed__" in args:
            return {"ok": False, "error": "could not parse arguments as JSON"}
        if name == "escalate_to_clinician" and str(args.get("reason", "")).lower().startswith("handover"):
            tools.call("hand_over", reason=args.get("reason", "handover"))
        return tools.call(name, **args)

    def _enforce_invariant(self, tools: ToolHarness) -> None:
        escalated = any(c.name in ("escalate_to_clinician", "hand_over") and c.ok for c in tools.calls)
        if escalated:
            for b in tools.ledger.open_bookings():
                if b.get("kind", "routine") == "routine":
                    tools.call("cancel", booking_id=b["booking_id"])

    def respond(self, message: str, tools: ToolHarness) -> AgentTurn:
        self.messages.append({"role": "user", "content": self._user_content(message, tools)})
        tool_list = self._tools()
        text = ""
        rounds = 0
        for step in range(self.cfg.max_steps):
            allow_tools = not (self.cfg.single_pass and rounds >= 1)
            res = self.client.chat(self.messages, tool_list if allow_tools else None)
            self.n_model_calls += 1
            if res.tool_calls and allow_tools:
                rounds += 1
                self.messages.append({"role": "assistant", "content": res.content or "",
                                      "tool_calls": [{"id": c["id"], "type": "function",
                                                      "function": {"name": c["name"],
                                                                   "arguments": json.dumps(c["arguments"])}}
                                                     for c in res.tool_calls]})
                for c in res.tool_calls:
                    out = self._exec(c, tools)
                    self.messages.append({"role": "tool", "tool_call_id": c["id"], "name": c["name"],
                                          "content": json.dumps(out, default=str)[:4000]})
                continue
            text = res.content or ""
            self.messages.append({"role": "assistant", "content": text})
            break
        else:
            text = "Sorry, I need to pass this to a member of staff."
            self.messages.append({"role": "assistant", "content": text})
        if self.cfg.invariant:
            self._enforce_invariant(tools)
        visible, note = parse_note(text)
        if note is None:
            self.parse_failures += 1
        return AgentTurn(visible, note)
