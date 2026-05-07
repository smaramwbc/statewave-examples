"""Coding agent demo — project context persists across sessions."""

from __future__ import annotations

import os
import sys

from statewave import StatewaveClient

SUBJECT_ID = "demo-coding-dev-bob"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
CONTEXT_BUDGET = 400

SESSION_1 = [
    {"messages": [
        {"role": "user", "content": "I'm Bob, working on a Python FastAPI backend called Taskflow. We use SQLAlchemy with Postgres, Alembic for migrations, and pytest for testing."},
        {"role": "assistant", "content": "Got it — Taskflow is a FastAPI + SQLAlchemy + Postgres project with Alembic migrations and pytest."},
    ]},
    {"messages": [
        {"role": "user", "content": "I prefer small focused functions, type hints everywhere, and I use Pydantic for all request/response schemas. No classes unless they add real value."},
        {"role": "assistant", "content": "Noted — functional style with type hints, Pydantic schemas, classes only when justified."},
    ]},
    {"messages": [
        {"role": "user", "content": "We decided to model task status as a finite state machine: draft → active → paused → completed → archived. Transitions are enforced in the service layer, not the DB."},
        {"role": "assistant", "content": "Good pattern — service layer validates transitions. I'll keep that in mind."},
    ]},
]

SESSION_2 = [
    {"messages": [{"role": "user", "content": "Can you help me add a PATCH endpoint to transition task status?"}]},
]


def main() -> None:
    sw = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    sw.delete_subject(SUBJECT_ID)

    print("=== Session 1: Developer introduces project and preferences ===")
    for payload in SESSION_1:
        sw.create_episode(subject_id=SUBJECT_ID, source="coding-chat", type="conversation", payload=payload)
    r = sw.compile_memories(SUBJECT_ID)
    print(f"Compiled {r.memories_created} memories")
    for m in r.memories:
        print(f"  [{m.kind}] {m.content}")

    print("\n=== Session 2: Developer returns, asks for a new feature ===")
    for payload in SESSION_2:
        sw.create_episode(subject_id=SUBJECT_ID, source="coding-chat", type="conversation", payload=payload)
    sw.compile_memories(SUBJECT_ID)

    task = "Developer wants to add a PATCH endpoint for task status transitions"
    ctx = sw.get_context(SUBJECT_ID, task=task, max_tokens=CONTEXT_BUDGET)
    print(f"\nContext bundle ({ctx.token_estimate}/{CONTEXT_BUDGET} tokens, "
          f"{len(ctx.facts)} facts, {len(ctx.procedures)} procedures, {len(ctx.episodes)} episodes):\n")
    print(ctx.assembled_context)

    sw.delete_subject(SUBJECT_ID)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Is the Statewave server running at {SERVER_URL}?", file=sys.stderr)
        sys.exit(1)
