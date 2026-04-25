# Statewave Examples

Runnable examples demonstrating [Statewave](https://github.com/smaramwbc/statewave) — memory runtime for AI agents and applications.

See also: [Python SDK](https://github.com/smaramwbc/statewave-py) · [TypeScript SDK](https://github.com/smaramwbc/statewave-ts) · [Docs](https://github.com/smaramwbc/statewave-docs)

## Prerequisites

A running Statewave instance:

```bash
cd ../statewave
docker compose up db -d
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn server.app:app --host 0.0.0.0 --port 8100
```

Install the Python SDK:

```bash
pip install statewave-py
```

## Examples

| Example | Language | Description |
|---------|----------|-------------|
| [minimal-quickstart](minimal-quickstart/) | Python | Basic record → compile → context loop |
| [support-agent-python](support-agent-python/) | Python | Polished demo: returning customer, ranked context, provenance, stateless vs. Statewave comparison |
| [coding-agent-python](coding-agent-python/) | Python | Coding assistant demo: project context recall across sessions |

All examples support optional authentication via `STATEWAVE_API_KEY` and `STATEWAVE_URL` environment variables.

## License

Apache-2.0
