/**
 * POST /api/chat/retrieve
 *
 * Receives a ChatRetrievalRequest from the browser adapter, calls the
 * Statewave server for each requested subject, and returns a ChatContextBundle.
 *
 * Uses StatewaveRetrievalAdapter from @statewavedev/chat-core/server so the
 * retrieval logic (token budgeting, multi-subject merge, warnings) is handled
 * by the library.
 */

import type { Request, Response } from 'express'
import { StatewaveClient } from '@statewavedev/sdk'
import { StatewaveRetrievalAdapter } from '@statewavedev/chat-core/server'
import type { ChatRetrievalRequest, MultiSubjectRetrievalConfig } from '@statewavedev/chat-core'

const DEFAULT_CONFIG: MultiSubjectRetrievalConfig = {
  globalMaxTokens: 2000,
}

export async function handleRetrieve(req: Request, res: Response): Promise<void> {
  const body = req.body as Partial<ChatRetrievalRequest>

  if (!Array.isArray(body.readSubjects) || body.readSubjects.length === 0) {
    res.status(400).json({ error: 'readSubjects is required' })
    return
  }
  if (typeof body.task !== 'string' || !body.task.trim()) {
    res.status(400).json({ error: 'task is required' })
    return
  }

  const client = new StatewaveClient({
    baseUrl: process.env.STATEWAVE_URL ?? 'http://localhost:8100',
    apiKey: process.env.STATEWAVE_API_KEY,
  })

  // StatewaveClient satisfies the structural StatewaveSDKClient interface
  // defined in @statewavedev/chat-core/server (getContext + createEpisode).
  const adapter = new StatewaveRetrievalAdapter(client as never)

  const config: MultiSubjectRetrievalConfig = { globalMaxTokens: DEFAULT_CONFIG.globalMaxTokens, ...(body.config ?? {}) }

  try {
    const bundle = await adapter.retrieve({
      readSubjects: body.readSubjects,
      task: body.task,
      sessionId: body.sessionId ?? 'example-session',
      config,
    })
    res.json(bundle)
  } catch (err) {
    const message = err instanceof Error ? err.message : 'retrieval_failed'
    res.status(502).json({ error: message })
  }
}
