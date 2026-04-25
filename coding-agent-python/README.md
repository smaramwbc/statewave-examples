# Coding Agent Example — Statewave

Demonstrates how a coding assistant uses Statewave to remember a developer's
project context, coding preferences, and past decisions across sessions.

## What it shows

1. **Session 1**: Developer introduces their project (Python/FastAPI), preferred
   patterns, and discusses a database schema decision.
2. **Session 2**: Developer returns and asks for help implementing a new feature.
   The agent uses compiled memories to recall the tech stack, preferences, and
   prior architecture decisions — no repetition needed.

## Run

```bash
# Requires Statewave server at http://localhost:8100
pip install statewave-py
python coding_agent.py
```
