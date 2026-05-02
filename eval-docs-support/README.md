# Docs-grounded support agent eval

Measures retrieval/ranking quality on the canonical `statewave-support-docs` subject. Designed to be run before and after a server-side ranking change so the diff is observable.

## What it measures

For each of 8 canonical product/support questions, the eval asks Statewave's `/v1/context` and checks:

| Signal | What it tells you |
|---|---|
| **Doc match** | Did at least one expected doc appear in the resolved citation set (top-4 by `source_episode_ids` → `doc_path`)? Catches the "same 4 citations across every query" failure shape. |
| **Term recall** | Fraction of substantive expected terms (e.g. `postgres`, `pgvector`, `fly`, `gpu`) found anywhere in retrieved facts/procedures. Catches the "model has no grounding for this question" shape. |
| **Groundability** | Were ≥ 2 retrieved facts substantive enough (contain at least one expected term) for the LLM to answer without hedging? |

Plus one aggregate signal:

- **Citation diversity** — count of unique `doc_path`s across all 8 queries combined. The bug we observed had this stuck at ~4; a well-functioning ranker should approach the count of distinct expected docs (~10).

The eval mocks nothing — it hits a live Statewave instance. The episode→doc_path map is pulled once via `/admin/subjects/{id}/episodes` so citations match what the widget renders.

## Run it

```bash
STATEWAVE_URL=https://statewave-api.fly.dev \
STATEWAVE_API_KEY=... \
python eval_docs_support.py
```

To capture a snapshot for before/after diffing:

```bash
python eval_docs_support.py --out=baseline.json
# … make change …
python eval_docs_support.py --out=after.json
diff <(jq -S . baseline.json) <(jq -S . after.json)
```

## What good looks like

Targets for a well-functioning docs-grounded retriever on this corpus:

| Metric | Floor | Goal |
|---|---|---|
| `doc_match_rate` | ≥ 60% | ≥ 85% |
| `avg_term_recall` | ≥ 0.5 | ≥ 0.75 |
| `groundable_rate` | ≥ 60% | ≥ 80% |
| `citation_diversity` | ≥ 6 unique docs | ≥ 10 unique docs |

## What this eval does NOT measure

- Answer quality — it doesn't call an LLM. We score what the *retriever* surfaces; whether the model uses it well is downstream.
- Confabulation — the eval can't detect a model that hallucinates correctly. That's the [Statewave Support persona's system prompt](https://github.com/smaramwbc/statewave-web/blob/main/api/widget-chat.ts) job.
- Citation precision (which exact section is best). Just doc-level recall.

## Notes

- The expected term list is deliberately conservative: stopwords and the word "Statewave" itself are excluded so they can't inflate term-recall scores trivially.
- Several questions list multiple acceptable expected docs (e.g. *"What database does Statewave require?"* accepts `architecture/overview.md`, `product.md`, or `why-statewave.md`). This isn't generosity — it's accepting that the same authoritative fact is documented in more than one place, which is true of well-written docs.
