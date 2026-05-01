# Minimal Quickstart

Demonstrates the core Statewave loop: record → compile → context.

## Run

```bash
pip install statewave-py
python quickstart.py
```

Requires a running Statewave server at `http://localhost:8100`.

## What leaves the box?

By default (heuristic compiler, no embeddings) this example runs **fully local** — no external API calls beyond the Statewave server you're talking to. To use the LLM compiler or hosted embeddings, set `STATEWAVE_COMPILER_TYPE=llm` (and matching API keys) on the server, and content will be sent to the provider you configure. See [Privacy & Data Flow](https://github.com/smaramwbc/statewave-docs/blob/main/architecture/privacy-and-data-flow.md).
