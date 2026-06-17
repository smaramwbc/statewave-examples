# chat-react-standalone

A runnable standalone chat app built on `@statewavedev/chat-react`.

Demonstrates the full proxy-adapter pattern:

```
Browser (React)                  Server (Express)             Statewave + LLM
──────────────────               ─────────────────────        ─────────────────
StatewaveChatProvider            POST /api/chat/retrieve  →   StatewaveRetrievalAdapter
  → proxy adapter.retrieve()  →  POST /api/chat/complete  →   StatewaveCompletionAdapter
  → proxy adapter.complete()
```

The Statewave API key and LLM API key stay server-side — the browser adapter contains no secrets.

## Prerequisites

- [Statewave server running](https://github.com/smaramwbc/statewave-docs/blob/main/getting-started.md) (default: `http://localhost:8100`)
- Node.js ≥ 20
- An LLM API key (OpenAI or Anthropic)

## Setup

```bash
cd chat-react-standalone
npm install
cp .env.example .env
# edit .env — set LLM_API_KEY and optionally STATEWAVE_URL
```

## Run

```bash
npm run dev
```

Opens `http://localhost:5173`.  The Vite dev server proxies `/api` to the Express server on port 3001.

## Subject selection

The subject to query is read from the `?subject=` query parameter:

```
http://localhost:5173?subject=alice-123
```

Or set `VITE_SUBJECT` in `.env` for a static default.  Falls back to `demo-user-1`.

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `STATEWAVE_URL` | `http://localhost:8100` | Statewave server |
| `STATEWAVE_API_KEY` | — | API key if auth is enabled |
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `LLM_API_KEY` | — | Provider API key |
| `LLM_BASE_URL` | provider default | Override for OpenAI-compatible proxies |
| `VITE_SUBJECT` | `demo-user-1` | Default subject |

## What this covers

- `StatewaveChatProvider` — wraps the headless engine and exposes session state via context
- `useChatMessages`, `useChatLoading`, `useSendMessage`, `useChatReset`, `useChatContext` — fine-grained hooks
- Proxy adapter pattern — browser-safe adapter that delegates to a server route
- `StatewaveRetrievalAdapter` and `StatewaveCompletionAdapter` from `@statewavedev/chat-core/server` — typed server-side adapters
- Context inspector — shows retrieved memory items with relevance scores
- Citation chips — `[C1]`, `[C2]` in the assistant reply reference retrieved items

## Files

```
src/
  adapter.ts      Browser-side proxy adapter (no secrets)
  App.tsx         StatewaveChatProvider setup
  ChatUI.tsx      Chat UI using fine-grained hooks
server/
  retrieve.ts     POST /api/chat/retrieve — calls Statewave
  complete.ts     POST /api/chat/complete — calls LLM
  index.ts        Express entry point
```
