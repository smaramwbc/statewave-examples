"""Handoff-pack eval — active issue, customer facts, attempted steps,
deprioritized resolutions, compactness, provenance, determinism.

Run:  pytest test_handoff.py -v
"""

from __future__ import annotations

import httpx
import pytest
from statewave import StatewaveClient

from conftest import seed_resolutions, seed_subject

SUBJECT_ID = "eval-handoff-bob"

EPISODES = [
    {"type": "message", "session_id": "sess-001",
     "payload": {"messages": [{"role": "user", "content": "Hi, I'm Bob Martinez from Acme Inc. Enterprise plan. I can't reset my password."}]}},
    {"type": "message", "session_id": "sess-001",
     "payload": {"messages": [{"role": "assistant", "content": "Hi Bob! I've sent a password reset link to bob@acme.io."}]}},
    {"type": "message", "session_id": "sess-001",
     "payload": {"messages": [{"role": "user", "content": "Got it, works now. Thanks!"}]}},
    {"type": "message", "session_id": "sess-002",
     "payload": {"messages": [{"role": "user", "content": "We're hitting 429 errors on /v1/episodes. Our batch sends ~200 req/s."}]}},
    {"type": "message", "session_id": "sess-002",
     "payload": {"messages": [{"role": "assistant", "content": "I've increased your rate limit to 500 req/s. The change is live."}]}},
    {"type": "message", "session_id": "sess-002",
     "payload": {"messages": [{"role": "user", "content": "Confirmed, no more 429s. Thanks!"}]}},
    {"type": "message", "session_id": "sess-003",
     "payload": {"messages": [{"role": "user", "content": "Our nightly data export has been failing 3 days. Times out after 5 min. Export ID: EXP-9912."}]}},
    {"type": "message", "session_id": "sess-003",
     "payload": {"messages": [{"role": "assistant", "content": "I see export EXP-9912 timing out. Let me check the backend logs."}]}},
    {"type": "message", "session_id": "sess-003",
     "payload": {"messages": [{"role": "assistant", "content": "Dataset grew to 2.1M rows. Bumping timeout to 15min didn't hold. Escalating to engineering."}]}},
    {"type": "message", "session_id": "sess-003",
     "payload": {"messages": [{"role": "user", "content": "Please hurry — compliance team needs this data by Friday."}]}},
]

RESOLUTIONS = [
    {"session_id": "sess-001", "status": "resolved", "resolution_summary": "Password reset link sent, user confirmed working"},
    {"session_id": "sess-002", "status": "resolved", "resolution_summary": "Rate limit increased to 500 req/s"},
    {"session_id": "sess-003", "status": "open", "resolution_summary": "Data export timing out, escalated to engineering"},
]


@pytest.fixture(scope="module", autouse=True)
def _seeded(sw: StatewaveClient, http: httpx.Client):
    seed_subject(sw, http, SUBJECT_ID, EPISODES)
    seed_resolutions(http, SUBJECT_ID, RESOLUTIONS)
    yield
    sw.delete_subject(SUBJECT_ID)


@pytest.fixture(scope="module")
def handoff(http: httpx.Client) -> dict:
    resp = http.post(
        "/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-003", "reason": "escalation to engineering"},
    )
    resp.raise_for_status()
    return resp.json()


def lower(s: str) -> str:
    return (s or "").lower()


def test_active_issue_surfaced(handoff: dict) -> None:
    active = lower(handoff["active_issue"])
    assert "export" in active or "exp-9912" in active
    assert "Active Issue" in handoff["handoff_notes"]


def test_customer_facts_present(handoff: dict) -> None:
    summary = lower(handoff["customer_summary"])
    facts = [lower(f) for f in handoff["key_facts"]]
    assert "bob" in summary or "acme" in summary or any("bob" in f or "acme" in f for f in facts)
    assert "enterprise" in summary or any("enterprise" in f for f in facts)


def test_resolved_items_deprioritized(handoff: dict) -> None:
    notes = handoff["handoff_notes"]
    assert "Previously Resolved" in notes
    active_pos = notes.find("Active Issue")
    resolved_pos = notes.find("Previously Resolved")
    assert active_pos != -1
    assert resolved_pos == -1 or active_pos < resolved_pos
    assert "Open Issues" in notes and "sess-003" in notes


def test_active_issue_signal_preserved(handoff: dict) -> None:
    assert handoff["token_estimate"] <= 4000
    assert "EXP-9912" in handoff["handoff_notes"]
    assert "password" not in lower(handoff["active_issue"])


def test_provenance_preserved(handoff: dict) -> None:
    prov = handoff["provenance"]
    assert prov.get("episode_ids")
    assert prov.get("resolution_ids")


def test_determinism(http: httpx.Client, handoff: dict) -> None:
    resp = http.post(
        "/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "sess-003", "reason": "escalation to engineering"},
    )
    repeat = resp.json()
    assert handoff["handoff_notes"] == repeat["handoff_notes"]
    assert handoff["active_issue"] == repeat["active_issue"]
