# Full-Loop Support Agent (with LLM)

A complete support-agent example: Statewave memory + real LLM response generation.

Shows the **exact difference** between a stateless agent and a Statewave-powered agent answering the same question — using a real model (GPT-4o-mini by default, any OpenAI-compatible model works).

## What it does

1. Seeds 3 sessions of realistic support history for a customer
2. Compiles memories from those episodes
3. Asks both agents: *"Hi, I need help adding a new team member to our account"*
4. **Stateless agent** — gets zero context, responds generically
5. **Statewave agent** — gets a ranked, token-bounded context bundle, responds with full customer awareness

## Run

```bash
# Requires:
#   Statewave server at localhost:8100
#   An LLM API key (OpenAI, Anthropic, etc.)
#   pip install statewave-py openai

export OPENAI_API_KEY="sk-..."  # or ANTHROPIC_API_KEY, etc.
export STATEWAVE_URL="http://localhost:8100"  # optional, default

python support_agent_llm.py
```

## Expected output

```
═══ Full-Loop Support Agent — Statewave + LLM ═══

Seeding 4 episodes (2 sessions)... ✓
Compiling memories... ✓ (6 memories)

Customer asks: "Hi, I need help adding a new team member to our account"

── Stateless Agent (no memory) ──────────────────
I'd be happy to help you add a team member! Could you please tell me
your account details and what plan you're on so I can guide you through
the process?

── Statewave Agent (full context) ───────────────
Hi Alice! Since Globex is on the Enterprise plan, you can add team
members directly from Settings → Team. Given your SSO is already
configured, the new member will authenticate via your existing SAML
setup. Would you like me to send an invite link, or do you prefer to
add them manually?

── Context used (131 tokens) ────────────────────
## Task
Help this customer with their question

## About this user
- I'm Alice Chen from Globex Corporation
- I'm on the Enterprise plan
...
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `STATEWAVE_URL` | `http://localhost:8100` | Statewave server URL |
| `STATEWAVE_API_KEY` | — | Statewave API key (if auth enabled) |
| `OPENAI_API_KEY` | — | **Required** — LLM API key (or set provider-specific key) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for the example's own LLM call |

## Key takeaway

The Statewave agent knows Alice's name, company, plan, and SSO setup — **without any of that being in the current message**. The stateless agent has to ask for basics. This is the core value: structured, ranked memory that makes every response contextually aware.

The core integration is ~15 lines:

```python
from statewave import StatewaveClient
from openai import OpenAI

sw = StatewaveClient()
ai = OpenAI()

context = sw.get_context_string("customer-123", "Help with their question")

response = ai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"You are a support agent.\n\n{context}"},
        {"role": "user", "content": customer_message},
    ],
)
```
