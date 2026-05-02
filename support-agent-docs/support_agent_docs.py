"""Statewave Support Agent — docs-grounded variant.

This example assumes you have already bootstrapped the default docs
memory pack:

    cd ../../statewave
    python -m scripts.bootstrap_docs_pack

It then asks the support agent realistic product questions and shows:
  * the ranked context Statewave returns from the docs subject
  * the citations carried in episode provenance
  * what a stateless agent would have to say versus a docs-grounded one
  * how the agent should behave when a question is *out of scope* for
    the public docs (e.g. "why is MY deployment slow?")

The actual LLM call is left as a one-line plug-in point at the bottom
so the demo runs without any model API key. See `support-agent-llm/`
for the wired-up LLM variant.
"""

from __future__ import annotations

import os
import sys
import textwrap

from statewave import StatewaveClient

DOCS_SUBJECT_ID = "statewave-support-docs"
SERVER_URL = os.getenv("STATEWAVE_URL", "http://localhost:8100")
CONTEXT_BUDGET = 600  # tokens — docs answers benefit from a roomier budget than chat history

# A small set of questions covering the three response modes the
# docs-grounded agent must handle.
QUESTIONS: list[dict] = [
    {
        "label": "Documented fact",
        "task": "What database does Statewave use, and is it required for vector search?",
        "expect": "answer with citation to architecture/overview.md or ADR-001",
    },
    {
        "label": "Documented fact (deployment)",
        "task": "How do I deploy Statewave on Fly.io for a small team?",
        "expect": "answer with citation to deployment/guide.md",
    },
    {
        "label": "Best-effort suggestion",
        "task": "We're seeing slow compile times on a 50-episode subject. Any guidance?",
        "expect": "docs cover compiler modes and scaling; agent should suggest based on those",
    },
    {
        "label": "Out of scope (user-specific)",
        "task": "Why is my Statewave instance returning 503 errors right now?",
        "expect": "agent must say it cannot know live deployment state — route to SUPPORT.md",
    },
]


def banner(s: str) -> None:
    w = 64
    print(f"\n{'╔' + '═' * w + '╗'}")
    print(f"║{s:^{w}}║")
    print(f"{'╚' + '═' * w + '╝'}\n")


def section(s: str) -> None:
    print(f"\n── {s} {'─' * max(0, 58 - len(s))}")


def wrap(s: str, prefix: str = "    ") -> str:
    return "\n".join(textwrap.wrap(s, width=80, initial_indent=prefix, subsequent_indent=prefix))


def render_citations(sw: StatewaveClient, ctx) -> list[str]:
    """Walk provenance back to source episodes and pull doc_path + heading_path.

    Statewave gives us memory IDs in `ctx.provenance`; episodes are linked
    via `source_episode_ids` on each memory. For the docs subject, every
    episode's `provenance.doc_path` and `payload.breadcrumb` is the citation.
    """
    timeline = sw.get_timeline(DOCS_SUBJECT_ID)
    episode_by_id = {str(ep.id): ep for ep in timeline.episodes}
    memory_by_id = {str(m.id): m for m in timeline.memories}

    citation_keys: set[tuple[str, str]] = set()
    memory_ids = (
        ctx.provenance.get("fact_ids", [])
        + ctx.provenance.get("summary_ids", [])
    )
    for mid in memory_ids:
        mem = memory_by_id.get(str(mid))
        if not mem:
            continue
        for eid in mem.source_episode_ids or []:
            ep = episode_by_id.get(str(eid))
            if not ep:
                continue
            doc_path = (ep.provenance or {}).get("doc_path", "?")
            breadcrumb = (ep.payload or {}).get("breadcrumb", "")
            citation_keys.add((doc_path, breadcrumb))

    # Also pull straight from raw episode IDs surfaced in the bundle
    for eid in ctx.provenance.get("episode_ids", []):
        ep = episode_by_id.get(str(eid))
        if not ep:
            continue
        doc_path = (ep.provenance or {}).get("doc_path", "?")
        breadcrumb = (ep.payload or {}).get("breadcrumb", "")
        citation_keys.add((doc_path, breadcrumb))

    return sorted(f"{path} § {bc}" if bc else path for path, bc in citation_keys)


