"""Shared pytest fixtures for the support-agent evals.

The handoff, resolutions, and session-aware context endpoints aren't on the
SDK yet, so the eval drops down to raw httpx for those calls. The plain
ingest/compile/get_context paths still go through the SDK.
"""

from __future__ import annotations

import os

import httpx
import pytest
from statewave import StatewaveClient

SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")


@pytest.fixture(scope="module")
def sw() -> StatewaveClient:
    return StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)


@pytest.fixture(scope="module")
def http() -> httpx.Client:
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    with httpx.Client(base_url=SERVER_URL, headers=headers) as client:
        yield client


def seed_subject(
    sw: StatewaveClient,
    http: httpx.Client,
    subject_id: str,
    episodes: list[dict],
) -> None:
    """Seed episodes via raw POST so we can pass session_id (not yet on SDK),
    then trigger compilation via the SDK."""
    sw.delete_subject(subject_id)
    for ep in episodes:
        http.post("/v1/episodes", json={
            "subject_id": subject_id,
            "source": ep.get("source", "support-chat"),
            "type": ep.get("type", "conversation"),
            "payload": ep["payload"],
            "metadata": ep.get("metadata", {}),
            "session_id": ep.get("session_id"),
        })
    sw.compile_memories(subject_id)


def seed_resolutions(http: httpx.Client, subject_id: str, resolutions: list[dict]) -> None:
    for r in resolutions:
        http.post("/v1/resolutions", json={"subject_id": subject_id, **r})
