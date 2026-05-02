# Full-Loop Support Agent (with LLM)

A complete support-agent example: Statewave memory + real LLM response generation.

Shows the **exact difference** between a stateless agent and a Statewave-powered agent answering the same question — using a real model. Multi-provider out of the box via [LiteLLM](https://github.com/BerriAI/litellm): OpenAI, Anthropic, Azure, Bedrock, Cohere, Ollama, Groq, and 100+ others.

## What it does

1. Seeds 4 conversational episodes of realistic support history for a customer
2. Compiles memories from those episodes
3. Asks both agents: *"Hi, I need help adding a new team member to our account"*
4. **Stateless agent** — gets zero context, responds generically
5. **Statewave agent** — gets a ranked, token-bounded context bundle, responds with full customer awareness

## Run

```bash
# Requires:
#   Statewave server at localhost:8100
#   pip install statewave-py litellm

# Pick any LiteLLM-supported model and provide the matching key.
# Examples:
export LLM_MODEL=gpt-4o-mini                              OPENAI_API_KEY=sk-...
# export LLM_MODEL=anthropic/claude-3-haiku-20240307      ANTHROPIC_API_KEY=sk-ant-...
# export LLM_MODEL=ollama/llama3                          # no key — runs locally
# export LLM_MODEL=groq/llama-3.1-70b-versatile           GROQ_API_KEY=...

export STATEWAVE_URL="http://localhost:8100"  # optional, default

python support_agent_llm.py
```

The script pre-flight-checks the env for the key your chosen model needs (via `litellm.validate_environment`) and fails fast with a friendly message if it's missing — full provider matrix at https://docs.litellm.ai/docs/providers.

## Expected output

```
═══ Full-Loop Support Agent — Statewave + LLM ═══
  model: gpt-4o-mini

Seeding 4 episodes... ✓
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
| `LLM_MODEL` | `gpt-4o-mini` | Any LiteLLM-supported model identifier |
| `OPENAI_MODEL` | — | Backward-compat fallback for `LLM_MODEL` |
| Provider key | — | Whatever the chosen model needs (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, …). Ollama needs no key. |

## Key takeaway

The Statewave agent knows Alice's name, company, plan, and SSO setup — **without any of that being in the current message**. The stateless agent has to ask for basics. This is the core value: structured, ranked memory that makes every response contextually aware.

The core integration is ~15 lines and works against any LiteLLM-supported provider:

```python
from statewave import StatewaveClient
from litellm import completion

sw = StatewaveClient()

context = sw.get_context_string("customer-123", "Help with their question")

response = completion(
    model="gpt-4o-mini",  # or anthropic/claude-..., ollama/llama3, ...
    messages=[
        {"role": "system", "content": f"You are a support agent.\n\n{context}"},
        {"role": "user", "content": customer_message},
    ],
)
```

Swap the `model=` value to point at any other provider — Statewave's role (memory + context assembly) doesn't change.
