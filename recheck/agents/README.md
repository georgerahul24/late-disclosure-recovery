# recheck/agents/ (LLM agents)

| File | What it does |
|---|---|
| `client.py` | `ChatClient`: a stdlib-only OpenAI-compatible client for `/v1/chat/completions` with tools. It works with Ollama and vLLM. It parses `tool_calls`, and also Qwen's `<tool_call>` tags if a server leaves them in the text. It counts calls and tokens. It retries 3 times on network errors. |
| `prompts.py` | All system prompts. `PLAIN` is the base. `SAFETY`, `LABEL` and `RECHECK` (plus its ablation variants) are appended. `NOTE_INSTRUCTION` is appended to every condition. |
| `llm_agent.py` | `LLMAgent(condition, client, detector)`, a ReAct loop. `CONDITIONS` maps each condition name to an `AgentConfig`. `parse_note` strips the `NOTE: {json}` line. |

## Conditions

| Name | Detector | Ledger in context | Retrieval | Read-back step | Other |
|---|---|---|---|---|---|
| `plain` | - | - | yes (tools exist, no instruction) | - | |
| `safety` | - | - | yes | - | + "escalate emergencies" |
| `plain_label` | label each turn | - | yes | - | isolates the detection gain |
| `recheck` | label each turn | yes | yes | yes | 4-step procedure |
| `hybrid` | label | yes | yes | yes | + deterministic invariant after each turn |
| `recheck_no_detector` | - | yes | yes | yes | |
| `recheck_detector_tool` | as an optional tool | yes | yes | yes | |
| `recheck_no_retrieval` | label | yes | **no search_record** | yes | |
| `recheck_full_record` | label | yes | `get_patient_record(full=true)` instead | yes | |
| `recheck_no_ledger` | label | **no** | yes | yes | re-check step removed |
| `recheck_no_readback` | label | yes | yes | **no** | |
| `recheck_single_pass` | label | yes | yes | yes | only one tool round per turn |

## How a turn works

1. The user content is `Patient: <msg>`, plus a `[Detector] label=... score=...` line if the condition uses one, plus an `[Action ledger]` block if it uses one.
2. The agent loops for up to `max_steps` (8) model calls. If the model returns tool calls, they run through the harness and the results go back as `role: tool` messages (truncated to 4000 characters). If the model returns text, the turn ends.
3. The NOTE is parsed and stripped. If parsing fails, the note is `None` and the failure is counted (`note_parse_failures` in the run output). Many failures make stage 1/2 attribution weaker; look at this number.

## Gotchas

- Ollama's default context is too small. The server must run with `OLLAMA_CONTEXT_LENGTH=8192` or more; the SLURM job sets this.
- Temperature is 0 and `seed` is passed. Ollama is still not perfectly deterministic across batch sizes, so seeds 0/1/2 give the variance estimate.
- `escalate_to_clinician` with a reason starting "handover" also logs a hand-over.
- The harness drops unknown tool arguments (logged as `dropped_args`) instead of failing.
