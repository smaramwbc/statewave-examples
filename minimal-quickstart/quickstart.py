"""Minimal Statewave quickstart — record, compile, retrieve context."""

import os

from statewave import StatewaveClient

SUBJECT = "demo-user-1"


def main() -> None:
    sw = StatewaveClient(
        base_url=os.getenv("STATEWAVE_URL", "http://localhost:8100"),
        api_key=os.getenv("STATEWAVE_API_KEY"),
    )

    print("Recording episodes...")
    sw.create_episode(
        subject_id=SUBJECT,
        source="chat",
        type="conversation",
        payload={"messages": [
            {"role": "user", "content": "My name is Alice and I work at Acme Corp."},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
        ]},
    )
    sw.create_episode(
        subject_id=SUBJECT,
        source="chat",
        type="conversation",
        payload={"messages": [
            {"role": "user", "content": "I prefer Python and use VS Code."},
        ]},
    )

    print("Compiling memories...")
    result = sw.compile_memories(SUBJECT)
    print(f"  {result.memories_created} memories created")
    for m in result.memories:
        print(f"  [{m.kind}] {m.content}")

    print("\nRetrieving context bundle...")
    ctx = sw.get_context(SUBJECT, task="Help the user set up a new project")
    print(f"  {ctx.token_estimate} tokens, {len(ctx.facts)} facts, {len(ctx.episodes)} episodes")
    print(f"\n{ctx.assembled_context}")

    sw.delete_subject(SUBJECT)


if __name__ == "__main__":
    main()