SYSTEM_PROMPT = """\
You are a Statewave support assistant. Answer using ONLY the official
Statewave documentation provided in the context block below. Cite the
doc path and section.

If the user asks about something the docs do not cover, say so plainly
and route them to https://github.com/smaramwbc/statewave/issues or to
SUPPORT.md. Never invent API fields, config keys, or version-specific
behavior. Never claim knowledge of the user's specific deployment.
"""


def call_llm(system_prompt: str, context_block: str, user_task: str) -> str:
    """Stub. Plug in your LLM client of choice here.

    See ../support-agent-llm/ for a working LiteLLM integration that runs
    against any of 100+ supported providers (OpenAI, Anthropic, Bedrock,
    Ollama, …). Returning a placeholder here keeps this demo runnable
    without any API keys.
    """
    return (
        "[plug in your LLM here — the system prompt above plus the docs "
        "context below would produce a grounded, cited answer]"
    )


def main() -> None:
    sw = StatewaveClient(SERVER_URL)

    # Verify the docs pack has been bootstrapped
    timeline = sw.get_timeline(DOCS_SUBJECT_ID)
    if not timeline.episodes:
        print(
            f"\n  ✗ Subject {DOCS_SUBJECT_ID!r} is empty.\n"
            "    Bootstrap the docs pack first:\n"
            "        cd ../../statewave\n"
            "        python -m scripts.bootstrap_docs_pack\n",
            file=sys.stderr,
        )
        sys.exit(1)

    banner("STATEWAVE DOCS-GROUNDED SUPPORT AGENT")
    print(f"  Subject:  {DOCS_SUBJECT_ID}")
    print(f"  Episodes: {len(timeline.episodes)}")
    print(f"  Memories: {len(timeline.memories)}")
    print(f"  Budget:   {CONTEXT_BUDGET} tokens per question")

    for q in QUESTIONS:
        section(f"Q: {q['label']}")
        print(wrap(f"User: {q['task']}"))
        print(wrap(f"(Expect: {q['expect']})"))

        ctx = sw.get_context(DOCS_SUBJECT_ID, task=q["task"], max_tokens=CONTEXT_BUDGET)

        print(f"\n  Token budget {CONTEXT_BUDGET} → used {ctx.token_estimate}")
        print(
            f"  Retrieved: {len(ctx.provenance.get('fact_ids', []))} facts, "
            f"{len(ctx.provenance.get('summary_ids', []))} summaries, "
            f"{len(ctx.provenance.get('episode_ids', []))} episodes"
        )

        citations = render_citations(sw, ctx)
        if citations:
            print("\n  Citations the agent should attribute:")
            for c in citations[:6]:
                print(f"    • {c}")
            if len(citations) > 6:
                print(f"    ... and {len(citations) - 6} more")
        else:
            print("\n  No documented context surfaced — the agent must say so.")

        # In a real deployment you would hand `ctx.assembled_context` and the
        # user task to your LLM along with SYSTEM_PROMPT. Here we stub it:
        answer = call_llm(SYSTEM_PROMPT, ctx.assembled_context, q["task"])
        print("\n  Grounded answer (LLM-produced in production):")
        print(wrap(answer, prefix="    "))

    print()
    print("=" * 80)
    print(
        "Notes:\n"
        "  • The agent does NOT learn from any source code — only the docs corpus.\n"
        "  • Out-of-scope questions are an EXPECTED outcome, not a failure mode.\n"
        "  • To wire up a real LLM, see ../support-agent-llm/.\n"
        "  • To refresh the pack after docs change, re-run with --purge:\n"
        "        cd ../../statewave && python -m scripts.bootstrap_docs_pack --purge\n"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n  ✗ Error: {e}", file=sys.stderr)
        print(f"    Make sure Statewave is running at {SERVER_URL}", file=sys.stderr)
        sys.exit(1)
