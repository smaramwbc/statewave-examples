/**
 * Browser-side proxy adapter.
 *
 * Implements the ChatAdapter interface by forwarding retrieval and completion
 * requests to the Express server at /api/chat/*.  The Statewave API key and
 * LLM API key stay server-side — this module contains no secrets.
 */

import type {
  ChatAdapter,
  ChatCompletionRequest,
  ChatCompletionResult,
  ChatContextBundle,
  ChatRetrievalRequest,
} from '@statewavedev/chat-core'

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${path} → HTTP ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export const adapter: ChatAdapter = {
  retrieval: {
    retrieve(req: ChatRetrievalRequest, opts?: { signal?: AbortSignal }): Promise<ChatContextBundle> {
      return post('/api/chat/retrieve', req, opts?.signal)
    },
  },
  completion: {
    complete(req: ChatCompletionRequest, opts?: { signal?: AbortSignal }): Promise<ChatCompletionResult> {
      return post('/api/chat/complete', req, opts?.signal)
    },
  },
}
