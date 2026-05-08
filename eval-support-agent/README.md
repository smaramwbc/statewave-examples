# Support Agent Eval Suite

Pytest-based evals that prove Statewave produces correct, ranked, traceable context for support-agent scenarios. The tests run against a live Statewave server (no mocks).

## What's covered

| File | Scenario | Asserts |
|------|----------|---------|
| `test_support_context.py` | Returning enterprise customer, 3 sessions | identity recall, preference recall, history recall, token-budget respected, provenance traces, idempotent compile, memory-count sanity |
| `test_handoff.py` | 3 sessions with 2 resolved + 1 open issue | active-issue extraction, customer facts surfaced, resolution deprioritization, signal preserved, provenance, determinism |
| `test_support_advanced.py` | 4 sessions with a recurring billing-gateway timeout | session-aware ranking, repeat-issue detection, health endpoint shape, health-aware handoff, resolution-aware ranking, compactness, determinism, provenance |

## Run

```bash
# Requires Statewave server at http://localhost:8100
pip install statewave httpx pytest

pytest -v                                    # all evals
pytest test_support_context.py               # one file
pytest -k handoff                            # by keyword
```

## Why this matters

Memory quality is measurable, not anecdotal. Run the suite against any Statewave deployment to validate the context bundle, the handoff pack, and the health endpoint shape. The tests intentionally sit at the public API boundary, so they double as integration coverage.

## SDK gap (current limitation)

`session_id` on episode creation, on `get_context`, and the `/v1/handoff` and `/v1/resolutions` endpoints aren't on the SDK yet. The conftest helper drops down to raw httpx for those calls — see [`conftest.py`](conftest.py).
