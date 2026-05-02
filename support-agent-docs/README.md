# Support Agent (docs-grounded)

A demo showing how a Statewave-powered support agent answers product questions using **only the official Statewave documentation** as its knowledge base — no source code, no hardcoded Q&A, no fabricated facts.

This is the "out of the box" support experience that ships with Statewave: a default memory pack built from `statewave-docs/` via the real `episodes → compile → memories` pipeline.

## What this demo shows

| Capability | How it's demonstrated |
|---|---|
| **Docs-grounded retrieval** | Every answer is sourced from the curated docs corpus, ranked and token-bounded by Statewave's existing context API |
| **Provenance / citations** | Each retrieved memory traces back to a specific doc path and section heading |
| **Three response modes** | Documented fact · Best-effort suggestion · Out of scope (user-specific or not in docs) |
| **Honest "I don't know"** | Demonstrates the agent refusing to speculate about live deployment state |
| **No source-code knowledge** | The pack contains zero source-code-derived content — only the published docs |

## Prerequisites

1. **Statewave server running** (see `../minimal-quickstart/` if you haven't set this up).

2. **Bootstrap the default docs pack** — this is the one-time step that turns `statewave-docs/` into ingestible episodes and compiles them into memories:

```bash
cd ../../statewave
python -m scripts.bootstrap_docs_pack
```

You should see `~178 sections → ~N memories` (depending on docs version).

3. **Install the Python SDK:**

```bash
pip install statewave-py
```

## Run

```bash
python support_agent_docs.py
```

## What happens

The demo asks four representative questions and, for each, shows what Statewave returned and how the agent should answer:

1. **Documented fact** — *"What database does Statewave use?"* → answered with a citation to the architecture overview.
2. **Documented fact (deployment)** — *"How do I deploy on Fly.io?"* → answered from `deployment/guide.md`.
3. **Best-effort suggestion** — *"Slow compile times — any guidance?"* → docs cover compiler modes and scaling, agent suggests directions grounded in those docs.
4. **Out of scope** — *"Why is my instance returning 503s?"* → the agent must say it cannot know live deployment state and route to `SUPPORT.md`.

The actual LLM call is stubbed out so the demo runs without an API key; see `../support-agent-llm/` for a wired-up variant. The point of this demo is the **retrieval + citation + grounding** layer that would sit underneath any LLM you choose.

## Refreshing the pack

Whenever `statewave-docs` changes, rebuild from scratch:

```bash
cd ../../statewave
python -m scripts.bootstrap_docs_pack --purge
```

## What this agent **does not** know

By design:

- ❌ Anything about your specific deployment (env vars, instance health, recent ops events)
- ❌ Live GitHub issues or roadmap items not in the docs
- ❌ Source-code-only details that aren't documented
- ❌ Anything in ADRs, the changelog, or speculative roadmap entries (those are excluded from the pack — see `statewave-docs/default-support-docs-pack.md`)

This is the right behavior. If your support agent needs to know live system state, layer a customer-specific subject on top — Statewave's context API supports merging context from multiple subjects in your application code.
