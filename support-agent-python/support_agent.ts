/**
 * Support agent demo (TypeScript) — returning customer recognised across sessions.
 *
 * Run:  npx tsx support-agent-python/support_agent.ts
 */

import { StatewaveClient } from "@statewavedev/sdk";

const SUBJECT_ID = "demo-support-alice-ts";
const SERVER_URL = process.env.STATEWAVE_URL ?? "http://localhost:8100";
const API_KEY = process.env.STATEWAVE_API_KEY;
const CONTEXT_BUDGET = 300;

const SESSION_1 = [
  { messages: [
    { role: "user", content: "Hi, my name is Alice Chen and I work at Globex Corporation. I am on the Enterprise plan." },
    { role: "assistant", content: "Welcome Alice! How can I help you today?" },
  ]},
  { messages: [
    { role: "user", content: "I prefer email notifications over Slack. My email is alice@globex.com." },
    { role: "assistant", content: "Got it, I have updated your notification preference to email." },
  ]},
  { messages: [
    { role: "user", content: "We had a billing issue last week — we were double-charged for the March invoice." },
    { role: "assistant", content: "I see the double charge. I have initiated a refund. You should see it within 3-5 business days." },
  ]},
];

const SESSION_2 = [
  { messages: [{ role: "user", content: "Can you help me upgrade our team from 5 to 20 seats?" }] },
];

async function main() {
  const sw = new StatewaveClient({ baseUrl: SERVER_URL, apiKey: API_KEY });
  await sw.deleteSubject(SUBJECT_ID);

  console.log("=== Session 1: First contact ===");
  for (const payload of SESSION_1) {
    await sw.createEpisode({ subjectId: SUBJECT_ID, source: "support-chat", type: "conversation", payload });
  }
  const r = await sw.compileMemories(SUBJECT_ID);
  console.log(`Compiled ${r.memoriesCreated} memories from ${SESSION_1.length} episodes`);
  for (const m of r.memories) console.log(`  [${m.kind}] ${m.content}`);

  const recompile = await sw.compileMemories(SUBJECT_ID);
  console.log(`Recompile: ${recompile.memoriesCreated} new memories (idempotent)`);

  console.log("\n=== Session 2: Alice returns a week later ===");
  for (const payload of SESSION_2) {
    await sw.createEpisode({ subjectId: SUBJECT_ID, source: "support-chat", type: "conversation", payload });
  }
  await sw.compileMemories(SUBJECT_ID);

  const ctx = await sw.getContext({
    subjectId: SUBJECT_ID,
    task: "Customer is asking about upgrading their team seats",
    maxTokens: CONTEXT_BUDGET,
  });
  console.log(
    `\nContext bundle (${ctx.tokenEstimate}/${CONTEXT_BUDGET} tokens, `
    + `${ctx.facts.length} facts, ${ctx.episodes.length} episodes):\n`,
  );
  console.log(ctx.assembledContext);

  console.log("\n=== Provenance — each fact traces back to a source episode ===");
  const episodesById = new Map(ctx.episodes.map((e) => [e.id, e]));
  for (const f of ctx.facts.slice(0, 4)) {
    for (const eid of f.sourceEpisodeIds) {
      const ep = episodesById.get(eid);
      if (!ep) continue;
      const messages = (ep.payload as { messages?: { content: string }[] }).messages ?? [];
      const firstMsg = messages[0]?.content ?? "?";
      console.log(`  ${JSON.stringify(f.content)}\n    ← ${firstMsg.slice(0, 60)}...`);
    }
  }

  console.log("\n=== Handoff pack (escalation to billing specialist) ===");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  const resp = await fetch(`${SERVER_URL}/v1/handoff`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      subject_id: SUBJECT_ID,
      session_id: "demo-session-2",
      reason: "escalation to billing specialist",
    }),
  });
  if (!resp.ok) throw new Error(`Handoff failed: ${resp.status} ${await resp.text()}`);
  const handoff = await resp.json() as {
    customer_summary: string;
    active_issue: string | null;
    key_facts: string[];
    resolution_history: unknown[];
    token_estimate: number;
    handoff_notes: string;
  };
  console.log(`Customer:      ${handoff.customer_summary}`);
  console.log(`Active issue:  ${handoff.active_issue ?? "(none detected)"}`);
  console.log(`Key facts:     ${handoff.key_facts.length}`);
  console.log(`Resolutions:   ${handoff.resolution_history.length}`);
  console.log(`Tokens:        ${handoff.token_estimate}`);
  console.log("\n--- Handoff notes (first 10 lines) ---");
  for (const line of handoff.handoff_notes.split("\n").slice(0, 10)) console.log(line);

  await sw.deleteSubject(SUBJECT_ID);
}

main().catch((err) => {
  console.error(err);
  console.error(`Is the Statewave server running at ${SERVER_URL}?`);
  process.exit(1);
});
