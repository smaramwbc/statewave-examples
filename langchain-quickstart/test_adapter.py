"""Smoke test — StatewaveMemory wires Statewave into LangChain correctly.

No external services: Statewave is mocked, no LLM is called. Requires
LangChain installed (the adapter subclasses `BaseMemory`), but neither
`langchain-openai` nor an API key.

    pip install langchain
    pytest test_adapter.py
"""

from __future__ import annotations

from unittest.mock import MagicMock

from adapter import StatewaveMemory


def _mock_client(context: str = "## Customer\n- Plan: Enterprise\n") -> MagicMock:
    """A stand-in StatewaveClient exposing the two methods StatewaveMemory uses."""
    client = MagicMock()
    client.get_context_string.return_value = context
    return client


def test_memory_variables_advertises_the_default_key():
    mem = StatewaveMemory(client=_mock_client(), subject_id="u1")
    assert mem.memory_variables == ["statewave_context"]


def test_memory_key_is_overridable():
    mem = StatewaveMemory(
        client=_mock_client(), subject_id="u1", memory_key="customer_memory"
    )
    assert mem.memory_variables == ["customer_memory"]


def test_load_memory_variables_returns_statewave_context():
    client = _mock_client(context="## Customer\n- Plan: Enterprise\n")
    mem = StatewaveMemory(client=client, subject_id="u1", max_tokens=400)

    out = mem.load_memory_variables({"input": "what's my plan?"})

    assert out == {"statewave_context": "## Customer\n- Plan: Enterprise\n"}
    client.get_context_string.assert_called_once_with(
        "u1", task="what's my plan?", max_tokens=400
    )


def test_save_context_writes_an_episode():
    client = _mock_client()
    mem = StatewaveMemory(client=client, subject_id="u1")

    mem.save_context({"input": "hi"}, {"output": "hello!"})

    client.create_episode.assert_called_once()
    kwargs = client.create_episode.call_args.kwargs
    assert kwargs["subject_id"] == "u1"
    assert kwargs["source"] == "langchain"
    assert kwargs["type"] == "conversation"
    assert kwargs["payload"]["messages"][0]["content"] == "hi"
    assert kwargs["payload"]["messages"][1]["content"] == "hello!"


def test_clear_is_a_noop():
    """Statewave is append-only — clear() must not accidentally drop a subject."""
    client = _mock_client()
    mem = StatewaveMemory(client=client, subject_id="u1")

    mem.clear()

    client.delete_subject.assert_not_called()
    client.create_episode.assert_not_called()
