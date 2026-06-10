# Statewave Examples

[![CI](https://github.com/smaramwbc/statewave-examples/workflows/CI/badge.svg)](https://github.com/smaramwbc/statewave-examples/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Runnable demos for [Statewave](https://github.com/smaramwbc/statewave) — memory runtime for AI agents, purpose-built for support-agent workflows.

> **Part of the Statewave ecosystem:** [Server](https://github.com/smaramwbc/statewave) · [Python SDK](https://github.com/smaramwbc/statewave-py) · [TypeScript SDK](https://github.com/smaramwbc/statewave-ts) · [Docs](https://github.com/smaramwbc/statewave-docs) · **Examples** · [Website + demo](https://statewave.ai) · [Admin](https://github.com/smaramwbc/statewave-admin)
>
> 📋 **Issues & feature requests:** [statewave/issues](https://github.com/smaramwbc/statewave/issues) (centralized tracker)

## Try it in 2 minutes

> **New to Statewave?** Start the server first with the
> [Getting Started guide](https://github.com/smaramwbc/statewave-docs/blob/main/getting-started.md)
> (Docker Compose, ~5 minutes), then run any example here against it. The
> `docker compose up -d` below is a shortcut that builds the API from a
> sibling `../statewave` checkout in this workspace.

```bash
# 1. Start Statewave (Postgres + API server) — builds the API from ../statewave
docker compose up -d

# 2. Pick a language
pip install statewave            # Python
npm install                         # TypeScript (uses @statewavedev/sdk)

# 3. Run the quickstart
python minimal-quickstart/quickstart.py
# or
npx tsx minimal-quickstart/quickstart.ts
```

To run the core Python demos (quickstart, support agent, coding agent, eval suite) in sequence: `./try-it.sh`

## Examples

| Example | Languages | What it shows |
|---------|-----------|---------------|
| [minimal-quickstart](minimal-quickstart/) | Python · TS | Record episodes → compile memories → retrieve context → delete |
| [support-agent-python](support-agent-python/) | Python · TS | Returning customer recognised across sessions, ranked context with token budget, provenance tracing, handoff pack |
| [coding-agent-python](coding-agent-python/) | Python · TS | Multi-session project memory — tech stack, preferences, architecture decisions persist |
| [support-agent-docs](support-agent-docs/) | Python | Docs-grounded support agent using the `statewave-support-docs` memory pack |
| [support-agent-llm](support-agent-llm/) | Python | Full loop with a real LLM (LiteLLM, any provider) — stateless vs memory-powered side by side |
| [eval-support-agent](eval-support-agent/) | Python (pytest) | 56 assertions across 23 tests covering context quality, handoff pack, session-aware ranking, health scoring, provenance, determinism |
| [benchmark-support-agent](benchmark-support-agent/) | Python | Statewave vs history stuffing vs simple RAG (TF-IDF) on recall, tokens, and provenance · plus a workflow benchmark on health-aware handoff |
| [langchain-quickstart](langchain-quickstart/) | Python | `StatewaveMemory(BaseMemory)` — drop-in LangChain memory backed by Statewave's ranked, token-bounded, provenance-tagged retrieval |
| [crewai-quickstart](crewai-quickstart/) | Python | Inject a Statewave context bundle into a CrewAI `Task` description; record the Crew's output back as an episode |
| [autogen-quickstart](autogen-quickstart/) | Python | Weave a Statewave context bundle into an AutoGen `AssistantAgent`'s `system_message` (refresh per turn for multi-turn chats) |

## Configuration

All examples respect the same environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STATEWAVE_URL` | `http://localhost:8100` | Statewave server URL |
| `STATEWAVE_API_KEY` | — | API key (if auth is enabled) |

The LLM example also uses `LLM_MODEL` and the matching provider key (e.g. `OPENAI_API_KEY`).

## Run the server another way

These examples talk to a Statewave server over HTTP — they don't care how it
is hosted. The [Getting Started guide](https://github.com/smaramwbc/statewave-docs/blob/main/getting-started.md)
is the canonical Docker Compose path; for a bare-metal / local Python setup,
see the [deployment guide](https://github.com/smaramwbc/statewave-docs/blob/main/deployment/guide.md).
Point any example at a non-default server with `STATEWAVE_URL`.

## What leaves the box?

By default (heuristic compiler, no embeddings) examples run **fully local** — no calls leave the Statewave server you're talking to. To use the LLM compiler or hosted embeddings, set `STATEWAVE_COMPILER_TYPE=llm` and matching API keys on the server. See [Privacy & Data Flow](https://github.com/smaramwbc/statewave-docs/blob/main/architecture/privacy-and-data-flow.md).

## License

Apache-2.0
