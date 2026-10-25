# recheck/ (the Python package)

Everything that runs an episode and grades it. Pure Python; the core needs no third-party packages. `scikit-learn` is only needed for the TF-IDF detector.

## Modules

| File | What it does | Key names |
|---|---|---|
| `records.py` | Patient record model (Synthea-shaped). Medications have start/stop dates; stopped ones are distractors. `facts()` flattens a record into retrievable text facts, each with a stable `fact_id`. All dates are relative to `REFERENCE_DATE` (2026-11-02). | `PatientRecord`, `MED_CLASSES`, `load_patients` |
| `rules.py` | Ground truth: is family X urgent for patient P? Also checks the exclusions that matched negatives must pass. | `evaluate(family, patient, severe)`, `FAMILIES` |
| `policy.py` | Clinic policy passages plus a tiny bag-of-words retriever (`lexical_search`), also used for record search. | `load_policy`, `lexical_search` |
| `scenarios.py` | Scenario schema, validation, and expansion into episodes (timing x phrasing x fault x seed). | `Scenario`, `Episode`, `expand_episodes`, `TIMINGS`, `FAULTS` |
| `backend.py` | Mock clinic backend: slots, bookings, escalations, hand-overs, outbox, and fault injection. `snapshot()` is all the grader reads. | `ClinicBackend`, `FaultPlan`, `ToolError` |
| `tools.py` | Per-conversation harness: the 10-tool allow-list, authority rules, the action ledger, and the call log. `call()` never raises. It drops unknown arguments and logs them. Also holds `TOOL_SCHEMAS` for LLMs. | `ToolHarness`, `ActionLedger`, `TOOL_SCHEMAS` |
| `simulator.py` | Rule-based, event-triggered patient (see docs/design.md section 2). | `PatientSimulator` |
| `runner.py` | Runs one episode or a suite. Defines the `Agent` protocol, `AgentTurn` and `EpisodeContext`. Maps fault names to `FaultPlan`s. | `run_episode`, `run_suite`, `fault_plan` |
| `grader.py` | End-state labels, the policy/strict/lenient schemes, routine completion, unsafe actions and stage attribution. | `grade_episode`, `classify_end_state` |
| `analysis.py` | Scenario-level means, bootstrap CIs, paired differences and contrast consistency. | `summarize`, `paired_diff` |
| `detectors/` | Keyword, TF-IDF and oracle detectors (LoRA planned). See its README. | |
| `controllers/` | Scripted pilot controllers and the DSC. See its README. | |
| `agents/` | LLM agents for every condition, plus an OpenAI-compatible client. See its README. | |

## Contracts you must not break

- **Agents touch the backend only through `ToolHarness.call`.** The one exception is `privileged_record()`, which is for deterministic controllers only.
- **`grade_episode` reads only** the final snapshot, the call log, the ledger, the transcript, the notes and the simulator's `disclosed_turn`. Never grade from agent text, except for the advice check.
- **The oracle detector** is the only thing allowed to read `EpisodeContext.oracle_scenario`.
- **Results must be deterministic** for scripted controllers. Tests rely on this.
- **If you add a tool**, add it to `TOOL_SCHEMAS`, add a `_t_<name>` method, decide whether it is state-changing, and update `docs/design.md`.

## Gotchas

- `Episode.episode_id` is built into the conversation id (`C-<episode_id>`). The grader rebuilds it, so do not change the format in one place only.
- `classify_end_state` counts escalations per patient, but bookings per conversation. The backend is fresh per episode, so this is safe.
- The `stolen` slot in the `slot_taken` fault belongs to patient "OTHER", so it never shows up in the patient's snapshot.
