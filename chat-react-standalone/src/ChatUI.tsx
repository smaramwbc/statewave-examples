/**
 * Minimal chat UI built on @statewavedev/chat-react primitives.
 *
 * Uses the hook-based API so you can see exactly what state is available and
 * swap in any render layer you like.  The provider lives in App.tsx.
 */

import { useRef, useEffect, useState } from 'react'
import {
  useChatMessages,
  useChatLoading,
  useSendMessage,
  useChatReset,
  useChatContext,
} from '@statewavedev/chat-react'

const S = {
  shell: {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100vh',
    maxWidth: '720px',
    margin: '0 auto',
    padding: '0 16px',
  },
  header: {
    padding: '20px 0 12px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: { fontSize: '16px', fontWeight: 600, color: '#f1f5f9' },
  subtitle: { fontSize: '12px', color: '#64748b', marginTop: '2px' },
  resetBtn: {
    fontSize: '12px',
    color: '#64748b',
    background: 'none',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '6px',
    padding: '4px 10px',
    cursor: 'pointer',
  },
  messages: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '20px 0',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  empty: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    color: '#475569',
    fontSize: '14px',
  },
  bubble: (role: string) => ({
    maxWidth: '80%',
    alignSelf: role === 'user' ? ('flex-end' as const) : ('flex-start' as const),
    background: role === 'user' ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.05)',
    border: `1px solid ${role === 'user' ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.08)'}`,
    borderRadius: role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
    padding: '10px 14px',
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#e2e8f0',
    whiteSpace: 'pre-wrap' as const,
  }),
  thinking: {
    alignSelf: 'flex-start' as const,
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '16px 16px 16px 4px',
    padding: '12px 16px',
    display: 'flex',
    gap: '4px',
    alignItems: 'center',
  },
  dot: (delay: number) => ({
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#64748b',
    animation: 'bounce 1.2s infinite',
    animationDelay: `${delay}ms`,
  }),
  composer: {
    padding: '12px 0 24px',
    borderTop: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    gap: '8px',
    alignItems: 'flex-end',
  },
  textarea: {
    flex: 1,
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '10px',
    padding: '10px 12px',
    fontSize: '14px',
    color: '#f1f5f9',
    resize: 'none' as const,
    outline: 'none',
    lineHeight: '1.5',
    minHeight: '40px',
    maxHeight: '120px',
  },
  sendBtn: (disabled: boolean) => ({
    padding: '10px 16px',
    background: disabled ? 'rgba(99,102,241,0.3)' : '#6366f1',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: 500,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'background 0.15s',
    flexShrink: 0,
  }),
  citationChip: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '0 5px',
    margin: '0 1px',
    borderRadius: '3px',
    fontSize: '10px',
    fontFamily: 'monospace',
    background: 'rgba(99,102,241,0.15)',
    border: '1px solid rgba(99,102,241,0.3)',
    color: '#818cf8',
  },
  contextPanel: {
    marginTop: '8px',
    padding: '10px 12px',
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '8px',
    fontSize: '11px',
    color: '#475569',
  },
}

const CITATION_RE = /(\[C\d+\])/g

function renderWithCitations(text: string) {
  const parts = text.split(CITATION_RE)
  return parts.map((part, i) =>
    CITATION_RE.test(part) ? (
      <span key={i} style={S.citationChip}>{part}</span>
    ) : (
      part
    ),
  )
}

export function ChatUI({ subject }: { subject: string }) {
  const messages = useChatMessages()
  const isLoading = useChatLoading()
  const sendMessage = useSendMessage()
  const reset = useChatReset()
  const contextBundle = useChatContext()

  const [draft, setDraft] = useState('')
  const [showContext, setShowContext] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isLoading])

  const handleSend = () => {
    const text = draft.trim()
    if (!text || isLoading) return
    sendMessage(text)
    setDraft('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
  }

  const hasContext = (contextBundle?.items.length ?? 0) > 0

  return (
    <>
      <style>{`@keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-5px)} }`}</style>

      <div style={S.shell}>
        {/* Header */}
        <div style={S.header}>
          <div>
            <div style={S.title}>Chat with Memory</div>
            <div style={S.subtitle}>
              Subject: <code style={{ fontFamily: 'monospace', color: '#818cf8' }}>{subject}</code>
              {hasContext && (
                <button
                  style={{ ...S.resetBtn, marginLeft: '8px', borderColor: 'rgba(99,102,241,0.3)', color: '#818cf8' }}
                  onClick={() => setShowContext((v) => !v)}
                >
                  {showContext ? 'Hide' : 'Show'} context ({contextBundle!.items.length})
                </button>
              )}
            </div>
          </div>
          {messages.length > 0 && (
            <button style={S.resetBtn} onClick={reset}>Clear</button>
          )}
        </div>

        {/* Context inspector */}
        {showContext && hasContext && (
          <div style={S.contextPanel}>
            <strong style={{ color: '#94a3b8' }}>Retrieved context ({contextBundle!.items.length} items, ~{contextBundle!.totalTokens} tokens)</strong>
            {contextBundle!.items.map((item) => (
              <div key={item.id} style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                <span style={{ color: '#6366f1', fontFamily: 'monospace' }}>[{item.id}]</span>{' '}
                <span style={{ color: '#64748b' }}>{item.subject}</span>
                {item.score != null && <span style={{ color: '#475569', marginLeft: '4px' }}>· {(item.score * 100).toFixed(0)}%</span>}
                <div style={{ marginTop: '4px', color: '#94a3b8', lineHeight: 1.5 }}>{item.content}</div>
              </div>
            ))}
          </div>
        )}

        {/* Messages */}
        {messages.length === 0 && !isLoading ? (
          <div style={S.empty}>
            <div style={{ fontSize: '28px' }}>💬</div>
            <div>Start a conversation</div>
            <div style={{ fontSize: '12px' }}>Answers are grounded in memory retrieved from <em>{subject}</em></div>
          </div>
        ) : (
          <div style={S.messages}>
            {messages.map((msg) => (
              <div key={msg.id} style={S.bubble(msg.role)}>
                {renderWithCitations(msg.content)}
              </div>
            ))}
            {isLoading && (
              <div style={S.thinking}>
                {[0, 150, 300].map((d) => <span key={d} style={S.dot(d)} />)}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Composer */}
        <div style={S.composer}>
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask about memory in this subject…"
            rows={1}
            style={S.textarea}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !draft.trim()}
            style={S.sendBtn(isLoading || !draft.trim())}
          >
            {isLoading ? '…' : 'Send'}
          </button>
        </div>
      </div>
    </>
  )
}
