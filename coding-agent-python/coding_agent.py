"""Coding Agent Demo — Statewave in action.

Shows how a coding assistant uses Statewave to remember a developer's
project context, tech stack, preferences, and prior architecture decisions
across multiple sessions.

Run:  python coding_agent.py
Requires: Statewave server at http://localhost:8100
          pip install statewave-py
"""

from __future__ import annotations

import os
import sys
import textwrap

from statewave import StatewaveClient

# ── Configuration ──────────────────────────────────────────────────────────

SUBJECT_ID = "demo-coding-dev-bob"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
CONTEXT_BUDGET = 400  # tokens

# ── Demo data ──────────────────────────────────────────────────────────────

SESSION_1_EPISODES = [
    {
        "label": "Bob introduces project",
        "source": "coding-chat",
        "type": "conversation",
        "payload": {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I'm Bob, working on a Python FastAPI backend called Taskflow. "
                        "We use SQLAlchemy with Postgres, Alembic for migrations, "
                        "and pytest for testing."
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        "Got it — Taskflow is a FastAPI + SQLAlchemy + Postgres project "
                        "with Alembic migrations and pytest. How can I help?"
                    ),
                },
            ]
        },
    },
    {
        "label": "Bob states coding preferences",
        "source": "coding-chat",
        "type": "conversation",
        "payload": {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I prefer small focused functions, type hints everywhere, "
                        "and I use Pydantic for all request/response schemas. "
                        "No classes unless they add real value."
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        "Noted — functional style with type hints, Pydantic schemas, "
                        "and classes only when justified."
                    ),
                },
            ]
        },
    },
    {
        "label": "Architecture discussion — task status machine",
        "source": "coding-chat",
        "type": "conversation",
        "payload": {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "We decided to model task status as a finite state machine: "
                        "draft → active → paused → completed → archived. "
                        "Transitions are enforced in the service layer, not the DB."
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        "Good pattern — the service layer validates transitions. "
                        "I'll keep that in mind when generating code."
                    ),
                },
            ]
        },
    },
]

SESSION_2_EPISODE = {
    "label": "Bob asks for a new endpoint",
    "source": "coding-chat",
    "type": "conversation",
    "payload": {
        "messages": [
            {
                "role": "user",
                "content": "Can you help me add a PATCH endpoint to transition task status?",
            },
        ]
    },
}

TASK = "Developer wants to add a PATCH endpoint for task status transitions"

# ── Simulated agent responses ─────────────────────────────────────────────

STATELESS_RESPONSE = (
    "Sure! Could you tell me what framework you're using, how statuses "
    "work in your project, and your preferred code style?"
)

STATEWAVE_RESPONSE = (
    "Here's a PATCH /tasks/{id}/status endpoint for Taskflow. It uses your "
    "FSM transition rules (draft→active→paused→completed→archived) enforced "
    "in the service layer, with Pydantic request/response schemas and type hints "
    "throughout — matching your project conventions.\n\n"
    "```python\n"
    "@router.patch('/tasks/{task_id}/status')\n"
    "async def transition_status(\n"
    "    task_id: uuid.UUID,\n"
    "    body: TransitionRequest,\n"
    "    session: AsyncSession = Depends(get_session),\n"
    ") -> TaskResponse:\n"
    "    return await task_service.transition(session, task_id, body.target_status)\n"
    "```"
)

# ── Helpers ────────────────────────────────────────────────────────────────

WIDTH = 72


def banner(text: str) -> None:
    print(f"\n{'═' * WIDTH}")
    print(f"  {text}")
    print(f"{'═' * WIDTH}")


def step(label: str) -> None:
    print(f"\n▸ {label}")


def show(label: str, body: str) -> None:
    print(f"\n┌─ {label}")
    for line in body.strip().splitlines():
        print(f"│  {line}")
    print("└" + "─" * (WIDTH - 1))


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    client = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)

    # Clean slate
    banner("SETUP — clean slate")
    step("Deleting previous demo data…")
    client.delete_subject(SUBJECT_ID)
    print("  ✓ clean")

    # ── Session 1 ──────────────────────────────────────────────────────────
    banner("SESSION 1 — Developer introduces project and preferences")

    for ep in SESSION_1_EPISODES:
        step(f"Recording: {ep['label']}")
        client.create_episode(
            subject_id=SUBJECT_ID,
            source=ep["source"],
            type=ep["type"],
            payload=ep["payload"],
        )
        print("  ✓ ingested")

    step("Compiling memories from session 1…")
    result = client.compile_memories(SUBJECT_ID)
    print(f"  ✓ {result.memories_created} memories compiled")
    for m in result.memories:
        print(f"    [{m.kind}] {m.summary[:60]}")

    # ── Session 2 ──────────────────────────────────────────────────────────
    banner("SESSION 2 — Developer returns, asks for a new feature")

    step(f"Recording: {SESSION_2_EPISODE['label']}")
    client.create_episode(
        subject_id=SUBJECT_ID,
        source=SESSION_2_EPISODE["source"],
        type=SESSION_2_EPISODE["type"],
        payload=SESSION_2_EPISODE["payload"],
    )
    print("  ✓ ingested")

    step("Compiling session 2 memories…")
    result = client.compile_memories(SUBJECT_ID)
    print(f"  ✓ {result.memories_created} new memories compiled")

    # ── Context retrieval ──────────────────────────────────────────────────
    banner("CONTEXT — What does Statewave give the coding agent?")

    step(f"Assembling context (budget={CONTEXT_BUDGET} tokens)…")
    ctx = client.get_context(SUBJECT_ID, task=TASK, max_tokens=CONTEXT_BUDGET)
    print(f"  ✓ {ctx.token_estimate} tokens")
    print(f"  ✓ {len(ctx.facts)} facts, {len(ctx.procedures)} procedures, {len(ctx.episodes)} episodes")

    show("Assembled context", ctx.assembled_context)

    # ── Comparison ─────────────────────────────────────────────────────────
    banner("COMPARISON — With vs. without memory")

    show("Without Statewave (stateless)", STATELESS_RESPONSE)
    show("With Statewave (memory-aware)", STATEWAVE_RESPONSE)

    # ── Cleanup ────────────────────────────────────────────────────────────
    banner("CLEANUP")
    step("Deleting demo data…")
    client.delete_subject(SUBJECT_ID)
    print("  ✓ done")

    print(f"\n{'═' * WIDTH}")
    print("  Demo complete. Statewave gave the coding agent full project context.")
    print(f"{'═' * WIDTH}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        print("  Is the Statewave server running at", SERVER_URL, "?", file=sys.stderr)
        sys.exit(1)
