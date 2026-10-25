# Late-Disclosure Recovery in Stateful Clinical Agents

This repo holds the code and docs for the LMA course project by George R., Arihant R. and Aditya P. (team "LEs & Arihant").

## The idea in one paragraph

A clinic chat agent books, changes and cancels appointments with tools. Sometimes a patient mentions a worrying symptom only after the agent has already booked a routine slot. For example: "Thanks, see you Thursday. One more thing, I hit my head yesterday." If that patient takes a blood thinner, the routine booking is now wrong. The agent has to notice the symptom, check the record, see that its own booking is now wrong, fix it, escalate to a clinician, and confirm the fix worked. We build (1) a **benchmark** that tests this and (2) a method called **RECHECK** that tries to do it well.

## Where to start

| If you are... | Read |
|---|---|
| A new agent or teammate picking up work | [`handoff.md`](handoff.md) first, then [`instructions.md`](instructions.md) and [`todo.md`](todo.md) |
| Running on the GPU cluster | [`instructions.md`](instructions.md) and [`cluster/README.md`](cluster/README.md) |
| Looking for the research plan | [`docs/proposal.pdf`](docs/proposal.pdf) and [`docs/README.md`](docs/README.md) |
| Looking for related work | [`papers.md`](papers.md) |
| Working on code | [`recheck/README.md`](recheck/README.md) |
| Working on scenarios or patients | [`data/README.md`](data/README.md) |

## Quick start

```bash
uv venv --python 3.12
uv pip install -e ".[ml,dev]"
uv run pytest -q                 # all tests should pass
uv run python scripts/run_pilot.py   # scripted-controller pilot on the dev fixtures
```

## Layout

```
docs/       proposal PDF, reviewer pointers, design notes, clinical sources
recheck/    the Python package (backend, tools, simulator, grader, controllers, detectors, agents)
data/       Synthea patients, eval scenarios, detector seeds, clinic policy, dev fixtures (tests only)
scripts/    command line entry points (data build, pilot, LLM runs, detector training)
cluster/    SLURM + Ollama scripts for the ada cluster
tests/      pytest tests
instructions.md  standing rules and cluster how-to
papers.md   literature review
todo.md     the live task list
handoff.md  current state of the project for whoever picks it up next
```

Every folder has its own `README.md` that explains what is inside and the rules for changing it.
