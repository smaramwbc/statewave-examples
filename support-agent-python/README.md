# Support Agent Demo

A returning customer is recognised across sessions: profile facts, preferences, and prior issues are retrieved within a token budget and traced back to the episodes that produced them. A handoff pack shows what an escalation hand-off looks like.

## What this demo shows

| Capability | How it's demonstrated |
|---|---|
| **Profile facts remembered** | Agent recalls name, company, plan, preferences from a prior session |
| **Relevant history retrieved** | Prior billing issue surfaces when the user returns with a related question |
| **Token-bounded, ranked context** | Context fits within `max_tokens`; highest-value facts and summaries survive |
| **Provenance** | Each fact traces back to its source episode |
| **Idempotent compilation** | Recompiling produces 0 new memories |
| **Handoff context pack** | Compact escalation brief via `/v1/handoff` |

For a real model in the loop, see [`../support-agent-llm/`](../support-agent-llm/).

## Prerequisites

A running Statewave server at `http://localhost:8100`:

```bash
docker compose up -d         # from statewave-examples/
```

## Run

```bash
pip install statewave-py httpx
python support_agent.py
# or
npx tsx support_agent.ts
```
