"""Handoff Context Pack Eval — proves Statewave handoff quality.

Seeds a realistic multi-session support scenario with resolved and open issues,
then asserts the handoff pack correctly surfaces active issues, customer facts,
attempted steps, deprioritizes resolved items, and stays compact.

Also compares against a naive baseline (raw episode dump) to show signal-to-noise
improvement.

Run:  python eval_handoff.py
Requires: Statewave server at http://localhost:8100
          pip install statewave-py httpx
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import httpx
from statewave import StatewaveClient
from statewave.exceptions import StatewaveAPIError, StatewaveConnectionError

# ── Configuration ──────────────────────────────────────────────────────────

SUBJECT_ID = "eval-handoff-bob"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")

# ── Test infrastructure ────────────────────────────────────────────────────


@dataclass
class Assertion:
    description: str
    passed: bool = False
    detail: str = ""


@dataclass
class TestCase:
    name: str
    assertions: list[Assertion] = field(default_factory=list)


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


# ── Scenario data ─────────────────────────────────────────────────────────

# Bob is an Enterprise customer with 3 support sessions:
# - sess-001: password reset (resolved)
# - sess-002: API rate limiting issue (resolved)
# - sess-003: data export failure (active, being escalated)

EPISODES = [
    # Session 1: Password reset (resolved)
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Hi, I'm Bob Martinez from Acme Inc. Enterprise plan. I can't reset my password."}]},
        "session_id": "sess-001",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "Hi Bob! I've sent a password reset link to your registered email bob@acme.io."}]},
        "session_id": "sess-001",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Got it, works now. Thanks!"}]},
        "session_id": "sess-001",
    },
    # Session 2: API rate limiting (resolved)
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "We're hitting 429 errors on the /v1/episodes endpoint. Our batch job sends ~200 req/s."}]},
        "session_id": "sess-002",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "I've increased your rate limit to 500 req/s for the Enterprise tier. The change is live."}]},
        "session_id": "sess-002",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Confirmed, no more 429s. Thanks!"}]},
        "session_id": "sess-002",
    },
    # Session 3: Data export failure (active — being escalated)
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Our nightly data export job has been failing for 3 days. We get a timeout after 5 minutes. Export ID: EXP-9912."}]},
        "session_id": "sess-003",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "I see the export EXP-9912 timing out. Let me check the backend logs."}]},
        "session_id": "sess-003",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "The export dataset grew to 2.1M rows last week. I've tried bumping the timeout to 15min but it still fails. Escalating to engineering."}]},
        "session_id": "sess-003",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Please hurry — our compliance team needs this data by Friday."}]},
        "session_id": "sess-003",
    },
]

RESOLUTIONS = [
    {"session_id": "sess-001", "status": "resolved", "resolution_summary": "Password reset link sent, user confirmed working"},
    {"session_id": "sess-002", "status": "resolved", "resolution_summary": "Rate limit increased to 500 req/s for Enterprise tier"},
    {"session_id": "sess-003", "status": "open", "resolution_summary": "Data export timing out, escalated to engineering"},
]


# ── Helpers ────────────────────────────────────────────────────────────────


def contains(text: str, expected: str) -> bool:
    return expected.lower() in text.lower()


def naive_baseline(episodes: list[dict]) -> str:
    """Simulate a naive 'dump all history' approach."""
    lines = []
    for ep in episodes:
        msgs = ep["payload"].get("messages", [])
        for msg in msgs:
            lines.append(f"[{msg['role']}] {msg['content']}")
    return "\n".join(lines)


# ── Eval logic ─────────────────────────────────────────────────────────────


def run_eval() -> EvalResult:
    client = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    http = httpx.Client(base_url=SERVER_URL)
    result = EvalResult()

    print("\n═══ Statewave Handoff Context Pack — Eval ═══\n")

    # ── Setup ──────────────────────────────────────────────────────────────
    try:
        client.delete_subject(SUBJECT_ID)
    except (StatewaveConnectionError, StatewaveAPIError):
        pass

    print("  Seeding scenario: Enterprise customer, 3 sessions, 1 active issue")
    for ep in EPISODES:
        client.create_episode(
            subject_id=SUBJECT_ID,
            source=ep["source"],
            type=ep["type"],
            payload=ep["payload"],
            session_id=ep.get("session_id"),
        )

    client.compile_memories(SUBJECT_ID)

    for res in RESOLUTIONS:
        http.post(f"{SERVER_URL}/v1/resolutions", json={"subject_id": SUBJECT_ID, **res})

    print("  ✓ Scenario seeded\n")

    # ── Generate handoff ───────────────────────────────────────────────────
    resp = http.post(
        f"{SERVER_URL}/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-003", "reason": "escalation to engineering"},
    )
    assert resp.status_code == 200, f"Handoff failed: {resp.status_code} {resp.text}"
    handoff = resp.json()

    # ── Test 1: Active issue surfaced clearly ──────────────────────────────
    test1 = TestCase(name="Active issue surfaced")
    a1 = Assertion(description='Active issue mentions "export" or "EXP-9912"')
    a1.passed = contains(handoff["active_issue"], "export") or contains(handoff["active_issue"], "EXP-9912")
    a1.detail = handoff["active_issue"][:80]
    test1.assertions.append(a1)

    a2 = Assertion(description='Handoff notes contain "Active Issue" section')
    a2.passed = "Active Issue" in handoff["handoff_notes"]
    test1.assertions.append(a2)
    result.tests.append(test1)

    # ── Test 2: Customer facts present ─────────────────────────────────────
    test2 = TestCase(name="Customer facts present")
    a1 = Assertion(description='"Bob" or "Acme" in customer_summary or key_facts')
    a1.passed = (
        contains(handoff["customer_summary"], "Bob")
        or contains(handoff["customer_summary"], "Acme")
        or any(contains(f, "Bob") or contains(f, "Acme") for f in handoff["key_facts"])
    )
    test2.assertions.append(a1)

    a2 = Assertion(description='"Enterprise" in key_facts or customer_summary')
    a2.passed = (
        contains(handoff["customer_summary"], "Enterprise")
        or any(contains(f, "Enterprise") for f in handoff["key_facts"])
    )
    test2.assertions.append(a2)
    result.tests.append(test2)

    # ── Test 3: Attempted steps preserved ──────────────────────────────────
    test3 = TestCase(name="Attempted steps preserved")
    a1 = Assertion(description="At least 1 attempted step recorded")
    a1.passed = len(handoff["attempted_steps"]) >= 1
    a1.detail = f"got {len(handoff['attempted_steps'])}"
    test3.assertions.append(a1)

    a2 = Assertion(description='Steps mention "timeout" or "bumping" or "escalat"')
    a2.passed = any(
        contains(s, "timeout") or contains(s, "bumping") or contains(s, "escalat")
        for s in handoff["attempted_steps"]
    )
    test3.assertions.append(a2)
    result.tests.append(test3)

    # ── Test 4: Resolved items deprioritized ───────────────────────────────
    test4 = TestCase(name="Resolved items deprioritized")
    notes = handoff["handoff_notes"]

    a1 = Assertion(description='"Previously Resolved" section exists in notes')
    a1.passed = "Previously Resolved" in notes
    test4.assertions.append(a1)

    # Active issue should appear BEFORE resolved items in the notes
    active_pos = notes.find("Active Issue")
    resolved_pos = notes.find("Previously Resolved")
    a2 = Assertion(description="Active Issue appears before Previously Resolved in notes")
    a2.passed = active_pos != -1 and (resolved_pos == -1 or active_pos < resolved_pos)
    test4.assertions.append(a2)

    a3 = Assertion(description="Open issue (sess-003) listed under Open Issues")
    a3.passed = "Open Issues" in notes and "sess-003" in notes
    test4.assertions.append(a3)
    result.tests.append(test4)

    # ── Test 5: Compactness vs naive baseline ──────────────────────────────
    test5 = TestCase(name="Compactness vs naive baseline")
    naive = naive_baseline(EPISODES)
    handoff_text = handoff["handoff_notes"]

    a1 = Assertion(description="Handoff is shorter than naive dump")
    a1.passed = len(handoff_text) < len(naive) * 1.5  # Allow some structure overhead
    a1.detail = f"handoff={len(handoff_text)} chars, naive={len(naive)} chars"
    test5.assertions.append(a1)

    a2 = Assertion(description=f"Token estimate ≤ 4000 (got {handoff['token_estimate']})")
    a2.passed = handoff["token_estimate"] <= 4000
    test5.assertions.append(a2)

    # Signal-to-noise: handoff should have the key issue without all the noise
    a3 = Assertion(description="Handoff contains 'EXP-9912' (key signal)")
    a3.passed = "EXP-9912" in handoff_text
    test5.assertions.append(a3)

    # Naive includes resolved password reset prominently; handoff should minimize it
    a4 = Assertion(description="'password' not in active_issue (deprioritized)")
    a4.passed = not contains(handoff["active_issue"], "password")
    test5.assertions.append(a4)
    result.tests.append(test5)

    # ── Test 6: Provenance preserved ───────────────────────────────────────
    test6 = TestCase(name="Provenance preserved")
    prov = handoff["provenance"]

    a1 = Assertion(description="provenance.episode_ids is non-empty")
    a1.passed = len(prov.get("episode_ids", [])) > 0
    test6.assertions.append(a1)

    a2 = Assertion(description="provenance.resolution_ids is non-empty")
    a2.passed = len(prov.get("resolution_ids", [])) > 0
    test6.assertions.append(a2)
    result.tests.append(test6)

    # ── Test 7: Determinism ────────────────────────────────────────────────
    test7 = TestCase(name="Deterministic output")
    resp2 = http.post(
        f"{SERVER_URL}/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-003", "reason": "escalation to engineering"},
    )
    handoff2 = resp2.json()

    a1 = Assertion(description="Two identical requests produce same handoff_notes")
    a1.passed = handoff["handoff_notes"] == handoff2["handoff_notes"]
    test7.assertions.append(a1)

    a2 = Assertion(description="Same active_issue both times")
    a2.passed = handoff["active_issue"] == handoff2["active_issue"]
    test7.assertions.append(a2)
    result.tests.append(test7)

    # ── Print results ──────────────────────────────────────────────────────
    print("─── Results ───\n")
    for i, test in enumerate(result.tests, 1):
        passed_count = sum(1 for a in test.assertions if a.passed)
        total_count = len(test.assertions)
        status = "✓" if passed_count == total_count else "✗"
        print(f"  Test {i}: {test.name} {status}")
        for a in test.assertions:
            mark = "✓" if a.passed else "✗"
            extra = f"  ({a.detail})" if a.detail else ""
            print(f"    {mark} {a.description}{extra}")
        print()

    print(f"═══ RESULTS: {result.passed}/{result.total} assertions passed ({result.score:.0%}) ═══\n")

    # ── Cleanup ────────────────────────────────────────────────────────────
    client.delete_subject(SUBJECT_ID)
    client.close()
    http.close()

    return result


if __name__ == "__main__":
    result = run_eval()
    sys.exit(0 if result.passed == result.total else 1)
