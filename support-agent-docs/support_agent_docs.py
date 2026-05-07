"""Docs-grounded support agent — uses the `statewave-support-docs` memory pack
to answer Statewave product questions from the official docs.

Bootstrap the pack first:

    cd ../../statewave
    python -m scripts.bootstrap_docs_pack

This demo retrieves ranked docs context for four representative questions —
documented facts, best-effort guidance, and an out-of-scope question the
agent must refuse. Plug your LLM into `call_llm` to produce real answers.
See ../support-agent-llm/ for a wired-up LiteLLM example.
"""

from __future__ import annotations

import os
import sys

from statewave import StatewaveClient

DOCS_SUBJECT_ID = "statewave-support-docs"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
API_KEY = os.getenv("STATEWAVE_API_KEY")
CONTEXT_BUDGET = 600

QUESTIONS = [
    {"label": "Documented fact",
     "task": "What database does Statewave use, and is it required for vector search?"},
    {"label": "Documented fact (deployment)",
     "task": "How do I deploy Statewave on Fly.io for a small team?"},
    {"label": "Best-effort suggestion",
     "task": "We're seeing slow compile times on a 50-episode subject. Any guidance?"},
    {"label": "Out of scope (user-specific)",
     "task": "Why is my Statewave instance returning 503 errors right now?"},
]

SYSTEM_PROMPT = """\
You are a Statewave support assistant. Answer using ONLY the official
Statewave documentation provided in the context block below. Cite the
doc path when possible.

If the user asks about something the docs do not cover, say so plainly
and route them to https://github.com/smaramwbc/statewave/issues. Never
invent API fields or claim knowledge of the user's specific deployment.
"""


def call_llm(system_prompt: str, context_block: str, user_task: str) -> str:
    """Plug in your LLM client. See ../support-agent-llm/ for a working example."""
    return "[plug in your LLM here — system + context above produces a grounded answer]"


def main() -> None:
    sw = StatewaveClient(base_url=SERVER_URL, api_key=API_KEY)

    timeline = sw.get_timeline(DOCS_SUBJECT_ID)
    if not timeline.episodes:
        print(
            f"Subject {DOCS_SUBJECT_ID!r} is empty. Bootstrap the docs pack first:\n"
            "  cd ../../statewave\n"
            "  python -m scripts.bootstrap_docs_pack",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Subject:  {DOCS_SUBJECT_ID}")
    print(f"Episodes: {len(timeline.episodes)}, memories: {len(timeline.memories)}")
    print(f"Budget:   {CONTEXT_BUDGET} tokens per question\n")

    for q in QUESTIONS:
        print(f"=== {q['label']}: {q['task']} ===")
        ctx = sw.get_context(DOCS_SUBJECT_ID, task=q["task"], max_tokens=CONTEXT_BUDGET)
        print(f"Used {ctx.token_estimate}/{CONTEXT_BUDGET} tokens — "
              f"{len(ctx.facts)} facts, {len(ctx.procedures)} procedures, {len(ctx.episodes)} episodes")

        for f in ctx.facts[:3]:
            print(f"  • {f.content}")
        if len(ctx.facts) > 3:
            print(f"  ... and {len(ctx.facts) - 3} more facts")

        answer = call_llm(SYSTEM_PROMPT, ctx.assembled_context, q["task"])
        print(f"\n{answer}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Is the Statewave server running at {SERVER_URL}?", file=sys.stderr)
        sys.exit(1)
