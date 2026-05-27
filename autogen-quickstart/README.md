# AutoGen Quickstart

An AutoGen `AssistantAgent` answers a returning user grounded in a Statewave-backed memory. The integration is two helpers — both wrap AutoGen's `system_message`, which keeps the adapter framework-version-agnostic.

## What this demo shows

| Capability | How it's demonstrated |
|---|---|
| **Memory in `system_message`** | `build_system_message` prepends a Statewave bundle to the agent's static role/instructions |
| **Refreshable per turn** | `update_system_message` re-fetches a fresh bundle before the next turn — useful for multi-turn chats |
| **Turn-by-turn capture** | `record_turn` writes the (user, assistant) pair back as an episode |
| **No AutoGen subclassing** | All helpers are duck-typed; works with `AssistantAgent`, `ConversableAgent`, or any agent exposing `update_system_message` |

## Prerequisites

A running Statewave server at `http://localhost:8100` — the
[`docker-compose.yml`](../docker-compose.yml) in the examples root brings up
Postgres 16 + pgvector and the API together:

```bash
docker compose up -d         # from statewave-examples/
```

Dependencies (framework pinned in the example only, not in the core SDK).
This example targets the classic **AutoGen 0.2 API**
(`from autogen import AssistantAgent`); the unpinned `pyautogen` on PyPI now
resolves to a 0.10.x package with a different import surface, so pin the 0.2
line:

```bash
pip install "statewave>=0.10.0" "pyautogen==0.2.*"
export OPENAI_API_KEY=sk-...
```

The newer `autogen-agentchat` (0.4+) split exposes a different API; the same
Statewave pattern (build the system_message, record turns) maps over directly.

## Run

```bash
python autogen_quickstart.py
```

The demo seeds Alice's profile, compiles it, then asks an `AssistantAgent` about her plan and contact channel — with Statewave context already woven into the system_message.

## The adapter

[`adapter.py`](adapter.py) is three small functions, dependency-free:

- `build_system_message(client, subject_id, base_prompt, *, task=..., max_tokens=1000)` — build a system_message string with a Statewave bundle on top and `base_prompt` (the agent's role/instructions) below.
- `update_system_message(agent, client, subject_id, base_prompt, *, task, max_tokens=1000)` — call mid-chat to refresh the agent's system_message with a fresh, task-biased bundle.
- `record_turn(client, subject_id, user_msg, assistant_msg, *, agent_name="autogen")` — record one user/assistant turn as a Statewave episode.

## Smoke test

The adapter's wiring is covered by mock-based tests — no AutoGen install needed:

```bash
pytest test_adapter.py
```

## See also

- [Statewave Python SDK](https://github.com/smaramwbc/statewave-py) — the underlying `StatewaveClient`.
- [Getting started](https://github.com/smaramwbc/statewave-docs/blob/main/getting-started.md) — bring a server up in 5 minutes.
- [`../langchain-quickstart/`](../langchain-quickstart/) — same pattern, `BaseMemory`-shaped, for LangChain.
- [`../crewai-quickstart/`](../crewai-quickstart/) — same pattern, Task-shaped, for CrewAI.
