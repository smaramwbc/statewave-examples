"""AutoGen quickstart — durable agent memory via Statewave.

Wires Statewave context into an AssistantAgent's system_message and
records each turn back as an episode so the next run benefits.

Prerequisites:
  * Statewave running locally (`docker compose up -d` from
    `statewave-examples/`).
  * `pip install "statewave>=0.10.0" pyautogen` (uses the classic
    AutoGen 0.2 API — `from autogen import AssistantAgent`).
  * `OPENAI_API_KEY` exported (or swap in any other model via
    AutoGen's `llm_config`).

Run:
  python autogen_quickstart.py
"""

from __future__ import annotations

import os

from autogen import AssistantAgent, UserProxyAgent

from statewave import StatewaveClient

from adapter import build_system_message, record_turn  # noqa: E402


SUBJECT_ID = "demo-autogen-alice"


def _seed(sw: StatewaveClient) -> None:
    sw.create_episode(
        subject_id=SUBJECT_ID,
        source="autogen-seed",
        type="conversation",
        payload={
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I'm Alice from Globex — we're on the Enterprise plan, "
                        "and I'd like email-only notifications."
                    ),
                },
                {
                    "role": "assistant",
                    "content": "Saved — Alice @ Globex, Enterprise, email-only.",
                },
            ]
        },
    )
    sw.compile_memories(SUBJECT_ID)


def main() -> None:
    sw = StatewaveClient(os.getenv("STATEWAVE_URL", "http://localhost:8100"))
    _seed(sw)

    user_msg = "What plan am I on, and what's my preferred contact channel?"

    base_prompt = (
        "You are a helpful support agent. Use the Statewave-backed memory "
        "above to ground your reply; cite specifics."
    )
    system_message = build_system_message(
        sw, SUBJECT_ID, base_prompt, task=user_msg, max_tokens=400
    )

    config_list = [{"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_API_KEY"]}]
    assistant = AssistantAgent(
        name="support",
        llm_config={"config_list": config_list, "cache_seed": None},
        system_message=system_message,
    )
    user = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False,
    )

    user.initiate_chat(assistant, message=user_msg)
    reply = assistant.last_message()["content"]
    print(reply)
    record_turn(sw, SUBJECT_ID, user_msg, reply)


if __name__ == "__main__":
    main()
