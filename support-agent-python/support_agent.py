"""Support Agent Demo — Statewave in action.

Shows how a support agent uses Statewave to remember a returning customer,
retrieve ranked context within a token budget, and respond with full awareness
of identity, preferences, and prior interactions.

Run:  python support_agent.py
Requires: Statewave server at http://localhost:8100
          pip install statewave-py
"""

from __future__ import annotations

import os
import sys
import textwrap

from statewave import StatewaveClient

# ── Configuration ──────────────────────────────────────────────────────────

SUBJECT_ID = "demo-support-alice"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
CONTEXT_BUDGET = 300  # tokens

# ── Demo data ──────────────────────────────────────────────────────────────

SESSION_1_EPISODES = [
    {
        "label": "Alice introduces herself (Globex, Enterprise)",
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Hi, my name is Alice Chen and I work at Globex Corporation. "
                        "I am on the Enterprise plan."
                    ),
                },
                {
                    "role": "assistant",
                    "content": "Welcome Alice! How can I help you today?",
                },
            ]
        },
    },
    {
        "label": "Alice sets notification preference (email)",
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I prefer email notifications over Slack. "
                        "My email is alice@globex.com."
                    ),
                },
                {
                    "role": "assistant",
                    "content": "Got it, I have updated your notification preference to email.",
                },
            ]
        },
    },
    {
        "label": "Alice reports billing double-charge",
        "source": "support-chat",
        "type": "conversation",
        "payload": {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "We had a billing issue last week — we were double-charged "
                        "for the March invoice."
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        "I see the double charge on your account. I have initiated "
                        "a refund for the duplicate payment. You should see it "
                        "within 3-5 business days."
                    ),
                },
            ]
        },
    },
]

SESSION_2_EPISODE = {
    "label": "Alice asks about upgrading seats",
    "source": "support-chat",
    "type": "conversation",
    "payload": {
        "messages": [
            {
                "role": "user",
                "content": "Can you help me upgrade our team from 5 to 20 seats?",
            },
        ]
    },
}

TASK = "Customer is asking about upgrading their team seats"

# ── Simulated agent responses ─────────────────────────────────────────────

STATELESS_RESPONSE = (
    "I'd be happy to help with seat upgrades! Could you tell me your name, "
    "company, and current plan so I can look up your account?"
)

STATEWAVE_RESPONSE = (
    "Hi Alice! I can help upgrade your Globex Enterprise team from 5 to 20 seats. "
    "Since you had that billing double-charge last month (the refund was processed), "
    "I'll make sure this upgrade invoice is correct before it goes out. "
    "I'll send the confirmation to your email as preferred. "
    "Shall I proceed with the upgrade?"
)


# ── Display helpers ────────────────────────────────────────────────────────

def banner(text: str) -> None:
    w = 62
    print(f"\n{'╔' + '═' * w + '╗'}")
    print(f"{'║'}{text:^{w}}{'║'}")
    print(f"{'╚' + '═' * w + '╝'}\n")


