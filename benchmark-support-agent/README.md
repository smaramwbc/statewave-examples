# Support Agent Context Benchmark

A **fair comparison** of three approaches to providing context in a support-agent scenario:

| Approach | Description |
|----------|-------------|
| **Statewave** | Structured memory: ingest → compile → ranked context assembly |
| **History Stuffing** | Naïve approach: concatenate all past messages into the prompt |
| **Simple RAG** | Vector similarity search over raw messages (no compilation) |

## What it measures

For the **same customer** and **same question**, each approach produces a context string.
The benchmark then asserts:

| Metric | What it proves |
|--------|---------------|
| Identity recall | Does the context contain the customer's name/company? |
| Preference recall | Does the context contain their stated technical preferences? |
| Issue history recall | Does the context reference past issues and resolutions? |
| Token efficiency | How many tokens does the approach use to deliver the same info? |
| Provenance | Can you trace context back to source interactions? |

## Methodology

1. **Same input data** — all three approaches receive the exact same 8 episodes (3 sessions)
2. **Same retrieval task** — "Help this customer add a team member"
3. **Deterministic** — no LLM in the loop; assertions are substring checks
4. **Honest baselines** — history stuffing gets ALL messages; RAG gets top-k by cosine similarity

### What the RAG baseline does

Since we want a self-contained benchmark (no external vector DB dependency), the RAG baseline:
- Splits messages into chunks
- Computes TF-IDF vectors (scikit-learn)
- Retrieves top-k chunks by cosine similarity to the query
- Concatenates them as context

This is a **fair and common** RAG implementation pattern.

## Run

```bash
# Requires: Statewave server at localhost:8100
# pip install statewave-py scikit-learn

export STATEWAVE_URL="http://localhost:8100"  # optional, default
python benchmark_support_context.py
```

## Expected output

```
═══ Support Agent Context Benchmark ═══

Scenario: 3-session enterprise customer, 8 episodes
Task: "Help this customer add a new team member to their account"

─── Statewave ───────────────────────────────────
  ✓ Identity recall: Alice Chen
  ✓ Identity recall: Globex
  ✓ Preference recall: Python SDK
  ✓ Issue history: SSO / SAML
  ✓ Issue history: ENG-4521
  ✓ Provenance: source tracing available
  Tokens: ~180

─── History Stuffing ────────────────────────────
  ✓ Identity recall: Alice Chen
  ✓ Identity recall: Globex
  ✓ Preference recall: Python SDK
  ✓ Issue history: SSO / SAML
  ✓ Issue history: ENG-4521
  ✗ Provenance: no source tracing
  Tokens: ~650

─── Simple RAG (TF-IDF, top-5) ─────────────────
  ? Identity recall: Alice Chen      (depends on retrieval)
  ? Identity recall: Globex          (depends on retrieval)
  ? Preference recall: Python SDK    (depends on retrieval)
  ? Issue history: SSO / SAML        (likely ✓)
  ? Issue history: ENG-4521          (likely ✓)
  ✗ Provenance: no source tracing
  Tokens: ~300

═══ Summary ═══
Statewave:       5/5 recall, provenance ✓, ~180 tokens
History Stuff:   5/5 recall, provenance ✗, ~650 tokens (3.6× more)
Simple RAG:      variable recall, provenance ✗, ~300 tokens
```

## What this benchmark proves

1. **Statewave achieves the same recall as history stuffing at 3-4× fewer tokens**
2. **Statewave provides provenance that neither baseline offers**
3. **Simple RAG has inconsistent recall** — it finds things related to the query but may miss identity/preference facts unrelated to the current task

## What this benchmark does NOT prove

- LLM response quality (no LLM in the eval loop)
- Performance at scale (only 8 episodes)
- Multi-tenant isolation
- Real embedding quality (RAG baseline uses TF-IDF, not neural embeddings)
- Production latency characteristics

## Fair play notes

- History stuffing **will** pass all recall tests — it has everything. The tradeoff is token cost.
- RAG retrieval quality depends on the similarity function and chunk strategy. We use a standard TF-IDF approach, which is generous to RAG.
- Statewave's advantage grows with longer histories (more episodes → more token savings from compilation).
