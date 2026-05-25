"""AutoGen ↔ Statewave adapter.

AutoGen's `AssistantAgent` is parameterised by a `system_message` string,
which makes Statewave integration a matter of building (or refreshing)
that string from a Statewave context bundle.

Three small helpers cover the common cases:

- `build_system_message(...)` — produce a system_message string at agent
  construction time, frozen for the rest of the chat.
- `update_system_message(...)` — refresh an agent's system_message just
  before the next turn, so multi-turn chats see fresh context.
- `record_turn(...)` — record one user/assistant turn back as an episode.

No AutoGen imports here — the adapter is dependency-free, so the smoke
test runs without AutoGen installed.
"""

from __future__ import annotations

from statewave import StatewaveClient


def build_system_message(
    client: StatewaveClient,
    subject_id: str,
    base_prompt: str,
    *,
    task: str = "answer the user's next question",
    max_tokens: int = 1000,
) -> str:
    """Build an AutoGen system_message with Statewave context prepended.

    ``base_prompt`` is the agent's static role/instructions; the
    Statewave bundle is fetched for ``task`` and placed above it so the
    model sees memory first, then its role.
    """
    context = client.get_context_string(subject_id, task=task, max_tokens=max_tokens)
    return f"{context}\n\n---\n\n{base_prompt}"


def update_system_message(
    agent,
    client: StatewaveClient,
    subject_id: str,
    base_prompt: str,
    *,
    task: str,
    max_tokens: int = 1000,
) -> None:
    """Refresh ``agent.system_message`` with a fresh Statewave bundle.

    ``agent`` is duck-typed — anything with an ``update_system_message``
    method works. AutoGen's ``AssistantAgent`` has exactly that.
    """
    agent.update_system_message(
        build_system_message(
            client, subject_id, base_prompt, task=task, max_tokens=max_tokens
        )
    )


def record_turn(
    client: StatewaveClient,
    subject_id: str,
    user_msg: str,
    assistant_msg: str,
    *,
    agent_name: str = "autogen",
) -> None:
    """Record one user/assistant turn as a Statewave episode."""
    client.create_episode(
        subject_id=subject_id,
        source=agent_name,
        type="conversation",
        payload={
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg},
            ]
        },
    )