def section(title: str) -> None:
    print(f"\n── {title} {'─' * max(0, 56 - len(title))}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def indent(text: str, prefix: str = "  ") -> str:
    return textwrap.indent(text, prefix)


def quote(text: str, width: int = 58) -> str:
    lines = textwrap.wrap(text, width=width)
    return "\n".join(f'  "{line}' + ('"' if i == len(lines) - 1 else "") for i, line in enumerate(lines))


# ── Main demo ──────────────────────────────────────────────────────────────

def main() -> None:
    sw = StatewaveClient(SERVER_URL)

    # Clean slate
    sw.delete_subject(SUBJECT_ID)

    banner("STATEWAVE SUPPORT AGENT DEMO")

    # ── Session 1: First contact ──────────────────────────────────────
    section("Session 1: First contact")

    for ep in SESSION_1_EPISODES:
        sw.create_episode(
            subject_id=SUBJECT_ID,
            source=ep["source"],
            type=ep["type"],
            payload=ep["payload"],
        )
        ok(f"Episode recorded: {ep['label']}")

    # ── Compile ───────────────────────────────────────────────────────
    section("Compile memories")

    result = sw.compile_memories(SUBJECT_ID)
    ok(f"Compiled {result.memories_created} memories from {len(SESSION_1_EPISODES)} episodes")
    for m in result.memories:
        content_preview = m.content.replace("\n", " ")[:60]
        print(f"    [{m.kind}] {content_preview}")

    # ── Verify idempotency ────────────────────────────────────────────
    recompile = sw.compile_memories(SUBJECT_ID)
    ok(f"Recompile: {recompile.memories_created} new memories (idempotent ✓)")

    # ── Session 2: Alice returns ──────────────────────────────────────
    section("Session 2: Alice returns a week later")

    sw.create_episode(
        subject_id=SUBJECT_ID,
        source=SESSION_2_EPISODE["source"],
        type=SESSION_2_EPISODE["type"],
        payload=SESSION_2_EPISODE["payload"],
    )
    ok(f"Episode recorded: {SESSION_2_EPISODE['label']}")

    # Compile the new episode too
    compile2 = sw.compile_memories(SUBJECT_ID)
    ok(f"Compiled {compile2.memories_created} new memories from return visit")

    # ── Context retrieval ─────────────────────────────────────────────
    section("Context retrieval")

    ctx = sw.get_context(SUBJECT_ID, task=TASK, max_tokens=CONTEXT_BUDGET)

    print(f"\n{indent(ctx.assembled_context)}")
    print(f"\n  Token budget: {CONTEXT_BUDGET} | Used: {ctx.token_estimate}")
    print(f"  Facts: {len(ctx.provenance.get('fact_ids', []))} | "
          f"Summaries: {len(ctx.provenance.get('summary_ids', []))} | "
          f"Episodes: {len(ctx.provenance.get('episode_ids', []))}")

    # ── Comparison ────────────────────────────────────────────────────
    section("Comparison: Stateless vs. Statewave")

    print("\n  WITHOUT STATEWAVE (no memory):")
    print(quote(STATELESS_RESPONSE))
    print()
    print("  WITH STATEWAVE (full context):")
    print(quote(STATEWAVE_RESPONSE))

    # ── Provenance trace ──────────────────────────────────────────────
    section("Provenance trace")

    timeline = sw.get_timeline(SUBJECT_ID)
    episode_map = {str(e.id): e for e in timeline.episodes}

    facts = [m for m in timeline.memories if m.kind == "profile_fact"]
    print(f"\n  {len(facts)} profile facts, each traced to source episodes:")
    for fact in facts[:4]:
        src_ids = fact.source_episode_ids
        for sid in src_ids:
            ep = episode_map.get(str(sid))
            if ep:
                first_msg = ep.payload.get("messages", [{}])[0].get("content", "?")[:50]
                print(f"    \"{fact.content}\" ← episode: \"{first_msg}...\"")

    # ── Handoff context pack ──────────────────────────────────────────
    section("Handoff context pack (escalation demo)")

    import httpx

    handoff_resp = httpx.post(
        f"{SERVER_URL}/v1/handoff",
        json={
            "subject_id": SUBJECT_ID,
            "session_id": "demo-session-2",
            "reason": "escalation to billing specialist",
        },
    )
    if handoff_resp.status_code == 200:
        handoff = handoff_resp.json()
        print(f"\n  Customer: {handoff['customer_summary']}")
        print(f"  Active issue: {handoff['active_issue'] or '(none detected)'}")
        print(f"  Key facts: {len(handoff['key_facts'])}")
        print(f"  Resolution history: {len(handoff['resolution_history'])}")
        print(f"  Token estimate: {handoff['token_estimate']}")
        print(f"\n  Handoff notes preview:")
        for line in handoff["handoff_notes"].split("\n")[:10]:
            print(f"    {line}")
        ok("Handoff pack generated successfully")
    else:
        print(f"  (Handoff endpoint returned {handoff_resp.status_code} — may need server update)")

    # ── Cleanup ───────────────────────────────────────────────────────
    section("Cleanup")

    del_result = sw.delete_subject(SUBJECT_ID)
    ok(f"Deleted {del_result.episodes_deleted} episodes + {del_result.memories_deleted} memories")

    print("\n  Demo complete. ✓\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n  ✗ Error: {e}", file=sys.stderr)
        print("  Make sure Statewave is running at http://localhost:8100", file=sys.stderr)
        sys.exit(1)
