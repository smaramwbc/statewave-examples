/**
 * POST /api/chat/complete
 *
 * Receives a ChatCompletionRequest (messages + context bundle) and calls the
 * configured LLM.  Uses StatewaveCompletionAdapter from
 * @statewavedev/chat-core/server so system-prompt assembly and structured-
 * output parsing are handled by the library.
 *
 * Supported providers (set LLM_PROVIDER env var):
 *   openai     — OpenAI Chat Completions (default)
 *   anthropic  — Anthropic Messages API
 *
 * Required env vars:
 *   LLM_PROVIDER  openai | anthropic          (default: openai)
 *   LLM_MODEL     e.g. gpt-4o-mini            (default: gpt-4o-mini)
 *   LLM_API_KEY   your provider API key
 *   LLM_BASE_URL  optional base URL override (for OpenAI-compatible proxies)
 */

import type { Request, Response } from 'express'
import { StatewaveCompletionAdapter } from '@statewavedev/chat-core/server'
import type { LLMCompletionFn } from '@statewavedev/chat-core/server'
import { DEFAULT_ANSWER_POLICY } from '@statewavedev/chat-core'
import type { ChatCompletionRequest } from '@statewavedev/chat-core'

function buildLLMFn(): LLMCompletionFn {
  const provider = process.env.LLM_PROVIDER ?? 'openai'
  const model = process.env.LLM_MODEL ?? 'gpt-4o-mini'
  const apiKey = process.env.LLM_API_KEY ?? ''
  const baseUrl = process.env.LLM_BASE_URL

  if (!apiKey) throw new Error('LLM not configured — set LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY in .env')

  if (provider === 'anthropic') {
    const url = `${(baseUrl ?? 'https://api.anthropic.com').replace(/\/+$/, '')}/v1/messages`
    return async (messages, opts) => {
      const system = messages.find((m) => m.role === 'system')?.content ?? ''
      const rest = messages.filter((m) => m.role !== 'system')
      const t0 = Date.now()
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({ model, max_tokens: 1024, system, messages: rest }),
        signal: opts?.signal,
      })
      if (!res.ok) throw new Error(`Anthropic HTTP ${res.status}`)
      const data = (await res.json()) as { content?: Array<{ type?: string; text?: string }> }
      const content = data.content?.find((b) => b.type === 'text')?.text ?? ''
      return { content, model, durationMs: Date.now() - t0 }
    }
  }

  // OpenAI / openai-compatible
  const url = `${(baseUrl ?? 'https://api.openai.com').replace(/\/+$/, '')}/v1/chat/completions`
  return async (messages, opts) => {
    const t0 = Date.now()
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ model, messages }),
      signal: opts?.signal,
    })
    if (!res.ok) throw new Error(`OpenAI HTTP ${res.status}`)
    const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }>; model?: string }
    const content = data.choices?.[0]?.message?.content ?? ''
    return { content, model: data.model ?? model, durationMs: Date.now() - t0 }
  }
}

let _adapter: StatewaveCompletionAdapter | null = null
function getAdapter(): StatewaveCompletionAdapter {
  _adapter ??= new StatewaveCompletionAdapter(buildLLMFn())
  return _adapter
}

export async function handleComplete(req: Request, res: Response): Promise<void> {
  const body = req.body as Partial<ChatCompletionRequest>

  if (!Array.isArray(body.messages) || body.messages.length === 0) {
    res.status(400).json({ error: 'messages is required' })
    return
  }
  if (!body.context) {
    res.status(400).json({ error: 'context is required' })
    return
  }

  let adapter: StatewaveCompletionAdapter
  try {
    adapter = getAdapter()
  } catch (err) {
    res.status(503).json({ error: err instanceof Error ? err.message : 'llm_not_configured' })
    return
  }

  try {
    const result = await adapter.complete({
      messages: body.messages,
      context: body.context,
      answerPolicy: body.answerPolicy ?? DEFAULT_ANSWER_POLICY,
      sessionId: body.sessionId ?? 'example-session',
    })
    res.json(result)
  } catch (err) {
    const message = err instanceof Error ? err.message : 'completion_failed'
    res.status(502).json({ error: message })
  }
}
