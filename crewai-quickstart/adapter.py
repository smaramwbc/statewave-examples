"""CrewAI ↔ Statewave adapter.

CrewAI doesn't have a pluggable memory base class the way LangChain
does, so the integration is just two small helpers:

- `build_task_description(...)` — prepend a Statewave context bundle to
  a Task's description before the Crew runs. Retrieval is biased toward
  the task description, so the agent gets the *task-relevant* slice of
  memory.
- `record_crew_output(...)` — record the Crew's output back to Statewave
  as an episode, so the next run benefits from it.

No CrewAI imports here — the adapter is dependency-free, which makes
the smoke test runnable without CrewAI installed.
"""

from __future__ import annotations

from statewave import StatewaveClient


def build_task_description(
    client: StatewaveClient,
    subject_id: str,
    task_description: str,
    *,
    max_tokens: int = 1000,
) -> str:
    """Return ``<statewave-context>\\n---\\n<task_description>``.

    The Statewave bundle is fetched for the task description itself, so
    retrieval is task-relevant.
    """
    context = client.get_context_string(
        subject_id, task=task_description, max_tokens=max_tokens
    )
    return f"{context}\n\n---\n\n{task_description}"


def record_crew_output(
    client: StatewaveClient,
    subject_id: str,
    task_description: str,
    output: str,
    *,
    crew_name: str = "crewai",
) -> None:
    """Record a Crew's output as a Statewave episode."""
    client.create_episode(
        subject_id=subject_id,
        source=crew_name,
        type="crew.run",
        payload={"task": task_description, "output": output},
    )
