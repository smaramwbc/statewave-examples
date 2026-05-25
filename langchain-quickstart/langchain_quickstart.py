"""LangChain quickstart — durable agent memory via Statewave.

Shows how to plug Statewave into a LangChain chain so the model gets a
ranked, token-bounded, provenance-tagged context bundle every turn —
no manual prompt stuffing, no second vector DB to operate.

Prerequisites:
  * Statewave running locally (`docker compose up -d` from
    `statewave-examples/`).
  * `pip install "statewave>=0.10.0" langchain langchain-openai`.
  * `OPENAI_API_KEY` exported (or swap the LLM for another provider).

Run:
  python langchain_quickstart.py
"""

from __future__ import annotations

import os

from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from statewave import StatewaveClient

from adapter import StatewaveMemory  # noqa: E402 — local sibling module


SUBJECT_ID = "demo-langchain-alice"


def _seed(sw: StatewaveClient) -> None:
    """Seed a couple of prior turns so the chain has something to retrieve."""
    history = [
        (
            "hi, I'm Alice — I work at Globex on the Enterprise plan.",
            "Welcome Alice! Glad to have Globex on the Enterprise plan.",
        ),
        (
            "I prefer email over Slack for notifications, please.",
            "Got it — email-only notifications saved.",
        ),
    ]
    for user_msg, assistant_msg in history:
        sw.create_episode(
            subject_id=SUBJECT_ID,
            source="langchain-seed",
            type="conversation",
            payload={
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ]
            },
        )
    sw.compile_memories(SUBJECT_ID)


def main() -> None:
    sw = StatewaveClient(os.getenv("STATEWAVE_URL", "http://localhost:8100"))
    _seed(sw)

    prompt = PromptTemplate(
        input_variables=["statewave_context", "input"],
        template=(
            "You are a helpful support agent. Use the durable customer memory "
            "below to ground your reply; ignore any field that isn't relevant.\n\n"
            "{statewave_context}\n\n"
            "User: {input}\n"
            "Assistant:"
        ),
    )

    chain = LLMChain(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        prompt=prompt,
        memory=StatewaveMemory(client=sw, subject_id=SUBJECT_ID, max_tokens=400),
    )

    # Returning user — the chain pulls Alice's plan + preferred channel from
    # Statewave on its own and grounds the reply in it.
    reply = chain.predict(input="What plan am I on, and how should we contact me?")
    print(reply)


if __name__ == "__main__":
    main()
