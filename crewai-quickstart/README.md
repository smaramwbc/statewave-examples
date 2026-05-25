# CrewAI Quickstart

A CrewAI agent answers a customer question grounded in a Statewave-backed account memory. The integration is two helpers — no framework subclassing, no glue code in the SDK.

## What this demo shows

| Capability | How it's demonstrated |
|---|---|
| **Task-relevant context injection** | `build_task_description` prepends a Statewave bundle to the Task description before the Crew runs |
| **Output recorded back** | `record_crew_output` writes the Crew's reply as a Statewave episode so the next run benefits |
| **No CrewAI memory plumbing** | Statewave is a drop-in replacement for ad-hoc backstory padding or scratch files |
| **Provenance preserved** | The bundle the agent sees is the same provenance-tagged context the rest of Statewave returns |

## Prerequisites

A running Statewave server at `http://localhost:8100`:

```bash
docker compose up -d         # from statewave-examples/
```

Dependencies (framework pinned in the example only, not in the core SDK):

```bash
pip install "statewave>=0.10.0" crewai
export OPENAI_API_KEY=sk-...
```

## Run

```bash
python crewai_quickstart.py
```

The demo seeds Globex's account context (plan, renewal, contact), compiles it, then runs a one-task Crew that drafts a renewal reply. Statewave context is injected into the Task description; the Crew's output is recorded back.

## The adapter

[`adapter.py`](adapter.py) is two small functions, dependency-free:

- `build_task_description(client, subject_id, task_description, *, max_tokens=1000)` — fetch a task-relevant Statewave bundle and prepend it to `task_description`, separated by a `---` rule. Pass the result to `Task(description=...)`.
- `record_crew_output(client, subject_id, task_description, output, *, crew_name="crewai")` — record one Crew run as an episode with payload `{ "task": ..., "output": ... }`.

The adapter doesn't import CrewAI, so it composes with any version. Drop these two calls around your existing Crew and Statewave-backed memory is in.

## Smoke test

The adapter's wiring is covered by mock-based tests — no CrewAI install needed:

```bash
pytest test_adapter.py
```

## See also

- [Statewave Python SDK](https://github.com/smaramwbc/statewave-py) — the underlying `StatewaveClient`.
- [Getting started](https://github.com/smaramwbc/statewave-docs/blob/main/getting-started.md) — bring a server up in 5 minutes.
- [`../langchain-quickstart/`](../langchain-quickstart/) — same pattern, BaseMemory-shaped, for LangChain.
- [`../autogen-quickstart/`](../autogen-quickstart/) — same pattern, system_message-shaped, for AutoGen.
