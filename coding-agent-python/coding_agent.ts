/**
 * Coding agent demo (TypeScript) — project context persists across sessions.
 *
 * Run:  npx tsx coding-agent-python/coding_agent.ts
 */

import { StatewaveClient } from "statewave-ts";

const SUBJECT_ID = "demo-coding-dev-bob-ts";
const SERVER_URL = process.env.STATEWAVE_URL ?? "http://localhost:8100";
const API_KEY = process.env.STATEWAVE_API_KEY;
const CONTEXT_BUDGET = 400;

const SESSION_1 = [
  { messages: [
    { role: "user", content: "I'm Bob, working on a Python FastAPI backend called Taskflow. We use SQLAlchemy with Postgres, Alembic for migrations, and pytest for testing." },
    { role: "assistant", content: "Got it — Taskflow is a FastAPI + SQLAlchemy + Postgres project with Alembic migrations and pytest." },
  ]},
  { messages: [
    { role: "user", content: "I prefer small focused functions, type hints everywhere, and I use Pydantic for all request/response schemas. No classes unless they add real value." },
    { role: "assistant", content: "Noted — functional style with type hints, Pydantic schemas, classes only when justified." },
  ]},
  { messages: [
    { role: "user", content: "We decided to model task status as a finite state machine: draft → active → paused → completed → archived. Transitions are enforced in the service layer, not the DB." },
    { role: "assistant", content: "Good pattern — service layer validates transitions. I'll keep that in mind." },
  ]},
];

const SESSION_2 = [
  { messages: [{ role: "user", content: "Can you help me add a PATCH endpoint to transition task status?" }] },
];

async function main() {
  const sw = new StatewaveClient({ baseUrl: SERVER_URL, apiKey: API_KEY });
  await sw.deleteSubject(SUBJECT_ID);

  console.log("=== Session 1: Developer introduces project and preferences ===");
  for (const payload of SESSION_1) {
    await sw.createEpisode({ subject_id: SUBJECT_ID, source: "coding-chat", type: "conversation", payload });
  }
  const r = await sw.compileMemories(SUBJECT_ID);
  console.log(`Compiled ${r.memories_created} memories`);
  for (const m of r.memories) console.log(`  [${m.kind}] ${m.content}`);

  console.log("\n=== Session 2: Developer returns, asks for a new feature ===");
  for (const payload of SESSION_2) {
    await sw.createEpisode({ subject_id: SUBJECT_ID, source: "coding-chat", type: "conversation", payload });
  }
  await sw.compileMemories(SUBJECT_ID);

  const ctx = await sw.getContext({
    subject_id: SUBJECT_ID,
    task: "Developer wants to add a PATCH endpoint for task status transitions",
    max_tokens: CONTEXT_BUDGET,
  });
  console.log(
    `\nContext bundle (${ctx.token_estimate}/${CONTEXT_BUDGET} tokens, `
    + `${ctx.facts.length} facts, ${ctx.procedures.length} procedures, ${ctx.episodes.length} episodes):\n`,
  );
  console.log(ctx.assembled_context);

  await sw.deleteSubject(SUBJECT_ID);
}

main().catch((err) => {
  console.error(err);
  console.error(`Is the Statewave server running at ${SERVER_URL}?`);
  process.exit(1);
});
