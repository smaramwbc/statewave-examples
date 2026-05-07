# Coding Agent Demo

A developer's project context — tech stack, conventions, and architecture decisions — persists across sessions. In session 2, the agent already knows the project before being asked.

## What this demo shows

- Session 1: developer introduces a FastAPI/SQLAlchemy/Postgres project, states preferences, discusses a finite-state-machine pattern for task status.
- Session 2: developer returns, asks for a PATCH endpoint. The retrieved context already contains the stack, the FSM rule, and the coding-style preferences — no repetition needed.

## Run

```bash
# Requires Statewave server at http://localhost:8100
pip install statewave-py
python coding_agent.py
# or
npx tsx coding_agent.ts
```
