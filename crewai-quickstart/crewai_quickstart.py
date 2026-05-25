"""CrewAI quickstart — agents sharing durable memory via Statewave.

Shows how to inject a Statewave context bundle into a CrewAI Task and
record the Crew's output back, so subsequent runs benefit from prior work.

Prerequisites:
  * Statewave running locally (`docker compose up -d` from
    `statewave-examples/`).
  * `pip install "statewave>=0.10.0" crewai`.
  * An LLM key for whichever model CrewAI uses (e.g. `OPENAI_API_KEY`).

Run:
  python crewai_quickstart.py
"""

from __future__ import annotations

import os

from crewai import Agent, Crew, Task

from statewave import StatewaveClient

from adapter import build_task_description, record_crew_output  # noqa: E402


SUBJECT_ID = "demo-crewai-globex"


def _seed(sw: StatewaveClient) -> None:
    """Seed one durable fact about the account."""
    sw.create_episode(
        subject_id=SUBJECT_ID,
        source="crewai-seed",
        type="note",
        payload={
            "text": (
                "Globex is on the Enterprise plan; renewal is in Q3. "
                "Primary contact: alice@globex.com."
            )
        },
    )
    sw.compile_memories(SUBJECT_ID)


def main() -> None:
    sw = StatewaveClient(os.getenv("STATEWAVE_URL", "http://localhost:8100"))
    _seed(sw)

    raw_task = (
        "Draft a brief reply to the customer's question about renewal "
        "pricing. Keep it to 3 sentences."
    )
    task_with_context = build_task_description(sw, SUBJECT_ID, raw_task, max_tokens=400)

    support_agent = Agent(
        role="Senior support engineer",
        goal="Reply to customers grounded in the durable account context.",
        backstory=(
            "You have access to Statewave-backed memory for this account. "
            "Cite specifics (plan, renewal, contact) when relevant."
        ),
        verbose=False,
    )

    task = Task(
        description=task_with_context,
        agent=support_agent,
        expected_output="A short, factual reply mentioning the customer's plan and contact channel.",
    )
    crew = Crew(agents=[support_agent], tasks=[task], verbose=False)

    result = crew.kickoff()
    print(result)
    record_crew_output(sw, SUBJECT_ID, raw_task, str(result))


if __name__ == "__main__":
    main()
