"""Minimal OpenAI-compatible chat client (stdlib only).

Works with Ollama (`ollama serve`, base_url http://host:11434/v1) and vLLM
(`vllm serve`, base_url http://host:8000/v1). No `openai` package needed, so
the cluster env stays small.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class ChatResult:
    content: str
    tool_calls: list[dict] = field(default_factory=list)  # [{"id", "name", "arguments": dict}]
    raw: dict | None = None
    usage: dict | None = None


_TOOL_TAG = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)


class ChatClient:
    def __init__(self, base_url: str, model: str, temperature: float = 0.0, seed: int = 0,
                 timeout: float = 300.0, max_tokens: int = 768, api_key: str = "none", json_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.json_mode = json_mode  # constrain output to one JSON object (judge); stops trailing prose
        self.n_calls = 0
        self.tokens_in = 0
        self.tokens_out = 0

    def chat(self, messages: list[dict], tools: list[dict] | None = None, retries: int = 3) -> ChatResult:
        body = {"model": self.model, "messages": messages, "temperature": self.temperature,
                "seed": self.seed, "max_tokens": self.max_tokens}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
        data = json.dumps(body).encode()
        last = None
        for attempt in range(retries):
            req = urllib.request.Request(f"{self.base_url}/chat/completions", data=data,
                                         headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {self.api_key}"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    out = json.loads(r.read())
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last = e
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"chat request failed after {retries} tries: {last}")
        self.n_calls += 1
        usage = out.get("usage") or {}
        self.tokens_in += usage.get("prompt_tokens", 0)
        self.tokens_out += usage.get("completion_tokens", 0)
        msg = out["choices"][0]["message"]
        content = msg.get("content") or ""
        calls = []
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function", {})
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    args = {"__unparsed__": args}
            calls.append({"id": tc.get("id") or f"call_{i}", "name": fn.get("name"), "arguments": args})
        if not calls:
            # Some servers leave Qwen's <tool_call> tags in the text.
            for i, m in enumerate(_TOOL_TAG.finditer(content)):
                try:
                    d = json.loads(m.group(1))
                    calls.append({"id": f"tag_{i}", "name": d.get("name"), "arguments": d.get("arguments") or {}})
                except json.JSONDecodeError:
                    pass
            if calls:
                content = _TOOL_TAG.sub("", content).strip()
        return ChatResult(content, calls, out, usage)
