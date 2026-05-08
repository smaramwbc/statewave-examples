# Support Agent Benchmarks

Two benchmarks against the same 8-episode customer scenario. Both run deterministically against a live Statewave server and exit non-zero if Statewave's headline claim doesn't hold.

## benchmark_support_context.py

Statewave vs history stuffing vs simple RAG (TF-IDF over the same messages).

For each approach we report:

- **Recall** — does the assembled context contain identity, preferences, and prior-issue keywords?
- **Tokens** — rough word-count estimate
- **Provenance** — can the output be traced back to source episodes?

History stuffing has everything by construction (5/5 recall) but no provenance and no ranking. RAG has whatever TF-IDF surfaces. Statewave has ranked + provenance — and how much recall depends on ranker tuning.

```bash
pip install statewave scikit-learn
python benchmark_support_context.py
```

## benchmark_support_workflow.py

Compares Statewave's `/v1/handoff` pack against a naïve "concatenate all messages" handoff for the same scenario. Eight criteria covering active-issue extraction, recurring-issue detection, health scoring, resolution-aware ranking, compactness, determinism, and provenance.

The naïve dump only ticks "compact" and "deterministic" by virtue of being trivial. Statewave needs the rest of the workflow to mean anything.

```bash
pip install statewave httpx
python benchmark_support_workflow.py
```

## What these don't prove

- LLM response quality (no model in the loop)
- Production latency or scale
- Real neural-embedding RAG (TF-IDF is the off-the-shelf baseline)

For a real model in the loop see [`../support-agent-llm/`](../support-agent-llm/).
