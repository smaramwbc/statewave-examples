"""Advanced support-agent eval — session-aware ranking, repeat-issue detection,
customer health scoring, health-aware handoff.

4-session scenario:
  sess-A: billing gateway timeout (resolved)
  sess-B: password reset (resolved, unrelated)
  sess-C: billing gateway timeout AGAIN (open, urgent)
  sess-D: active — customer asking for update on sess-C

Run:  pytest test_support_advanced.py -v
"""

from __future__ import annotations

import httpx
import pytest
from statewave import StatewaveClient

from conftest import seed_resolutions, seed_subject

SUBJECT_ID = "eval-advanced-carol"

EPISODES = [
    {"type": "message", "session_id": "sess-A",
     "payload": {"messages": [{"role": "user", "content": "Hi, I'm Carol from DataFlow Inc. Enterprise plan. Our billing gateway is timing out when processing payments."}]}},
    {"type": "message", "session_id": "sess-A",
     "payload": {"messages": [{"role": "assistant", "content": "Hi Carol! I see the gateway timeout. Let me restart the payment processing service."}]}},
    {"type": "message", "session_id": "sess-A",
     "payload": {"messages": [{"role": "user", "content": "That fixed it, payments are going through now. Thanks!"}]}},
    {"type": "message", "session_id": "sess-B",
     "payload": {"messages": [{"role": "user", "content": "Hey, I need to reset my admin password for our dashboard."}]}},
    {"type": "message", "session_id": "sess-B",
     "payload": {"messages": [{"role": "assistant", "content": "Done — reset link sent to carol@dataflow.io."}]}},
    {"type": "message", "session_id": "sess-C",
     "payload": {"messages": [{"role": "user", "content": "The billing gateway is timing out AGAIN. This is urgent — invoices due today and payments are failing."}]}},
    {"type": "message", "session_id": "sess-C",
     "payload": {"messages": [{"role": "assistant", "content": "I see the timeout recurring. The restart fix from last time isn't holding. Let me check the gateway logs and escalate."}]}},
    {"type": "message", "session_id": "sess-C",
     "payload": {"messages": [{"role": "assistant", "content": "Escalated to the payments team. Root cause: connection pool exhaustion. They're deploying a fix."}]}},
    {"type": "message", "session_id": "sess-D",
     "payload": {"messages": [{"role": "user", "content": "Hi, any update on the billing gateway issue? We're still blocked and this is critical for our month-end close."}]}},
]

RESOLUTIONS = [
    {"session_id": "sess-A", "status": "resolved", "resolution_summary": "Restarted payment processing service"},
    {"session_id": "sess-B", "status": "resolved", "resolution_summary": "Password reset link sent successfully"},
    {"session_id": "sess-C", "status": "open", "resolution_summary": "Billing gateway timeout recurring, escalated"},
]


@pytest.fixture(scope="module", autouse=True)
def _seeded(sw: StatewaveClient, http: httpx.Client):
    seed_subject(sw, http, SUBJECT_ID, EPISODES)
    seed_resolutions(http, SUBJECT_ID, RESOLUTIONS)
    yield
    sw.delete_subject(SUBJECT_ID)


@pytest.fixture(scope="module")
def context_text(http: httpx.Client) -> str:
    bundle = http.post("/v1/context", json={
        "subject_id": SUBJECT_ID,
        "task": "Help with the billing gateway issue",
        "max_tokens": 800,
        "session_id": "sess-D",
    }).json()
    return bundle["assembled_context"].lower()


@pytest.fixture(scope="module")
def health(http: httpx.Client) -> dict:
    return http.get(f"/v1/subjects/{SUBJECT_ID}/health").json()


@pytest.fixture(scope="module")
def handoff(http: httpx.Client) -> dict:
    return http.post(
        "/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-D", "reason": "shift handoff"},
    ).json()


def test_active_session_content_in_context(context_text: str) -> None:
    assert "update" in context_text or "month-end" in context_text


def test_open_issue_escalation_in_context(context_text: str) -> None:
    assert "escalat" in context_text or "connection pool" in context_text


def test_billing_outranks_password(context_text: str) -> None:
    assert "gateway" in context_text or "billing" in context_text


def test_repeat_issue_signal(context_text: str) -> None:
    assert "restart" in context_text or "payment processing" in context_text
    assert "timeout" in context_text and ("restart" in context_text or "again" in context_text)


def test_health_endpoint_shape(health: dict) -> None:
    assert health["state"] in ("healthy", "watch", "at_risk")
    assert isinstance(health["score"], int)
    signals = [f["signal"] for f in health["factors"]]
    assert "unresolved_issues" in signals
    assert all(f.get("signal") and f.get("detail") for f in health["factors"])


def test_handoff_includes_health(handoff: dict, health: dict) -> None:
    assert handoff.get("health_state") in ("healthy", "watch", "at_risk")
    assert handoff.get("health_state") == health["state"]
    assert isinstance(handoff.get("health_score"), int)
    notes = handoff.get("handoff_notes", "")
    assert any(icon in notes for icon in ("🔴", "🟡", "🟢"))


def test_handoff_health_factors_compact(handoff: dict) -> None:
    factors = handoff.get("health_factors", [])
    assert 0 < len(factors) <= 3


def test_resolution_aware_ranking(handoff: dict) -> None:
    active = (handoff.get("active_issue") or "").lower()
    assert "gateway" in active or "billing" in active
    assert len(handoff.get("resolution_history", [])) >= 2
    assert "Open Issues" in handoff.get("handoff_notes", "")


def test_handoff_compact_and_deterministic(http: httpx.Client, handoff: dict) -> None:
    assert handoff.get("token_estimate", 9999) <= 4000
    repeat = http.post(
        "/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-D", "reason": "shift handoff"},
    ).json()
    assert handoff["handoff_notes"] == repeat["handoff_notes"]
    assert handoff["health_score"] == repeat["health_score"]


def test_handoff_provenance(handoff: dict) -> None:
    prov = handoff.get("provenance", {})
    assert prov.get("episode_ids")
    assert prov.get("resolution_ids")
