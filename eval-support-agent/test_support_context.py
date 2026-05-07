"""Context quality eval — assert Statewave returns the right facts for a
returning enterprise customer across three sessions.

Run:  pytest test_support_context.py -v
"""

from __future__ import annotations

import httpx
import pytest
from statewave import StatewaveClient

from conftest import seed_subject

SUBJECT_ID = "eval-support-alice"

EPISODES = [
    {"session_id": "sess-001",
     "payload": {"messages": [
         {"role": "user", "content": "Hi, I'm Alice Chen from Globex Corporation. We're on the Enterprise plan."},
         {"role": "assistant", "content": "Welcome Alice! How can I help you today?"},
     ]}},
    {"session_id": "sess-001",
     "payload": {"messages": [
         {"role": "user", "content": "I want to integrate via the Python SDK. We also need webhook notifications for real-time updates."},
         {"role": "assistant", "content": "Great choices! The Python SDK and webhooks work well together."},
     ]}},
    {"session_id": "sess-001",
     "payload": {"messages": [
         {"role": "user", "content": "Actually, we're blocked on SSO configuration. The SAML callback URL keeps failing."},
         {"role": "assistant", "content": "I see — let me look into the SSO issue. Can you share the error?"},
         {"role": "user", "content": "It returns a 403 with 'invalid assertion' after the IdP redirect."},
     ]}},
    {"session_id": "sess-001",
     "payload": {"messages": [
         {"role": "assistant", "content": "I've escalated this to our engineering team. Ticket: ENG-4521."},
         {"role": "user", "content": "Thanks, please keep me posted."},
     ]}},
    {"session_id": "sess-002",
     "payload": {"messages": [
         {"role": "user", "content": "Hi, any update on the SSO issue? Ticket ENG-4521."},
         {"role": "assistant", "content": "Engineering pushed a fix yesterday. Can you try the SAML flow again?"},
         {"role": "user", "content": "It works now! SSO is configured."},
     ]}},
    {"session_id": "sess-002",
     "payload": {"messages": [
         {"role": "user", "content": "One more thing — can we get a consolidated invoice for our 3 workspaces?"},
         {"role": "assistant", "content": "Done. Consolidated billing is enabled for Globex."},
     ]}},
]


@pytest.fixture(scope="module", autouse=True)
def _seeded(sw: StatewaveClient, http: httpx.Client):
    seed_subject(sw, http, SUBJECT_ID, EPISODES)
    yield
    sw.delete_subject(SUBJECT_ID)


def assembled(sw: StatewaveClient, task: str, max_tokens: int = 600) -> str:
    return sw.get_context(SUBJECT_ID, task, max_tokens=max_tokens).assembled_context.lower()


def test_identity_recall(sw: StatewaveClient) -> None:
    ctx = assembled(sw, "Help this customer with their billing question")
    assert "alice chen" in ctx
    assert "globex" in ctx
    assert "enterprise" in ctx


def test_preference_recall(sw: StatewaveClient) -> None:
    ctx = assembled(sw, "Suggest an integration approach for this customer")
    assert "python sdk" in ctx
    assert "webhook" in ctx


def test_history_recall(sw: StatewaveClient) -> None:
    ctx = assembled(sw, "Follow up on their open issue")
    assert "sso" in ctx


def test_token_budget_respected(sw: StatewaveClient) -> None:
    bundle = sw.get_context(SUBJECT_ID, "Help with password reset", max_tokens=500)
    assert bundle.token_estimate <= 500
    text = bundle.assembled_context.lower()
    assert "alice" in text or "globex" in text


def test_provenance_traces_to_source(sw: StatewaveClient) -> None:
    bundle = sw.get_context(SUBJECT_ID, "Summarize this customer's history", max_tokens=600)
    prov = bundle.provenance
    assert prov.get("fact_ids") or prov.get("summary_ids") or prov.get("episode_ids")
    assert bundle.facts
    assert all(f.source_episode_ids for f in bundle.facts)


def test_compilation_idempotent(sw: StatewaveClient) -> None:
    assert sw.compile_memories(SUBJECT_ID).memories_created == 0


def test_memory_count_reasonable(sw: StatewaveClient) -> None:
    search = sw.search_memories(SUBJECT_ID, limit=100)
    assert 5 <= len(search.memories) <= 30
    assert sum(1 for m in search.memories if m.kind == "profile_fact") >= 3
