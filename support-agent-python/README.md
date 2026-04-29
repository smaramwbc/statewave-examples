# Support Agent Demo

A polished demo showing how a support agent uses Statewave to remember returning users, retrieve trusted context, and produce better answers with provenance-aware memory.

## What this demo shows

| Capability | How it's demonstrated |
|---|---|
| **Profile facts remembered** | Agent recalls name, company, plan, preferences from a prior session |
| **Relevant history retrieved** | Prior billing issue surfaces when user returns with a related problem |
| **Token-bounded, ranked context** | Context fits within budget; highest-value facts and history survive |
| **Provenance** | Every memory traces back to its source episode |
| **No duplicate junk** | Recompiling doesn't create duplicates; summaries replace raw episodes |
| **Stateless vs. Statewave comparison** | Side-by-side responses show the difference |
| **Handoff context packs** | Compact escalation brief generated for agent-to-agent transfer |

## Prerequisites

1. **Statewave server running locally:**

```bash
cd ../../statewave
docker compose up db -d
source .venv/bin/activate
alembic upgrade head
uvicorn server.app:app --host 0.0.0.0 --port 8100
```

2. **Install the Python SDK:**

```bash
pip install statewave-py
```

## Run

```bash
python support_agent.py
```

## What happens

The demo simulates two support sessions with the same customer:

**Session 1** — Alice Chen from Globex (Enterprise plan) contacts support. She shares her identity, mentions she prefers email, and reports a billing double-charge.

**Session 2** — Alice returns a week later asking about upgrading seats. Statewave retrieves her profile facts, prior billing history, and preferences — the agent responds with full context instead of asking "who are you?" again.

The demo prints:
1. Episodes recorded (raw interaction data)
2. Memories compiled (facts + summaries extracted)
3. Assembled context bundle (what the agent would see)
4. Side-by-side comparison: stateless response vs. Statewave-powered response
5. Provenance trace (which episodes produced which memories)
6. Cleanup

## Sample output

```
╔══════════════════════════════════════════════════════════════╗
║              STATEWAVE SUPPORT AGENT DEMO                   ║
╚══════════════════════════════════════════════════════════════╝

── Session 1: First contact ──────────────────────────────────
✓ Episode recorded: Alice introduces herself (Globex, Enterprise)
✓ Episode recorded: Alice sets notification preference (email)
✓ Episode recorded: Alice reports billing double-charge

── Compile memories ──────────────────────────────────────────
✓ Compiled 9 memories from 3 episodes
  [profile_fact] My name is Alice Chen
  [profile_fact] I work at Globex Corporation
  [profile_fact] I am on the Enterprise plan
  [profile_fact] I prefer email notifications over Slack
  [episode_summary] Alice Chen introduces herself → Welcome Alice!
  ...

── Session 2: Alice returns ──────────────────────────────────
✓ Episode recorded: Alice asks about upgrading seats

── Context retrieval ─────────────────────────────────────────
## Task
Customer is asking about upgrading their team seats

## About this user
- My name is Alice Chen
- I work at Globex Corporation
- I am on the Enterprise plan
- I prefer email notifications over Slack

## Recent history
- We had a billing issue — double-charged for March → Refund initiated
- ...

Token budget: 300 | Used: 187

── Comparison ────────────────────────────────────────────────
WITHOUT STATEWAVE:
  "I'd be happy to help with seat upgrades. Could you tell me
   your name, company, and current plan?"

WITH STATEWAVE:
  "Hi Alice! I can help upgrade your Globex Enterprise team.
   Since you had that billing double-charge last month (refund
   was processed), I'll make sure this upgrade invoice is
   correct. I'll send confirmation to your email as preferred.
   How many seats do you need?"
```
