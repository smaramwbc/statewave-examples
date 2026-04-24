"""Minimal Statewave quickstart — record, compile, retrieve context."""

import os

from statewave import StatewaveClient

SUBJECT = "demo-user-1"


def main():
    sw = StatewaveClient(
        base_url=os.getenv("STATEWAVE_URL", "http://localhost:8100"),
        api_key=os.getenv("STATEWAVE_API_KEY"),
    )

    # 1. Record episodes
    print("Recording episodes...")
    sw.create_episode(
        subject_id=SUBJECT,
        source="chat",
        type="conversation",
        payload={
            "messages": [
                {"role": "user", "content": "My name is Alice and I work at Acme Corp."},
                {"role": "assistant", "content": "Nice to meet you, Alice!"},
            ]
        },
    )
    sw.create_episode(
        subject_id=SUBJECT,
        source="chat",
        type="conversation",
        payload={
            "messages": [
                {"role": "user", "content": "I prefer Python and use VS Code."},
            ]
        },
    )

    # 2. Compile memories
    print("Compiling memories...")
    result = sw.compile_memories(SUBJECT)
    print(f"  Created {result.memories_created} memories")
    for m in result.memories:
        print(f"    [{m.kind}] {m.content[:80]}")

    # 3. Retrieve context
    print("\nRetrieving context bundle...")
    ctx = sw.get_context(SUBJECT, task="Help the user set up a new project")
    print(f"  Token estimate: {ctx.token_estimate}")
    print(f"\n--- Assembled context ---\n{ctx.assembled_context}")

    # 4. Inspect timeline
    tl = sw.get_timeline(SUBJECT)
    print(f"\nTimeline: {len(tl.episodes)} episodes, {len(tl.memories)} memories")

    # 5. Cleanup
    sw.delete_subject(SUBJECT)
    print("\nSubject deleted.")


if __name__ == "__main__":
    main()
