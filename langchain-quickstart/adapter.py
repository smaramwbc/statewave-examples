"""LangChain ↔ Statewave adapter.

A `BaseMemory` subclass that, on every chain call, retrieves a
token-bounded, provenance-tagged context bundle from Statewave for the
active subject and exposes it under `memory_key` (default
`statewave_context`). After the chain runs, `save_context` records the
input/output as a Statewave episode so the next call benefits from it.

Compared to LangChain's built-in conversation memories, this gives you
Statewave's ranked retrieval, token budgeting, and provenance — without
changing the prompt template (just include `{statewave_context}` in it).
"""

from __future__ import annotations

from typing import Any

from langchain_core.memory import BaseMemory
from pydantic import ConfigDict

from statewave import StatewaveClient


class StatewaveMemory(BaseMemory):
    """LangChain memory backed by Statewave."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: StatewaveClient
    subject_id: str
    max_tokens: int = 1000
    memory_key: str = "statewave_context"
    input_key: str = "input"
    output_key: str = "output"

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Pull a fresh, task-relevant context bundle from Statewave.

        The bundle is built for the current `input`, so retrieval is
        biased toward what the user is actually asking about right now.
        """
        task = inputs.get(self.input_key, "")
        ctx = self.client.get_context_string(
            self.subject_id, task=task, max_tokens=self.max_tokens
        )
        return {self.memory_key: ctx}

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """Record the (input, output) pair as an episode for next time."""
        self.client.create_episode(
            subject_id=self.subject_id,
            source="langchain",
            type="conversation",
            payload={
                "messages": [
                    {"role": "user", "content": inputs.get(self.input_key, "")},
                    {"role": "assistant", "content": outputs.get(self.output_key, "")},
                ]
            },
        )

    def clear(self) -> None:
        """No-op: Statewave is append-only.

        Clearing a subject's memory is a deliberate operator action —
        call `client.delete_subject(subject_id)` explicitly. We avoid
        wiring it into `clear()` so a routine chain reset can't
        accidentally drop durable memory.
        """
