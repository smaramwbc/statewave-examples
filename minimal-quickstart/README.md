# Minimal Quickstart

The core Statewave loop in ~50 lines: record episodes → compile memories → retrieve a context bundle → delete.

## Run

```bash
# Requires Statewave server at http://localhost:8100
pip install statewave
python quickstart.py
# or
npx tsx quickstart.ts
```

## What leaves the box?

By default (heuristic compiler, no embeddings) this example runs **fully local** — no calls leave the Statewave server. To use the LLM compiler or hosted embeddings, configure `STATEWAVE_COMPILER_TYPE=llm` (and provider keys) on the server. See [Privacy & Data Flow](https://github.com/smaramwbc/statewave-docs/blob/main/architecture/privacy-and-data-flow.md).
