/**
 * App — wires StatewaveChatProvider to the proxy adapter and renders ChatUI.
 *
 * The subject is read from ?subject=<id> so you can test different memory
 * subjects without a rebuild.  Falls back to VITE_SUBJECT if set, then to
 * "demo-user-1".
 */

import { StatewaveChatProvider } from '@statewavedev/chat-react'
import { adapter } from './adapter'
import { ChatUI } from './ChatUI'

const viteSubject = (import.meta as { env?: { VITE_SUBJECT?: string } }).env?.VITE_SUBJECT ?? null

const subject =
  new URLSearchParams(window.location.search).get('subject') ??
  viteSubject ??
  'demo-user-1'

export function App() {
  return (
    <StatewaveChatProvider
      adapter={adapter}
      readSubjects={[subject]}
      retrievalConfig={{
        globalMaxTokens: 2000,
      }}
    >
      <ChatUI subject={subject} />
    </StatewaveChatProvider>
  )
}
