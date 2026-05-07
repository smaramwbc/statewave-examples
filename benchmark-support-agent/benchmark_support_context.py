"""Support context benchmark — Statewave vs history stuffing vs simple RAG.

All three approaches see the same customer history and the same task.
We measure: recall of key facts, token cost, and whether the approach
preserves provenance back to source episodes.

Run:  pip install statewave-py scikit-learn
      python benchmark_support_context.py
"""

from __future__ import annotations

import os
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from statewave import StatewaveClient

SUBJECT_ID = "bench-support-alice"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
TASK = "Help this customer add a new team member to their account"

EPISODES = [
    {"messages": [
        {"role": "user", "content": "Hi, I'm Alice Chen from Globex Corporation. We're on the Enterprise plan."},
        {"role": "assistant", "content": "Welcome Alice! How can I help you today?"},
    ]},
    {"messages": [
        {"role": "user", "content": "I want to integrate via the Python SDK. We also need webhook notifications for real-time updates."},
        {"role": "assistant", "content": "Great choices! The Python SDK and webhooks work well together."},
    ]},
    {"messages": [
        {"role": "user", "content": "We're blocked on SSO configuration. The SAML callback URL keeps failing with a 403 'invalid assertion' error."},
        {"role": "assistant", "content": "I've escalated to engineering. Ticket: ENG-4521."},
    ]},
    {"messages": [
        {"role": "user", "content": "Hi, any update on the SSO issue? Ticket ENG-4521."},
        {"role": "assistant", "content": "Engineering pushed a fix. Can you try the SAML flow again?"},
        {"role": "user", "content": "It works now! SSO is configured. Thanks!"},
    ]},
    {"messages": [
        {"role": "user", "content": "Can we get a consolidated invoice for our 3 workspaces?"},
        {"role": "assistant", "content": "Done — consolidated billing is now enabled for Globex."},
    ]},
    {"messages": [
        {"role": "user", "content": "Also, our team prefers email notifications over Slack for billing alerts."},
        {"role": "assistant", "content": "Updated! Billing alerts will go to email."},
    ]},
    {"messages": [
        {"role": "user", "content": "Hey, we want to add a staging environment workspace."},
        {"role": "assistant", "content": "For Enterprise, I'd recommend a separate workspace with the same SSO config."},
    ]},
    {"messages": [
        {"role": "user", "content": "Great. Your support has been excellent — you always remember our setup."},
        {"role": "assistant", "content": "Happy to help, Alice!"},
    ]},
]

RECALL_CHECKS = [
    ("Identity: Alice Chen", "alice"),
    ("Identity: Globex", "globex"),
    ("Preference: Python SDK", "python sdk"),
    ("Issue history: SSO/SAML", "sso"),
    ("Issue history: ENG-4521", "eng-4521"),
]


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


def all_messages() -> list[str]:
    return [
        f"[{m['role']}] {m['content']}"
        for ep in EPISODES
        for m in ep["messages"]
    ]


def evaluate(name: str, context: str, has_provenance: bool, tokens: int) -> tuple[int, int]:
    print(f"\n--- {name} ---")
    hits = 0
    for label, needle in RECALL_CHECKS:
        ok = needle.lower() in context.lower()
        print(f"  {'✓' if ok else '✗'} {label}")
        hits += int(ok)
    print(f"  {'✓' if has_provenance else '✗'} Provenance: "
          f"{'source tracing available' if has_provenance else 'no source tracing'}")
    print(f"  Tokens: ~{tokens}")
    return hits, len(RECALL_CHECKS)


def run_statewave(client: StatewaveClient) -> tuple[str, int, bool]:
    client.delete_subject(SUBJECT_ID)
    for ep in EPISODES:
        client.create_episode(subject_id=SUBJECT_ID, source="support-chat", type="conversation", payload=ep)
    client.compile_memories(SUBJECT_ID)
    bundle = client.get_context(SUBJECT_ID, task=TASK, max_tokens=800)
    return bundle.assembled_context, bundle.token_estimate, bool(bundle.provenance)


def run_history_stuffing() -> tuple[str, int, bool]:
    context = "## Full conversation history\n\n" + "\n".join(all_messages())
    return context, estimate_tokens(context), False


def run_simple_rag(top_k: int = 5) -> tuple[str, int, bool]:
    messages = all_messages()
    vec = TfidfVectorizer(stop_words="english")
    matrix = vec.fit_transform(messages)
    sims = cosine_similarity(vec.transform([TASK]), matrix).flatten()
    top = sims.argsort()[-top_k:][::-1]
    context = f"## Retrieved (top-{top_k} by TF-IDF)\n\n" + "\n".join(messages[i] for i in top)
    return context, estimate_tokens(context), False


def main() -> None:
    print(f"Scenario: {len(EPISODES)} support episodes")
    print(f"Task:     {TASK!r}")

    client = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)

    sw_ctx, sw_tokens, sw_prov = run_statewave(client)
    hs_ctx, hs_tokens, hs_prov = run_history_stuffing()
    rag_ctx, rag_tokens, rag_prov = run_simple_rag()

    sw_hits, total = evaluate("Statewave", sw_ctx, sw_prov, sw_tokens)
    hs_hits, _ = evaluate("History stuffing", hs_ctx, hs_prov, hs_tokens)
    rag_hits, _ = evaluate("Simple RAG (TF-IDF, top-5)", rag_ctx, rag_prov, rag_tokens)

    print("\n--- Summary ---")
    print(f"  Statewave         {sw_hits}/{total} recall, provenance ✓, ~{sw_tokens} tokens")
    print(f"  History stuffing  {hs_hits}/{total} recall, provenance ✗, ~{hs_tokens} tokens")
    print(f"  Simple RAG        {rag_hits}/{total} recall, provenance ✗, ~{rag_tokens} tokens")

    client.delete_subject(SUBJECT_ID)
    sys.exit(0 if sw_prov and sw_hits > 0 else 1)


if __name__ == "__main__":
    main()
