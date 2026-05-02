# Statewave Examples

Runnable demos showing what [Statewave](https://github.com/smaramwbc/statewave) does — memory runtime for AI agents, purpose-built for support-agent workflows.

> **Part of the Statewave ecosystem:** [Server](https://github.com/smaramwbc/statewave) · [Python SDK](https://github.com/smaramwbc/statewave-py) · [TypeScript SDK](https://github.com/smaramwbc/statewave-ts) · [Docs](https://github.com/smaramwbc/statewave-docs) · **Examples** · [Website + demo](https://statewave.ai) · [Admin](https://github.com/smaramwbc/statewave-admin)
>
> 📋 **Issues & feature requests:** [statewave/issues](https://github.com/smaramwbc/statewave/issues) (centralized tracker)

## Proof & Evaluation

| Asset | What it proves |
|-------|---------------|
| [eval-support-agent](eval-support-agent/) | Context quality eval — 7 tests, 14 assertions on identity, preferences, provenance, token budget |
| [eval-support-agent (handoff)](eval-support-agent/eval_handoff.py) | Handoff pack eval — 7 tests, 16 assertions on active issue surfacing, resolution deprioritization, health-aware handoff, compactness vs naive baseline |
| [eval-support-agent (advanced)](eval-support-agent/eval_support_advanced.py) | Advanced eval — 7 tests, 24 assertions on session-aware ranking, repeat-issue detection, health scoring, health-aware handoff, resolution ranking, determinism |
| [benchmark-support-agent](benchmark-support-agent/) | Statewave vs history stuffing vs naive RAG — recall, tokens, provenance comparison |
| [benchmark-support-agent (workflow)](benchmark-support-agent/benchmark_support_workflow.py) | Support workflow benchmark — 9 criteria comparing health, repeat-issue, session-aware, provenance capabilities vs naive (Statewave 9/9, Naive 2/9) |
| [support-agent-llm](support-agent-llm/) | Full LLM loop — Statewave context → LLM → side-by-side stateless vs memory response |

## Try it in 2 minutes

```bash
# 1. Start Statewave (Postgres + API server)
docker compose up -d

# 2. Install the SDK
pip install statewave-py

# 3. Run all demos
./try-it.sh
```

Or run individual examples:

```bash
python minimal-quickstart/quickstart.py        # 30 seconds — core loop
python support-agent-python/support_agent.py   # 1 minute — full agent demo
python coding-agent-python/coding_agent.py     # 1 minute — multi-session recall
```

## Examples

| Example | What it shows | Time |
|---------|--------------|------|
| [minimal-quickstart](minimal-quickstart/) | Record episodes → compile memories → retrieve context → delete | 30s |
| [support-agent-python](support-agent-python/) | Returning customer recognition, ranked context with token budget, provenance tracing, stateless vs. Statewave comparison | 1 min |
| [support-agent-docs](support-agent-docs/) | **Docs-grounded support agent** — uses the default `statewave-support-docs` memory pack (built from the official docs) to answer product questions with citations | 1 min |
| [support-agent-llm](support-agent-llm/) | **Full-loop with real LLM** — Statewave context → LLM → side-by-side stateless vs memory-powered response | 1 min |
| [coding-agent-python](coding-agent-python/) | Multi-session project memory — tech stack, preferences, and architecture decisions persist across sessions | 1 min |
| [eval-support-agent](eval-support-agent/) | **Context quality eval** — seeds support scenarios, asserts expected facts in retrieved context, reports pass/fail score | 30s |
| [benchmark-support-agent](benchmark-support-agent/) | **Comparison benchmark** — Statewave vs history stuffing vs simple RAG on recall, tokens, and provenance | 30s |

## What you'll see

**Minimal quickstart** — ingest two conversations, compile profile facts, retrieve a context bundle with token estimate:
```
Recording episodes...
Compiling memories...
  Created 3 memories
    [profile_fact] The user's name is Alice
    [profile_fact] The user works at Acme Corp
    [preference] The user prefers Python and uses VS Code

Retrieving context bundle...
  Token estimate: 147
```

**Support agent** — returning customer gets recognised across sessions, context is ranked by relevance:
```
SESSION 1: Alice introduces herself, reports a billing issue

SESSION 2: Alice returns days later — agent already knows:
  • Name: Alice Chen
  • Company: Globex Corporation (Enterprise plan)
  • Previous issue: billing discrepancy (resolved)
  → Agent responds with full context, no repetition needed
```

**Coding agent** — developer's project context persists across sessions:
```
SESSION 1: Bob describes Taskflow (FastAPI + SQLAlchemy + Postgres)

SESSION 2: Bob asks for help — agent already knows:
  • Project: Taskflow, Python FastAPI backend
  • Stack: SQLAlchemy, Postgres, Alembic, pytest
  • Decision: chose async SQLAlchemy for I/O-bound workload
  → Agent gives project-aware help immediately
```

## Configuration

All examples support environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STATEWAVE_URL` | `http://localhost:8100` | Statewave server URL |
| `STATEWAVE_API_KEY` | — | API key (if auth is enabled) |

## Alternative: manual server setup

If you prefer not to use Docker:

```bash
cd ../statewave
docker compose up db -d           # just the database
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn server.app:app --host 0.0.0.0 --port 8100
```

## License

Apache-2.0
