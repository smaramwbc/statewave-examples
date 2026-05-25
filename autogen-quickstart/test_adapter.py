"""Smoke test — AutoGen adapter helpers shape correctly.

No external services: Statewave is mocked, AutoGen is not invoked. The
adapter has no AutoGen imports, so this test runs even without AutoGen
installed.

    pytest test_adapter.py
"""

from __future__ import annotations

from unittest.mock import MagicMock

from adapter import build_system_message, record_turn, update_system_message


def _mock_client(context: str = "## Profile\n- Plan: Enterprise\n") -> MagicMock:
    client = MagicMock()
    client.get_context_string.return_value = context
    return client


def test_build_system_message_prepends_context():
    client = _mock_client(context="## Profile\n- Plan: Enterprise\n")

    out = build_system_message(
        client, "u1", "You are a helpful agent.", task="plan?", max_tokens=300
    )

    assert "## Profile" in out
    assert "You are a helpful agent." in out
    # Context first, base prompt below.
    assert out.index("## Profile") < out.index("You are a helpful agent.")
    client.get_context_string.assert_called_once_with("u1", task="plan?", max_tokens=300)


def test_build_system_message_default_task_and_budget():
    client = _mock_client()
    build_system_message(client, "u1", "Be helpful.")
    kw = client.get_context_string.call_args.kwargs
    assert kw["max_tokens"] == 1000
    # A default task is supplied so retrieval still gets a signal.
    assert kw["task"]


def test_update_system_message_refreshes_via_the_agent():
    client = _mock_client()
    agent = MagicMock()

    update_system_message(agent, client, "u1", "Be helpful.", task="hi")

    agent.update_system_message.assert_called_once()
    new_msg = agent.update_system_message.call_args.args[0]
    assert "Be helpful." in new_msg


def test_record_turn_writes_episode_with_both_messages():
    client = _mock_client()

    record_turn(client, "u1", "hi", "hello", agent_name="autogen-test")

    client.create_episode.assert_called_once()
    kw = client.create_episode.call_args.kwargs
    assert kw["subject_id"] == "u1"
    assert kw["source"] == "autogen-test"
    assert kw["type"] == "conversation"
    msgs = kw["payload"]["messages"]
    assert [m["content"] for m in msgs] == ["hi", "hello"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]


def test_record_turn_default_source():
    client = _mock_client()
    record_turn(client, "u1", "hi", "hello")
    assert client.create_episode.call_args.kwargs["source"] == "autogen"
