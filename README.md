# Statewave Examples

Runnable examples demonstrating Statewave capabilities using official SDKs.

## Prerequisites

A running Statewave instance:

```bash
cd ../statewave
docker compose up db -d
pip install -e ".[dev]"
alembic upgrade head
python -m server.main
```

## Examples

| Example | Language | Description |
|---------|----------|-------------|
| [minimal-quickstart](minimal-quickstart/) | Python | Ingest, compile, retrieve context |

## License

Apache-2.0
