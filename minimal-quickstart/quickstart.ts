/**
 * Minimal Statewave quickstart — record, compile, retrieve context.
 *
 * Run:  npx tsx minimal-quickstart/quickstart.ts
 */

import { StatewaveClient } from "@statewavedev/sdk";

const SUBJECT = "demo-user-1-ts";

async function main() {
  const sw = new StatewaveClient({
    baseUrl: process.env.STATEWAVE_URL ?? "http://localhost:8100",
    apiKey: process.env.STATEWAVE_API_KEY,
  });

  console.log("Recording episodes...");
  await sw.createEpisode({
    subjectId: SUBJECT,
    source: "chat",
    type: "conversation",
    payload: {
      messages: [
        { role: "user", content: "My name is Alice and I work at Acme Corp." },
        { role: "assistant", content: "Nice to meet you, Alice!" },
      ],
    },
  });
  await sw.createEpisode({
    subjectId: SUBJECT,
    source: "chat",
    type: "conversation",
    payload: {
      messages: [{ role: "user", content: "I prefer Python and use VS Code." }],
    },
  });

  console.log("Compiling memories...");
  const result = await sw.compileMemories(SUBJECT);
  console.log(`  ${result.memoriesCreated} memories created`);
  for (const m of result.memories) {
    console.log(`  [${m.kind}] ${m.content}`);
  }

  console.log("\nRetrieving context bundle...");
  const ctx = await sw.getContext({
    subjectId: SUBJECT,
    task: "Help the user set up a new project",
  });
  console.log(`  ${ctx.tokenEstimate} tokens, ${ctx.facts.length} facts, ${ctx.episodes.length} episodes`);
  console.log(`\n${ctx.assembledContext}`);

  await sw.deleteSubject(SUBJECT);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
