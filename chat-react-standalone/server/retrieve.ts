import type { Request, Response } from 'express'
import { StatewaveClient } from '@statewavedev/sdk'
import { StatewaveRetrievalAdapter } from '@statewavedev/chat-core/server'
import type { ChatRetrievalRequest, MultiSubjectRetrievalConfig } from '@statewavedev/chat-core'

const DEFAULT_CONFIG: MultiSubjectRetrievalConfig = { globalMaxTokens: 2000 }

export async function handleRetrieve(req: Request, res: Response): Promise<void> {
  const body = req.body as Partial<ChatRetrievalRequest>

  if (!Array.isArray(body.readSubjects) || body.readSubjects.length === 0) {
    res.status(400).json({ error: 'readSubjects is required' }); return
  }
  if (typeof body.task !== 'string' || !body.task.trim()) {
    res.status(400).json({ error: 'task is required' }); return
  }

  const t0 = Date.now()
  console.log(`[retrieve] subjects=${body.readSubjects.join(',')} task="${body.task}"`)

  const client = new StatewaveClient({
    baseUrl: process.env.STATEWAVE_URL ?? 'http://localhost:8100',
    apiKey: process.env.STATEWAVE_API_KEY,
  })

  const adapter = new StatewaveRetrievalAdapter(client as never)
  const config: MultiSubjectRetrievalConfig = {
    globalMaxTokens: DEFAULT_CONFIG.globalMaxTokens,
    ...(body.config ?? {}),
  }

  try {
    const bundle = await adapter.retrieve({
      readSubjects: body.readSubjects,
      task: body.task,
      sessionId: body.sessionId ?? 'example-session',
      config,
    })
    const ms = Date.now() - t0
    console.log(`[retrieve] ${ms}ms — ${bundle.items.length} items, ~${bundle.totalTokens} tokens, ok=[${bundle.successfulSubjects.join(',')}]`)
    if (bundle.subjectWarnings.length > 0) {
      for (const w of bundle.subjectWarnings) {
        console.warn(`[retrieve] WARNING subject=${w.subject} reason=${w.reason} detail=${w.detail ?? ''}`)
      }
    }
    if (bundle.items.length === 0) {
      console.warn(`[retrieve] 0 items returned — subject may have no compiled memories or retrieval failed silently`)
    } else {
      for (const item of bundle.items) {
        console.log(`[retrieve]   [${item.id}] subject=${item.subject} score=${item.score?.toFixed(3) ?? 'n/a'} tokens=${item.tokenCount ?? '?'} content="${item.content.slice(0, 80).replace(/\n/g, ' ')}…"`)
      }
    }
    res.json(bundle)
  } catch (err) {
    console.error('[retrieve] ERROR', err)
    res.status(502).json({ error: err instanceof Error ? err.message : 'retrieval_failed' })
  }
}
