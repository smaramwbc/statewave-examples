# LangChain Quickstart

A returning customer keeps their plan, preferences, and prior context across turns — delivered to a LangChain chain via a small `BaseMemory` subclass backed by Statewave.

## What this demo shows

| Capability | How it's demonstrated |
|---|---|
| **Drop-in LangChain memory** | `StatewaveMemory(BaseMemory)` plugs into any chain via the `memory=` kwarg |
| **Token-bounded, ranked context** | Each turn gets a fresh Statewave bundle sized to `max_tokens`, biased toward the current input |
| **Durable across runs** | `save_context` records every turn as an episode — restart the script and the model still knows you |
| **No vector DB plumbing** | Statewave's compile → retrieve loop replaces the usual "embed + Pinecone" stack inside the chain |
| **Provenance preserved** | Memory in the prompt is the same provenance-tagged bundle the rest of Statewave returns |

## Prerequisites

A running Statewave server at `http://localhost:8100`:

```bash
docker compose up -d         # from statewave-examples/
```

Dependencies (no framework deps are pinned in the core Statewave SDK — install them at the example level):

```bash
pip install "statewave>=0.10.0" langchain langchain-openai
export OPENAI_API_KEY=sk-...
```

## Run

```bash
python langchain_quickstart.py
```

The demo seeds Alice's plan and contact preference as episodes, compiles them into memories, and then asks a follow-up question. The chain pulls the right slice of memory via `StatewaveMemory` and the model answers grounded in it.

## The adapter

[`adapter.py`](adapter.py) is the entire integration — about 40 lines:

- `StatewaveMemory(BaseMemory)` — the LangChain memory class.
  - `load_memory_variables({"input": ...})` → fetches a Statewave bundle for the current input and exposes it as `{memory_key: <context>}` (default key: `statewave_context`).
  - `save_context(inputs, outputs)` → appends the (user, assistant) turn as a Statewave episode.
  - `clear()` is intentionally a no-op — Statewave is append-only, and accidentally dropping durable memory because a chain was reset is the wrong default. Call `client.delete_subject(subject_id)` explicitly when you really mean it.

Reference it in your prompt template via the `{statewave_context}` placeholder:

```python
prompt = PromptTemplate(
    input_variables=["statewave_context", "input"],
    template="{statewave_context}\n\nUser: {input}\nAssistant:",
)
```

## Smoke test

The adapter's wiring is covered by a small mock-based test — no LLM, no Statewave server, only LangChain installed:

```bash
pip install langchain
pytest test_adapter.py
```

## See also

- [Statewave Python SDK](https://github.com/smaramwbc/statewave-py) — the underlying `StatewaveClient`.
- [Getting started](https://github.com/smaramwbc/statewave-docs/blob/main/getting-started.md) — bring a server up in 5 minutes.
- [`../support-agent-python/`](../support-agent-python/) — the same retrieve-then-respond pattern without LangChain.
