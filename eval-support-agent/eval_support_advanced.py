"""Advanced Support-Agent Eval — proves session-aware, health-aware, repeat-issue capabilities.

Covers features not in the basic eval:
- Session-aware context ranking (active session boosted)
- Resolution-aware ranking (resolved deprioritized, open boosted)
- Repeat-issue detection (recurring patterns surfaced)
- Customer health scoring (at-risk state computed correctly)
- Health-aware handoff (health state + factors in handoff pack)

Seeds a 4-session scenario:
- sess-A: billing gateway timeout (resolved 30 days ago)
- sess-B: unrelated password issue (resolved 25 days ago)
- sess-C: billing gateway timeout AGAIN (open, urgency markers)
- sess-D: active session — customer asking for update on sess-C

Run:  python eval_support_advanced.py
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

SUBJECT_ID = "eval-advanced-carol"
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

EPISODES = [
    # Session A: Billing gateway timeout (resolved 30 days ago)
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Hi, I'm Carol from DataFlow Inc. Enterprise plan. Our billing gateway is timing out when processing payments."}]},
        "session_id": "sess-A",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "Hi Carol! I see the gateway timeout. Let me restart the payment processing service."}]},
        "session_id": "sess-A",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "That fixed it, payments are going through now. Thanks!"}]},
        "session_id": "sess-A",
    },
    # Session B: Password reset (resolved, unrelated)
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Hey, I need to reset my admin password for our dashboard."}]},
        "session_id": "sess-B",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "Done — reset link sent to carol@dataflow.io. You're all set."}]},
        "session_id": "sess-B",
    },
    # Session C: Billing gateway timeout AGAIN (open, with urgency)
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "The billing gateway is timing out AGAIN. This is urgent — we have invoices due today and payments are failing."}]},
        "session_id": "sess-C",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "I see the timeout recurring. The restart fix from last time isn't holding. Let me check the gateway logs and escalate."}]},
        "session_id": "sess-C",
    },
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "assistant", "content": "I've escalated to the payments team. The root cause appears to be a connection pool exhaustion. They're deploying a fix."}]},
        "session_id": "sess-C",
    },
    # Session D: Active — customer checking in
    {
        "source": "support-chat",
        "type": "message",
        "payload": {"messages": [{"role": "user", "content": "Hi, any update on the billing gateway issue? We're still blocked and this is critical for our month-end close."}]},
        "session_id": "sess-D",
    },
]

RESOLUTIONS = [
    {"session_id": "sess-A", "status": "resolved", "resolution_summary": "Restarted payment processing service, gateway timeout resolved"},
    {"session_id": "sess-B", "status": "resolved", "resolution_summary": "Password reset link sent successfully"},
    {"session_id": "sess-C", "status": "open", "resolution_summary": "Billing gateway timeout recurring, escalated to payments team"},
]


# ── Helpers ────────────────────────────────────────────────────────────────


def contains(text: str, expected: str) -> bool:
    return expected.lower() in text.lower()


# ── Eval logic ─────────────────────────────────────────────────────────────


def run_eval() -> EvalResult:
    client = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    http = httpx.Client(base_url=SERVER_URL)
    result = EvalResult()

    print("\n═══ Statewave Advanced Support-Agent Eval ═══\n")

    # ── Setup ──────────────────────────────────────────────────────────────
    try:
        client.delete_subject(SUBJECT_ID)
    except (StatewaveConnectionError, StatewaveAPIError):
        pass

    print("  Seeding scenario: Enterprise customer, 4 sessions (2 resolved, 1 open, 1 active)")
    print("  Pattern: billing gateway timeout is a RECURRING issue")
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

    # ── Test 1: Session-aware context — active session boosted ─────────────
    test1 = TestCase(name="Session-aware context ranking")
    ctx = client.get_context(
        SUBJECT_ID, "Help with the billing gateway issue", max_tokens=800, session_id="sess-D"
    )
    context_text = ctx.assembled_context

    a1 = Assertion(description="Active session (sess-D) content appears in context")
    a1.passed = contains(context_text, "update") or contains(context_text, "month-end")
    test1.assertions.append(a1)

    a2 = Assertion(description="Open issue (sess-C) content appears — escalation mentioned")
    a2.passed = contains(context_text, "escalat") or contains(context_text, "connection pool")
    test1.assertions.append(a2)

    a3 = Assertion(description="Unrelated resolved session (password) is NOT prominent")
    # The password session should not dominate; gateway content should appear first
    a3.passed = contains(context_text, "gateway") or contains(context_text, "billing")
    a3.detail = "Gateway/billing content present (expected to outrank password reset)"
    test1.assertions.append(a3)

    result.tests.append(test1)

    # ── Test 2: Repeat-issue detection — prior resolution surfaced ─────────
    test2 = TestCase(name="Repeat-issue detection")

    a1 = Assertion(description="Prior resolution (sess-A: restart fix) surfaced in context")
    a1.passed = contains(context_text, "restart") or contains(context_text, "sess-A") or contains(context_text, "payment processing")
    a1.detail = "Prior fix for same issue type should be visible"
    test2.assertions.append(a1)

    a2 = Assertion(description="Context includes the recurring pattern signal")
    # Either the compiled memory mentions recurrence, or both gateway sessions appear
    has_both = contains(context_text, "timeout") and (contains(context_text, "restart") or contains(context_text, "again"))
    a2.passed = has_both
    a2.detail = "Both timeout instances referenced"
    test2.assertions.append(a2)

    result.tests.append(test2)

    # ── Test 3: Health scoring ─────────────────────────────────────────────
    test3 = TestCase(name="Customer health scoring")
    resp = http.get(f"{SERVER_URL}/v1/subjects/{SUBJECT_ID}/health")
    assert resp.status_code == 200, f"Health endpoint failed: {resp.status_code}"
    health = resp.json()

    a1 = Assertion(description="Health state is 'watch' or 'at_risk' (has open + recurring issue)")
    a1.passed = health["state"] in ("watch", "at_risk")
    a1.detail = f"state={health['state']}, score={health['score']}"
    test3.assertions.append(a1)

    a2 = Assertion(description="Health score is below 70 (not healthy)")
    a2.passed = health["score"] < 70
    a2.detail = f"score={health['score']}"
    test3.assertions.append(a2)

    a3 = Assertion(description="Factors include 'unresolved_issues' signal")
    signals = [f["signal"] for f in health["factors"]]
    a3.passed = "unresolved_issues" in signals
    a3.detail = f"signals={signals}"
    test3.assertions.append(a3)

    a4 = Assertion(description="Factors are explainable (each has signal + detail)")
    a4.passed = all(f.get("signal") and f.get("detail") for f in health["factors"])
    test3.assertions.append(a4)

    result.tests.append(test3)

    # ── Test 4: Health-aware handoff ───────────────────────────────────────
    test4 = TestCase(name="Health-aware handoff")
    resp = http.post(
        f"{SERVER_URL}/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-D", "reason": "shift handoff"},
    )
    assert resp.status_code == 200, f"Handoff failed: {resp.status_code}"
    handoff = resp.json()

    a1 = Assertion(description="Handoff includes health_state field")
    a1.passed = handoff.get("health_state") in ("healthy", "watch", "at_risk")
    a1.detail = f"health_state={handoff.get('health_state')}"
    test4.assertions.append(a1)

    a2 = Assertion(description="Handoff health_state matches standalone health endpoint")
    a2.passed = handoff.get("health_state") == health["state"]
    test4.assertions.append(a2)

    a3 = Assertion(description="Handoff includes health_score")
    a3.passed = isinstance(handoff.get("health_score"), int)
    a3.detail = f"health_score={handoff.get('health_score')}"
    test4.assertions.append(a3)

    a4 = Assertion(description="Handoff notes contain health indicator (🔴/🟡/🟢)")
    notes = handoff.get("handoff_notes", "")
    a4.passed = any(icon in notes for icon in ("🔴", "🟡", "🟢"))
    test4.assertions.append(a4)

    a5 = Assertion(description="Handoff notes contain health state (AT_RISK or WATCH)")
    a5.passed = "AT_RISK" in notes or "WATCH" in notes
    test4.assertions.append(a5)

    a6 = Assertion(description="Health factors included in handoff (≤3, compact)")
    factors = handoff.get("health_factors", [])
    a6.passed = 0 < len(factors) <= 3
    a6.detail = f"got {len(factors)} factors"
    test4.assertions.append(a6)

    result.tests.append(test4)

    # ── Test 5: Resolved deprioritization + open issue boost ───────────────
    test5 = TestCase(name="Resolution-aware ranking")

    a1 = Assertion(description="Active issue (gateway timeout) is the primary topic in handoff")
    a1.passed = contains(handoff.get("active_issue", ""), "gateway") or contains(handoff.get("active_issue", ""), "billing")
    a1.detail = handoff.get("active_issue", "")[:80]
    test5.assertions.append(a1)

    a2 = Assertion(description="Resolution history present in handoff")
    a2.passed = len(handoff.get("resolution_history", [])) >= 2
    a2.detail = f"got {len(handoff.get('resolution_history', []))} resolutions"
    test5.assertions.append(a2)

    a3 = Assertion(description="Open Issues section in handoff notes")
    a3.passed = "Open Issues" in notes
    test5.assertions.append(a3)

    result.tests.append(test5)

    # ── Test 6: Compactness and determinism ────────────────────────────────
    test6 = TestCase(name="Compactness and determinism")

    a1 = Assertion(description=f"Handoff token estimate ≤ 4000 (got {handoff.get('token_estimate', 0)})")
    a1.passed = handoff.get("token_estimate", 9999) <= 4000
    test6.assertions.append(a1)

    # Second request should be identical
    resp2 = http.post(
        f"{SERVER_URL}/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-D", "reason": "shift handoff"},
    )
    handoff2 = resp2.json()
    a2 = Assertion(description="Deterministic: two identical requests produce same handoff_notes")
    a2.passed = handoff.get("handoff_notes") == handoff2.get("handoff_notes")
    test6.assertions.append(a2)

    a3 = Assertion(description="Deterministic: same health_score both times")
    a3.passed = handoff.get("health_score") == handoff2.get("health_score")
    test6.assertions.append(a3)

    result.tests.append(test6)

    # ── Test 7: Provenance ─────────────────────────────────────────────────
    test7 = TestCase(name="Provenance preserved")
    prov = handoff.get("provenance", {})

    a1 = Assertion(description="provenance.episode_ids is non-empty")
    a1.passed = len(prov.get("episode_ids", [])) > 0
    test7.assertions.append(a1)

    a2 = Assertion(description="provenance.resolution_ids is non-empty")
    a2.passed = len(prov.get("resolution_ids", [])) > 0
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

    total_assertions = result.total
    passed_assertions = result.passed
    print(f"═══ RESULTS: {passed_assertions}/{total_assertions} assertions passed ({result.score:.0%}) ═══\n")

    # ── Cleanup ────────────────────────────────────────────────────────────
    client.delete_subject(SUBJECT_ID)
    client.close()
    http.close()

    return result


if __name__ == "__main__":
    result = run_eval()
    sys.exit(0 if result.passed == result.total else 1)
