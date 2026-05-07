"""Support agent demo — returning customer recognised across sessions.

Shows ingest → compile → context across two sessions, then a handoff pack
for escalation. The handoff endpoint is not yet on the SDK, so we call
`/v1/handoff` directly with httpx.
"""

from __future__ import annotations

import os
import sys

import httpx
from statewave import StatewaveClient

SUBJECT_ID = "demo-support-alice"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
CONTEXT_BUDGET = 300

SESSION_1 = [
    {"messages": [
        {"role": "user", "content": "Hi, my name is Alice Chen and I work at Globex Corporation. I am on the Enterprise plan."},
        {"role": "assistant", "content": "Welcome Alice! How can I help you today?"},
    ]},
    {"messages": [
        {"role": "user", "content": "I prefer email notifications over Slack. My email is alice@globex.com."},
        {"role": "assistant", "content": "Got it, I have updated your notification preference to email."},
    ]},
    {"messages": [
        {"role": "user", "content": "We had a billing issue last week — we were double-charged for the March invoice."},
        {"role": "assistant", "content": "I see the double charge. I have initiated a refund for the duplicate payment. You should see it within 3-5 business days."},
    ]},
]

SESSION_2 = [
    {"messages": [{"role": "user", "content": "Can you help me upgrade our team from 5 to 20 seats?"}]},
]


def main() -> None:
    sw = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)
    sw.delete_subject(SUBJECT_ID)

    print("=== Session 1: First contact ===")
    for payload in SESSION_1:
        sw.create_episode(subject_id=SUBJECT_ID, source="support-chat", type="conversation", payload=payload)
    r = sw.compile_memories(SUBJECT_ID)
    print(f"Compiled {r.memories_created} memories from {len(SESSION_1)} episodes")
    for m in r.memories:
        print(f"  [{m.kind}] {m.content}")

    recompile = sw.compile_memories(SUBJECT_ID)
    print(f"Recompile: {recompile.memories_created} new memories (idempotent)")

    print("\n=== Session 2: Alice returns a week later ===")
    for payload in SESSION_2:
        sw.create_episode(subject_id=SUBJECT_ID, source="support-chat", type="conversation", payload=payload)
    sw.compile_memories(SUBJECT_ID)

    task = "Customer is asking about upgrading their team seats"
    ctx = sw.get_context(SUBJECT_ID, task=task, max_tokens=CONTEXT_BUDGET)

    print(f"\nContext bundle ({ctx.token_estimate}/{CONTEXT_BUDGET} tokens, "
          f"{len(ctx.facts)} facts, {len(ctx.episodes)} episodes):\n")
    print(ctx.assembled_context)

    print("\n=== Provenance — each fact traces back to a source episode ===")
    episodes_by_id = {str(e.id): e for e in ctx.episodes}
    for f in ctx.facts[:4]:
        for eid in f.source_episode_ids:
            ep = episodes_by_id.get(str(eid))
            if ep:
                first_msg = ep.payload.get("messages", [{}])[0].get("content", "?")
                print(f"  {f.content!r}\n    ← {first_msg[:60]}...")

    print("\n=== Handoff pack (escalation to billing specialist) ===")
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    resp = httpx.post(
        f"{SERVER_URL}/v1/handoff",
        json={"subject_id": SUBJECT_ID, "session_id": "demo-session-2", "reason": "escalation to billing specialist"},
        headers=headers,
    )
    resp.raise_for_status()
    handoff = resp.json()
    print(f"Customer:      {handoff['customer_summary']}")
    print(f"Active issue:  {handoff['active_issue'] or '(none detected)'}")
    print(f"Key facts:     {len(handoff['key_facts'])}")
    print(f"Resolutions:   {len(handoff['resolution_history'])}")
    print(f"Tokens:        {handoff['token_estimate']}")
    print("\n--- Handoff notes (first 10 lines) ---")
    for line in handoff["handoff_notes"].split("\n")[:10]:
        print(line)

    sw.delete_subject(SUBJECT_ID)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Is the Statewave server running at {SERVER_URL}?", file=sys.stderr)
        sys.exit(1)
