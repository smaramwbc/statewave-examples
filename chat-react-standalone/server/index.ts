/**
 * Express server — serves /api/chat/* in dev mode.
 *
 * In production, also serves the Vite build from dist/.
 *
 * Start:  npx tsx server/index.ts
 *         (or via `npm run dev` which runs it alongside Vite)
 */

import 'dotenv/config'
import express from 'express'
import { handleRetrieve } from './retrieve.js'
import { handleComplete } from './complete.js'

const app = express()
app.use(express.json())

app.post('/api/chat/retrieve', (req, res) => { void handleRetrieve(req, res) })
app.post('/api/chat/complete', (req, res) => { void handleComplete(req, res) })

// Health check
app.get('/api/health', (_req, res) => res.json({ ok: true }))

const PORT = Number(process.env.PORT ?? 3001)
app.listen(PORT, () => {
  console.log(`[server] listening on http://localhost:${PORT}`)
  console.log(`[server] Statewave: ${process.env.STATEWAVE_URL ?? 'http://localhost:8100'}`)
  console.log(`[server] LLM provider: ${process.env.LLM_PROVIDER ?? 'openai'} / ${process.env.LLM_MODEL ?? 'gpt-4o-mini'}`)
})
