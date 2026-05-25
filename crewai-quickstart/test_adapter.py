"""Smoke test — CrewAI adapter wires Statewave context in and records output back.

No external services: Statewave is mocked, CrewAI is not invoked. The
adapter has no CrewAI imports, so this test runs even without CrewAI
installed.

    pytest test_adapter.py
"""

from __future__ import annotations

from unittest.mock import MagicMock

from adapter import build_task_description, record_crew_output


def _mock_client(context: str = "## Account\n- Plan: Enterprise\n") -> MagicMock:
    client = MagicMock()
    client.get_context_string.return_value = context
    return client


def test_build_task_description_prepends_context():
    client = _mock_client(context="## Account\n- Plan: Enterprise\n")

    out = build_task_description(client, "acct-1", "Draft a reply.", max_tokens=500)

    assert "## Account" in out
    assert "Draft a reply." in out
    # Statewave context comes before the task body.
    assert out.index("## Account") < out.index("Draft a reply.")
    client.get_context_string.assert_called_once_with(
        "acct-1", task="Draft a reply.", max_tokens=500
    )


def test_build_task_description_default_token_budget():
    client = _mock_client()
    build_task_description(client, "acct-1", "do a thing")
    assert client.get_context_string.call_args.kwargs["max_tokens"] == 1000


def test_record_crew_output_writes_an_episode():
    client = _mock_client()

    record_crew_output(client, "acct-1", "task description", "the reply", crew_name="my-crew")

    client.create_episode.assert_called_once()
    kw = client.create_episode.call_args.kwargs
    assert kw["subject_id"] == "acct-1"
    assert kw["source"] == "my-crew"
    assert kw["type"] == "crew.run"
    assert kw["payload"] == {"task": "task description", "output": "the reply"}


def test_record_crew_output_default_source():
    client = _mock_client()
    record_crew_output(client, "acct-1", "t", "o")
    assert client.create_episode.call_args.kwargs["source"] == "crewai"
