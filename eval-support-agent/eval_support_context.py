"""Support Agent Context Quality Eval — proves Statewave context correctness.

Seeds realistic multi-session support episodes, compiles memories,
then asserts expected facts appear in retrieved context bundles.
Also validates provenance tracing and compilation idempotency.

Run:  python eval_support_context.py
Requires: Statewave server at http://localhost:8100
          pip install statewave-py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

from statewave import StatewaveClient
from statewave.exceptions import StatewaveAPIError, StatewaveConnectionError

# ── Configuration ──────────────────────────────────────────────────────────

SUBJECT_ID = "eval-support-alice"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
TOKEN_BUDGET = 600

# ── Test infrastructure ────────────────────────────────────────────────────


@dataclass
class Assertion:
    description: str
    passed: bool = False
    detail: str = ""


@dataclass
class TestCase:
    name: str
    task: str
    assertions: list[Assertion] = field(default_factory=list)
    max_tokens: int = TOKEN_BUDGET


@dataclass
class EvalResult:
    tests: list[TestCase] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(len(t.assertions) for t in self.tests)

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests for a in t.assertions if a.passed)

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


# ── Episode data (realistic multi-session support customer) ────────────────

EPISODES = [
    # Session 1: Initial contact — identity + plan
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
    # Session 1: Technical preference
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 1,
            "messages": [
                {"role": "user", "content": "I want to integrate via the Python SDK. We also need webhook notifications for real-time updates."},
                {"role": "assistant", "content": "Great choices! The Python SDK and webhooks work well together. Let me help you set that up."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-001"},
    },
    # Session 1: Issue raised
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 1,
            "messages": [
                {"role": "user", "content": "Actually, we're blocked on SSO configuration. The SAML callback URL keeps failing."},
                {"role": "assistant", "content": "I see — let me look into the SSO issue. Can you share the error you're seeing?"},
                {"role": "user", "content": "It returns a 403 with 'invalid assertion' after the IdP redirect."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-001"},
    },
    # Session 1: Escalation
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 1,
            "messages": [
                {"role": "assistant", "content": "I've escalated this to our engineering team. They'll look at the SAML assertion validation. Ticket: ENG-4521."},
                {"role": "user", "content": "Thanks, please keep me posted."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-001"},
    },
    # Session 2: Follow-up (2 days later)
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 2,
            "messages": [
                {"role": "user", "content": "Hi, any update on the SSO issue? Ticket ENG-4521."},
                {"role": "assistant", "content": "Hi Alice! Engineering pushed a fix yesterday. Can you try the SAML flow again?"},
                {"role": "user", "content": "It works now! SSO is configured. Thanks!"},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-002"},
    },
    # Session 2: New request — billing
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 2,
            "messages": [
                {"role": "user", "content": "One more thing — can we get a consolidated invoice for our 3 workspaces?"},
                {"role": "assistant", "content": "Absolutely. I've enabled consolidated billing for Globex. You'll see a single invoice next cycle."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-002"},
    },
    # Session 3: Returning with new question
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 3,
            "messages": [
                {"role": "user", "content": "Hey, we want to add our staging environment. What's the best approach?"},
                {"role": "assistant", "content": "For Enterprise, I'd recommend a separate workspace with the same SSO config. Want me to provision it?"},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-003"},
    },
    # Session 3: Satisfaction signal
    {
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "session": 3,
            "messages": [
                {"role": "user", "content": "Yes please. Your support has been excellent — every time I come back you already know our setup."},
                {"role": "assistant", "content": "Happy to help, Alice! I'll send the staging workspace details shortly."},
            ],
        },
        "metadata": {"channel": "chat", "session_id": "sess-003"},
    },
]

# ── Eval logic ─────────────────────────────────────────────────────────────


def check_contains(context: str, expected: str) -> bool:
    """Case-insensitive substring check."""
    return expected.lower() in context.lower()


def run_eval() -> EvalResult:
    """Run the full eval suite."""
    client = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    result = EvalResult()

    # ── Connection check ───────────────────────────────────────────────────
    print("\n═══ Statewave Support Agent — Context Quality Eval ═══\n")
    try:
        client.delete_subject(SUBJECT_ID)
    except StatewaveConnectionError:
        print(f"❌ Cannot connect to Statewave at {SERVER_URL}")
        print(f"   Start the server first: uvicorn server.app:app --port 8100")
        sys.exit(2)
    except StatewaveAPIError:
        pass  # 404 is fine — subject didn't exist

    # ── Seed episodes ──────────────────────────────────────────────────────
    print(f"Scenario: Returning enterprise customer (3 sessions)")
    print(f"  Seeding {len(EPISODES)} episodes...", end=" ", flush=True)
    for ep in EPISODES:
        client.create_episode(
            subject_id=SUBJECT_ID,
            source=ep["source"],
            type=ep["type"],
            payload=ep["payload"],
            metadata=ep.get("metadata"),
        )
    print("✓")

    # ── Compile ────────────────────────────────────────────────────────────
    print("  Compiling memories...", end=" ", flush=True)
    compile_result = client.compile_memories(SUBJECT_ID)
    print(f"✓ ({compile_result.memories_created} memories created)")
    print()

    # ── Test 1: Identity recall ────────────────────────────────────────────
    test1 = TestCase(name="Identity recall", task="Help this customer with their billing question")
    ctx = client.get_context(SUBJECT_ID, test1.task, max_tokens=test1.max_tokens)
    context_text = ctx.assembled_context

    for desc, expected in [
        ('Customer name "Alice Chen" in context', "Alice Chen"),
        ('Company "Globex" in context', "Globex"),
        ('Plan "Enterprise" in context', "Enterprise"),
    ]:
        a = Assertion(description=desc)
        a.passed = check_contains(context_text, expected)
        test1.assertions.append(a)
    result.tests.append(test1)

    # ── Test 2: Preference recall ──────────────────────────────────────────
    test2 = TestCase(name="Preference recall", task="Suggest an integration approach for this customer")
    ctx = client.get_context(SUBJECT_ID, test2.task, max_tokens=test2.max_tokens)
    context_text = ctx.assembled_context

    for desc, expected in [
        ('Preference "Python SDK" in context', "Python SDK"),
        ('Preference "webhook" in context', "webhook"),
    ]:
        a = Assertion(description=desc)
        a.passed = check_contains(context_text, expected)
        test2.assertions.append(a)
    result.tests.append(test2)

    # ── Test 3: History recall ─────────────────────────────────────────────
    test3 = TestCase(name="History recall", task="Follow up on their open issue")
    ctx = client.get_context(SUBJECT_ID, test3.task, max_tokens=test3.max_tokens)
    context_text = ctx.assembled_context

    for desc, expected in [
        ('Prior issue "SSO" in context', "SSO"),
        ('Ticket "ENG-4521" in context', "ENG-4521"),
    ]:
        a = Assertion(description=desc)
        a.passed = check_contains(context_text, expected)
        test3.assertions.append(a)
    result.tests.append(test3)

    # ── Test 4: Token efficiency ───────────────────────────────────────────
    test4 = TestCase(name="Token efficiency", task="Help with password reset", max_tokens=500)
    ctx = client.get_context(SUBJECT_ID, test4.task, max_tokens=test4.max_tokens)

    a1 = Assertion(description=f"Token estimate ≤ 500 (was {ctx.token_estimate})")
    a1.passed = ctx.token_estimate <= 500
    test4.assertions.append(a1)

    a2 = Assertion(description="Identity facts still included for unknown task")
    a2.passed = check_contains(ctx.assembled_context, "Alice") or check_contains(ctx.assembled_context, "Globex")
    test4.assertions.append(a2)
    result.tests.append(test4)

    # ── Test 5: Provenance tracing ─────────────────────────────────────────
    test5 = TestCase(name="Provenance tracing", task="Summarize this customer's history")
    ctx = client.get_context(SUBJECT_ID, test5.task, max_tokens=test5.max_tokens)

    prov = ctx.provenance
    has_ids = bool(
        prov.get("fact_ids")
        or prov.get("summary_ids")
        or prov.get("episode_ids")
    )
    a1 = Assertion(description="Provenance contains source IDs")
    a1.passed = has_ids
    test5.assertions.append(a1)

    a2 = Assertion(description="Facts list is non-empty")
    a2.passed = len(ctx.facts) > 0
    test5.assertions.append(a2)

    a3 = Assertion(description="Each fact has source_episode_ids")
    a3.passed = all(len(f.source_episode_ids) > 0 for f in ctx.facts) if ctx.facts else False
    test5.assertions.append(a3)
    result.tests.append(test5)

    # ── Test 6: Compilation idempotency ────────────────────────────────────
    test6 = TestCase(name="Compilation idempotency", task="(n/a)")
    recompile = client.compile_memories(SUBJECT_ID)

    a1 = Assertion(description="Recompile creates 0 new memories")
    a1.passed = recompile.memories_created == 0
    a1.detail = f"got {recompile.memories_created}"
    test6.assertions.append(a1)
    result.tests.append(test6)

    # ── Test 7: Memory count sanity ────────────────────────────────────────
    test7 = TestCase(name="Memory count sanity", task="(n/a)")
    search = client.search_memories(SUBJECT_ID, limit=100)
    mem_count = len(search.memories)

    a1 = Assertion(description=f"Memory count is reasonable (got {mem_count}, expect 8–30)")
    a1.passed = 8 <= mem_count <= 30
    test7.assertions.append(a1)

    fact_count = sum(1 for m in search.memories if m.kind == "profile_fact")
    a2 = Assertion(description=f"At least 3 profile facts extracted (got {fact_count})")
    a2.passed = fact_count >= 3
    test7.assertions.append(a2)
    result.tests.append(test7)

    # ── Print results ──────────────────────────────────────────────────────
    for i, test in enumerate(result.tests, 1):
        passed_count = sum(1 for a in test.assertions if a.passed)
        total_count = len(test.assertions)
        status = "✓" if passed_count == total_count else "✗"
        print(f"Test {i}: {test.name} {status}")
        if test.task != "(n/a)":
            print(f"  Task: \"{test.task}\"")
        print(f"  Assertions:")
        for a in test.assertions:
            mark = "✓" if a.passed else "✗"
            extra = f"  ({a.detail})" if a.detail else ""
            print(f"    {mark} {a.description}{extra}")
        print(f"  Score: {passed_count}/{total_count}")
        print()

    print(f"═══ RESULTS: {result.passed}/{result.total} assertions passed ({result.score:.0%}) ═══")

    # ── Cleanup ────────────────────────────────────────────────────────────
    client.delete_subject(SUBJECT_ID)
    client.close()

    return result


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_eval()
    sys.exit(0 if result.passed == result.total else 1)
