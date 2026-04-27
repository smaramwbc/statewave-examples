"""Support Agent Context Benchmark — Statewave vs History Stuffing vs Simple RAG.

Compares three approaches to providing context for a support agent,
using the same customer history and the same retrieval task.

Run:  python benchmark_support_context.py
Requires:
  - Statewave server at http://localhost:8100
  - pip install statewave-py scikit-learn
"""

from __future__ import annotations

import os
import sys
import textwrap
from dataclasses import dataclass, field

from statewave import StatewaveClient
from statewave.exceptions import StatewaveAPIError, StatewaveConnectionError

# ── Configuration ──────────────────────────────────────────────────────────

SUBJECT_ID = "bench-support-alice"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
TASK = "Help this customer add a new team member to their account"

# ── Shared episode data ────────────────────────────────────────────────────

EPISODES = [
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 1,
            "messages": [
                {"role": "user", "content": "Hi, I'm Alice Chen from Globex Corporation. We're on the Enterprise plan."},
                {"role": "assistant", "content": "Welcome Alice! How can I help you today?"},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-001"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 1,
            "messages": [
                {"role": "user", "content": "I want to integrate via the Python SDK. We also need webhook notifications for real-time updates."},
                {"role": "assistant", "content": "Great choices! The Python SDK and webhooks work well together."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-001"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 1,
            "messages": [
                {"role": "user", "content": "We're blocked on SSO configuration. The SAML callback URL keeps failing with a 403 'invalid assertion' error."},
                {"role": "assistant", "content": "I've escalated to engineering. Ticket: ENG-4521."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-001"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 2,
            "messages": [
                {"role": "user", "content": "Hi, any update on the SSO issue? Ticket ENG-4521."},
                {"role": "assistant", "content": "Engineering pushed a fix. Can you try the SAML flow again?"},
                {"role": "user", "content": "It works now! SSO is configured. Thanks!"},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-002"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 2,
            "messages": [
                {"role": "user", "content": "Can we get a consolidated invoice for our 3 workspaces?"},
                {"role": "assistant", "content": "Done — consolidated billing is now enabled for Globex."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-002"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 2,
            "messages": [
                {"role": "user", "content": "Also, our team prefers email notifications over Slack for billing alerts."},
                {"role": "assistant", "content": "Updated! Billing alerts will go to email."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-002"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 3,
            "messages": [
                {"role": "user", "content": "Hey, we want to add a staging environment workspace."},
                {"role": "assistant", "content": "For Enterprise, I'd recommend a separate workspace with the same SSO config."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-003"},
    },
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 3,
            "messages": [
                {"role": "user", "content": "Great. Your support has been excellent — you always remember our setup."},
                {"role": "assistant", "content": "Happy to help, Alice! I'll send staging workspace details shortly."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-003"},
    },
]

# ── Extract all messages as flat text (used by baselines) ──────────────────


def _all_messages() -> list[str]:
    """Extract every message as individual text chunks."""
    chunks = []
    for ep in EPISODES:
        for msg in ep["payload"]["messages"]:
            chunks.append(f"[{msg['role']}] {msg['content']}")
    return chunks


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (words * 1.3)."""
    return int(len(text.split()) * 1.3)


# ── Assertions ─────────────────────────────────────────────────────────────

RECALL_CHECKS = [
    ("Identity: Alice Chen", "alice"),
    ("Identity: Globex", "globex"),
    ("Preference: Python SDK", "python sdk"),
    ("Issue history: SSO/SAML", "sso"),
    ("Issue history: ENG-4521", "eng-4521"),
]


@dataclass
class ApproachResult:
    name: str
    context: str
    tokens: int
    has_provenance: bool
    recall_results: list[tuple[str, bool]] = field(default_factory=list)

    @property
    def recall_score(self) -> int:
        return sum(1 for _, passed in self.recall_results if passed)

    @property
    def recall_total(self) -> int:
        return len(self.recall_results)


def evaluate_recall(context: str) -> list[tuple[str, bool]]:
    """Check all recall assertions against a context string."""
    results = []
    for label, needle in RECALL_CHECKS:
        results.append((label, needle.lower() in context.lower()))
    return results


# ── Approach 1: Statewave ──────────────────────────────────────────────────


def run_statewave(client: StatewaveClient) -> ApproachResult:
    """Statewave: ingest → compile → context assembly."""
    # Clean slate
    try:
        client.delete_subject(SUBJECT_ID)
    except StatewaveAPIError:
        pass

    # Ingest
    for ep in EPISODES:
        client.create_episode(subject_id=SUBJECT_ID, **ep)

    # Compile
    client.compile_memories(SUBJECT_ID)

    # Retrieve context
    bundle = client.get_context(SUBJECT_ID, task=TASK, max_tokens=800)
    context = bundle.assembled_context or ""

    # Check provenance
    has_provenance = bool(bundle.provenance) and len(bundle.provenance) > 0

    tokens = bundle.token_estimate or _estimate_tokens(context)

    return ApproachResult(
        name="Statewave",
        context=context,
        tokens=tokens,
        has_provenance=has_provenance,
        recall_results=evaluate_recall(context),
    )


# ── Approach 2: History Stuffing ───────────────────────────────────────────


def run_history_stuffing() -> ApproachResult:
    """Naïve: concatenate ALL messages into a single context block."""
    messages = _all_messages()
    context = "## Full conversation history\n\n" + "\n".join(messages)
    tokens = _estimate_tokens(context)

    return ApproachResult(
        name="History Stuffing",
        context=context,
        tokens=tokens,
        has_provenance=False,
        recall_results=evaluate_recall(context),
    )


# ── Approach 3: Simple RAG (TF-IDF) ───────────────────────────────────────


def run_simple_rag(top_k: int = 5) -> ApproachResult:
    """Simple RAG: TF-IDF vectorize messages, retrieve top-k by cosine similarity."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print("  ⚠ scikit-learn not installed — skipping RAG baseline")
        print("    pip install scikit-learn")
        return ApproachResult(
            name="Simple RAG (TF-IDF)",
            context="[skipped — scikit-learn not installed]",
            tokens=0,
            has_provenance=False,
            recall_results=[("skipped", False)] * len(RECALL_CHECKS),
        )

    messages = _all_messages()

    # Vectorize
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(messages)

    # Query vector
    query_vec = vectorizer.transform([TASK])

    # Cosine similarity
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Top-k indices
    top_indices = similarities.argsort()[-top_k:][::-1]

    # Build context from top-k
    retrieved = [messages[i] for i in top_indices]
    context = "## Retrieved context (top-{} by similarity)\n\n".format(top_k)
    context += "\n".join(retrieved)
    tokens = _estimate_tokens(context)

    return ApproachResult(
        name=f"Simple RAG (TF-IDF, top-{top_k})",
        context=context,
        tokens=tokens,
        has_provenance=False,
        recall_results=evaluate_recall(context),
    )


# ── Main ───────────────────────────────────────────────────────────────────


def print_result(r: ApproachResult) -> None:
    """Pretty-print one approach's results."""
    print(f"\n─── {r.name} {'─' * (45 - len(r.name))}")
    for label, passed in r.recall_results:
        icon = "✓" if passed else "✗"
        print(f"  {icon} {label}")
    prov_icon = "✓" if r.has_provenance else "✗"
    print(f"  {prov_icon} Provenance: {'source tracing available' if r.has_provenance else 'no source tracing'}")
    print(f"  Tokens: ~{r.tokens}")


def main() -> None:
    print("\n═══ Support Agent Context Benchmark ═══\n")
    print(f"Scenario: 3-session enterprise customer, {len(EPISODES)} episodes")
    print(f"Task: \"{TASK}\"")

    # ── Connect to Statewave ───────────────────────────────────────────────
    client = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    try:
        # Quick connectivity check
        client.delete_subject("__bench_ping__")
    except StatewaveConnectionError:
        print(f"\n❌ Cannot connect to Statewave at {SERVER_URL}")
        print("   Start the server: docker compose up -d")
        sys.exit(2)
    except StatewaveAPIError:
        pass  # 404 expected

    # ── Run all approaches ─────────────────────────────────────────────────
    statewave_result = run_statewave(client)
    history_result = run_history_stuffing()
    rag_result = run_simple_rag(top_k=5)

    # ── Print results ──────────────────────────────────────────────────────
    print_result(statewave_result)
    print_result(history_result)
    print_result(rag_result)

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n═══ Summary ═══")
    for r in [statewave_result, history_result, rag_result]:
        prov = "✓" if r.has_provenance else "✗"
        print(f"  {r.name:30s} {r.recall_score}/{r.recall_total} recall, provenance {prov}, ~{r.tokens} tokens")

    # Token efficiency
    if statewave_result.tokens > 0 and history_result.tokens > 0:
        ratio = history_result.tokens / statewave_result.tokens
        print(f"\n  Token efficiency: Statewave uses {ratio:.1f}× fewer tokens than history stuffing")

    # ── Exit code ──────────────────────────────────────────────────────────
    # Statewave must pass all recall + provenance
    sw_pass = statewave_result.recall_score == statewave_result.recall_total and statewave_result.has_provenance
    if sw_pass:
        print("\n✅ Benchmark PASSED — Statewave delivers full recall with provenance at minimal tokens")
        sys.exit(0)
    else:
        print("\n❌ Benchmark FAILED — Statewave did not meet expected quality bar")
        sys.exit(1)


if __name__ == "__main__":
    main()
