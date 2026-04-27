"""Full-loop support agent — Statewave memory + real LLM response.

Demonstrates the complete flow:
  1. Ingest support episodes
  2. Compile memories
  3. Retrieve context
  4. Generate LLM response with full customer awareness

Compares: stateless agent vs Statewave-powered agent on the same question.

Run:  OPENAI_API_KEY=sk-... python support_agent_llm.py
Requires: pip install statewave-py openai
"""

from __future__ import annotations

import os
import sys
import textwrap

from openai import OpenAI
from statewave import StatewaveClient
from statewave.exceptions import StatewaveAPIError, StatewaveConnectionError

# ── Config ─────────────────────────────────────────────────────────────────

SUBJECT_ID = "demo-llm-support-alice"
STATEWAVE_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
STATEWAVE_API_KEY = os.getenv("STATEWAVE_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CUSTOMER_MESSAGE = "Hi, I need help adding a new team member to our account"

SYSTEM_PROMPT = (
    "You are a helpful support agent. Be concise, friendly, and specific. "
    "Use any context provided to personalise your response. "
    "Do not ask for information you already have."
)

# ── Episode data ───────────────────────────────────────────────────────────

EPISODES = [
    {
        "source": "support-chat", "type": "conversation",
        "payload": {"messages": [
            {"role": "user", "content": "Hi, I'm Alice Chen from Globex Corporation. We're on the Enterprise plan."},
            {"role": "assistant", "content": "Welcome Alice! How can I help you today?"},
        ]},
    },
    {
        "source": "support-chat", "type": "conversation",
        "payload": {"messages": [
            {"role": "user", "content": "We need to set up SSO. We use Okta as our IdP."},
            {"role": "assistant", "content": "I've enabled SAML SSO for Globex. Your callback URL is https://app.example.com/sso/callback."},
        ]},
    },
    {
        "source": "support-chat", "type": "conversation",
        "payload": {"messages": [
            {"role": "user", "content": "SSO is working now. We have 12 team members using it. Thanks!"},
            {"role": "assistant", "content": "Great to hear! All 12 members are authenticating via Okta successfully."},
        ]},
    },
    {
        "source": "support-chat", "type": "conversation",
        "payload": {"messages": [
            {"role": "user", "content": "I prefer getting responses that are short and to the point, no fluff please."},
            {"role": "assistant", "content": "Noted — I'll keep things concise for you, Alice."},
        ]},
    },
]

# ── Main ───────────────────────────────────────────────────────────────────


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY to run this example.")
        sys.exit(1)

    sw = StatewaveClient(base_url=STATEWAVE_URL, api_key=STATEWAVE_API_KEY)
    ai = OpenAI()

    print("\n═══ Full-Loop Support Agent — Statewave + LLM ═══\n")

    # ── Setup ──────────────────────────────────────────────────────────────
    try:
        sw.delete_subject(SUBJECT_ID)
    except (StatewaveAPIError, StatewaveConnectionError) as e:
        if isinstance(e, StatewaveConnectionError):
            print(f"❌ Cannot connect to Statewave at {STATEWAVE_URL}")
            sys.exit(2)

    print(f"Seeding {len(EPISODES)} episodes...", end=" ", flush=True)
    for ep in EPISODES:
        sw.create_episode(subject_id=SUBJECT_ID, source=ep["source"], type=ep["type"], payload=ep["payload"])
    print("✓")

    print("Compiling memories...", end=" ", flush=True)
    result = sw.compile_memories(SUBJECT_ID)
    print(f"✓ ({result.memories_created} memories)")

    # ── Get context ────────────────────────────────────────────────────────
    bundle = sw.get_context(SUBJECT_ID, "Help this customer with their question", max_tokens=400)
    context_str = bundle.assembled_context

    print(f"\nCustomer asks: \"{CUSTOMER_MESSAGE}\"\n")

    # ── Stateless response ─────────────────────────────────────────────────
    stateless = ai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": CUSTOMER_MESSAGE},
        ],
        max_tokens=150,
    )
    print("── Stateless Agent (no memory) ──────────────────")
    print(textwrap.fill(stateless.choices[0].message.content.strip(), width=60))

    # ── Statewave response ─────────────────────────────────────────────────
    statewave_resp = ai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{context_str}"},
            {"role": "user", "content": CUSTOMER_MESSAGE},
        ],
        max_tokens=150,
    )
    print("\n── Statewave Agent (full context) ───────────────")
    print(textwrap.fill(statewave_resp.choices[0].message.content.strip(), width=60))

    # ── Show context used ──────────────────────────────────────────────────
    print(f"\n── Context used ({bundle.token_estimate} tokens) ────────────────")
    # Show first 8 lines of context
    for line in context_str.split("\n")[:8]:
        print(f"  {line}")
    if context_str.count("\n") > 8:
        print("  ...")

    # ── Cleanup ────────────────────────────────────────────────────────────
    sw.delete_subject(SUBJECT_ID)
    sw.close()
    print("\n═══ Done ═══\n")


if __name__ == "__main__":
    main()
