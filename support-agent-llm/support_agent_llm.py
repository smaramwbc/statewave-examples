"""Full-loop support agent — Statewave context + real LLM response.

Compares stateless agent vs Statewave-powered agent on the same question,
using LiteLLM so any provider works.

Examples:
  LLM_MODEL=gpt-4o-mini OPENAI_API_KEY=sk-...
  LLM_MODEL=anthropic/claude-3-haiku-20240307 ANTHROPIC_API_KEY=sk-ant-...
  LLM_MODEL=ollama/llama3                    (no key — runs locally)

See https://docs.litellm.ai/docs/providers for the full provider list.

Run:  pip install statewave litellm
      LLM_MODEL=gpt-4o-mini OPENAI_API_KEY=sk-... python support_agent_llm.py
"""

from __future__ import annotations

import os
import sys
import textwrap

from litellm import completion
from statewave import StatewaveClient

SUBJECT_ID = "demo-llm-support-alice"
STATEWAVE_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
STATEWAVE_API_KEY = os.getenv("STATEWAVE_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

CUSTOMER_MESSAGE = "Hi, I need help adding a new team member to our account"

SYSTEM_PROMPT = (
    "You are a helpful support agent. Be concise, friendly, and specific. "
    "Use any context provided to personalise your response. "
    "Do not ask for information you already have."
)

EPISODES = [
    {"messages": [
        {"role": "user", "content": "Hi, I'm Alice Chen from Globex Corporation. We're on the Enterprise plan."},
        {"role": "assistant", "content": "Welcome Alice! How can I help you today?"},
    ]},
    {"messages": [
        {"role": "user", "content": "We need to set up SSO. We use Okta as our IdP."},
        {"role": "assistant", "content": "I've enabled SAML SSO for Globex. Your callback URL is https://app.example.com/sso/callback."},
    ]},
    {"messages": [
        {"role": "user", "content": "SSO is working now. We have 12 team members using it. Thanks!"},
        {"role": "assistant", "content": "Great to hear! All 12 members are authenticating via Okta successfully."},
    ]},
    {"messages": [
        {"role": "user", "content": "I prefer getting responses that are short and to the point, no fluff please."},
        {"role": "assistant", "content": "Noted — I'll keep things concise for you, Alice."},
    ]},
]


def ask(model: str, system: str, user: str) -> str:
    resp = completion(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=150,
    )
    return resp.choices[0].message.content.strip()


def main() -> None:
    sw = StatewaveClient(base_url=STATEWAVE_URL, api_key=STATEWAVE_API_KEY)
    print(f"Model: {LLM_MODEL}\n")

    sw.delete_subject(SUBJECT_ID)
    for ep in EPISODES:
        sw.create_episode(subject_id=SUBJECT_ID, source="support-chat", type="conversation", payload=ep)
    r = sw.compile_memories(SUBJECT_ID)
    print(f"Seeded {len(EPISODES)} episodes, compiled {r.memories_created} memories\n")

    bundle = sw.get_context(SUBJECT_ID, "Help this customer with their question", max_tokens=400)
    print(f'Customer: "{CUSTOMER_MESSAGE}"\n')

    stateless = ask(LLM_MODEL, SYSTEM_PROMPT, CUSTOMER_MESSAGE)
    print("--- Stateless agent (no memory) ---")
    print(textwrap.fill(stateless, width=72))

    aware = ask(LLM_MODEL, f"{SYSTEM_PROMPT}\n\n{bundle.assembled_context}", CUSTOMER_MESSAGE)
    print("\n--- Statewave agent (full context) ---")
    print(textwrap.fill(aware, width=72))

    print(f"\n--- Context used ({bundle.token_estimate} tokens) ---")
    for line in bundle.assembled_context.split("\n")[:8]:
        print(line)
    if bundle.assembled_context.count("\n") > 8:
        print("...")

    sw.delete_subject(SUBJECT_ID)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
