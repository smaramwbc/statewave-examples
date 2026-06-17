/**
 * Chat UI built on @statewavedev/chat-react fine-grained hooks.
 *
 * - CSS-variable theming: data-theme="dark" (default) / "light", persisted to localStorage
 * - Error bubbles for status==="error" messages
 * - Context inspector as a sliding right-side panel
 * - Citation chip rendering [C1], [C2]…
 * - VITE_SHOW_CONTEXT=false env var disables the context inspector entirely
 */

import { useRef, useEffect, useState } from 'react'
import {
  useChatMessages,
  useChatLoading,
  useSendMessage,
  useChatReset,
  useChatContext,
} from '@statewavedev/chat-react'
import { ThemeSwitcher } from './ThemeSwitcher'

// ── Env config ────────────────────────────────────────────────────────────────

const CONTEXT_ENABLED =
  (import.meta as { env?: { VITE_SHOW_CONTEXT?: string } }).env?.VITE_SHOW_CONTEXT !== 'false'

// ── CSS variables ─────────────────────────────────────────────────────────────

const CSS_VARS = `
  :root, [data-theme="dark"] {
    --bg:           #0f172a;
    --surface:      #1e293b;
    --border:       rgba(255,255,255,0.08);
    --text:         #f1f5f9;
    --text2:        #94a3b8;
    --muted:        #475569;
    --accent:       #6366f1;
    --accent-bg:    rgba(99,102,241,0.15);
    --accent-border:rgba(99,102,241,0.25);
    --error-bg:     rgba(239,68,68,0.1);
    --error-border: rgba(239,68,68,0.25);
    --error-text:   #fca5a5;
  }
  [data-theme="light"] {
    --bg:           #f8fafc;
    --surface:      #ffffff;
    --border:       rgba(0,0,0,0.08);
    --text:         #0f172a;
    --text2:        #475569;
    --muted:        #94a3b8;
    --accent:       #6366f1;
    --accent-bg:    rgba(99,102,241,0.1);
    --accent-border:rgba(99,102,241,0.2);
    --error-bg:     rgba(239,68,68,0.07);
    --error-border: rgba(239,68,68,0.2);
    --error-text:   #ef4444;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; }
  @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-5px)} }
  textarea:focus { outline: none; }
`

// ── Citation rendering ────────────────────────────────────────────────────────

const CITATION_RE = /(\[C\d+\])/g

function renderWithCitations(text: string) {
  const parts = text.split(CITATION_RE)
  if (parts.length === 1) return text
  return parts.map((part, i) =>
    CITATION_RE.test(part) ? (
      <span
        key={i}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '0 5px',
          margin: '0 1px',
          borderRadius: '3px',
          fontSize: '10px',
          fontFamily: 'monospace',
          background: 'var(--accent-bg)',
          border: '1px solid var(--accent-border)',
          color: 'var(--accent)',
          verticalAlign: 'baseline',
        }}
      >
        {part}
      </span>
    ) : (
      part
    ),
  )
}

// ── Main component ────────────────────────────────────────────────────────────

const PANEL_WIDTH = 340

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
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.overflowY = 'hidden'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    const capped = el.scrollHeight > 120
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
    el.style.overflowY = capped ? 'auto' : 'hidden'
  }

  const hasContext = (contextBundle?.items.length ?? 0) > 0
  const hasMessages = messages.length > 0
  const panelOpen = CONTEXT_ENABLED && showContext && hasContext

  return (
    <>
      <style>{CSS_VARS}</style>

      {/* Backdrop — click outside to close panel */}
      <div
        onClick={() => setShowContext(false)}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.25)',
          backdropFilter: 'blur(1px)',
          zIndex: 49,
          opacity: panelOpen ? 1 : 0,
          pointerEvents: panelOpen ? 'auto' : 'none',
          transition: 'opacity 0.22s ease',
        }}
      />

      {/* Sliding context panel */}
      <div
        style={{
          position: 'fixed',
          top: 0, right: 0, bottom: 0,
          width: `${PANEL_WIDTH}px`,
          background: 'var(--surface)',
          borderLeft: '1px solid var(--border)',
          boxShadow: panelOpen ? '-8px 0 32px rgba(0,0,0,0.3)' : 'none',
          transform: panelOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.25s cubic-bezier(0.4,0,0.2,1), box-shadow 0.25s ease',
          zIndex: 50,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Panel header */}
        <div style={{
          padding: '14px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text)' }}>Retrieved Context</div>
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
              {contextBundle?.items.length ?? 0} items · ~{contextBundle?.totalTokens ?? 0} tokens
            </div>
          </div>
          <button
            onClick={() => setShowContext(false)}
            title="Close"
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              color: 'var(--muted)',
              cursor: 'pointer',
              fontSize: '13px',
              lineHeight: 1,
              padding: '5px 8px',
              transition: 'color 0.1s, border-color 0.1s',
            }}
          >
            ✕
          </button>
        </div>

        {/* Panel body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
          {contextBundle?.items.map((item) => (
            <div
              key={item.id}
              style={{
                padding: '10px 16px',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontFamily: 'monospace', color: 'var(--accent)', fontSize: '10px', fontWeight: 600 }}>[{item.id}]</span>
                <span style={{ color: 'var(--muted)', fontSize: '10px', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.subject}</span>
                {item.score != null && (
                  <span style={{ color: 'var(--muted)', fontSize: '10px', flexShrink: 0 }}>
                    {(item.score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <div style={{ color: 'var(--text2)', lineHeight: 1.5, fontSize: '11px' }}>{item.content}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat layout */}
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: '720px', margin: '0 auto', padding: '0 16px' }}>

        {/* Header */}
        <div style={{ padding: '16px 0 12px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}>Chat with Memory</div>
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
              <code style={{ fontFamily: 'monospace', color: 'var(--accent)', fontSize: '11px' }}>{subject}</code>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
            {CONTEXT_ENABLED && hasContext && (
              <button
                onClick={() => setShowContext((v) => !v)}
                style={btnStyle(showContext ? 'accent' : 'default')}
              >
                {showContext ? 'Hide' : 'Context'} ({contextBundle!.items.length})
              </button>
            )}
            {hasMessages && (
              <button onClick={reset} style={btnStyle('default')}>Clear</button>
            )}
            <ThemeSwitcher />
          </div>
        </div>

        {/* Messages */}
        {!hasMessages && !isLoading ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--muted)', fontSize: '14px', textAlign: 'center', padding: '0 24px' }}>
            <div style={{ fontSize: '28px' }}>💬</div>
            <div style={{ color: 'var(--text2)', fontWeight: 500 }}>Start a conversation</div>
            <div style={{ fontSize: '12px' }}>
              Answers are grounded in memory from <em style={{ color: 'var(--accent)', fontStyle: 'normal', fontFamily: 'monospace' }}>{subject}</em>
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '20px 0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {messages.map((msg) => {
              const isUser = msg.role === 'user'
              const isError = msg.status === 'error'

              if (isError) {
                return (
                  <div key={msg.id} style={{ alignSelf: 'flex-start', maxWidth: '86%', padding: '10px 14px', borderRadius: '12px 12px 12px 4px', background: 'var(--error-bg)', border: '1px solid var(--error-border)', color: 'var(--error-text)', fontSize: '13px', lineHeight: 1.6 }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, marginBottom: '4px', opacity: 0.8 }}>Error</div>
                    {msg.error?.message ?? msg.content}
                  </div>
                )
              }

              return (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: isUser ? 'flex-end' : 'flex-start',
                    maxWidth: '82%',
                    padding: '10px 14px',
                    borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    background: isUser ? 'var(--accent-bg)' : 'var(--surface)',
                    border: `1px solid ${isUser ? 'var(--accent-border)' : 'var(--border)'}`,
                    color: 'var(--text)',
                    fontSize: '14px',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {isUser ? msg.content : renderWithCitations(msg.content)}
                </div>
              )
            })}
            {isLoading && (
              <div style={{ alignSelf: 'flex-start', padding: '12px 16px', borderRadius: '16px 16px 16px 4px', background: 'var(--surface)', border: '1px solid var(--border)', display: 'flex', gap: '4px', alignItems: 'center' }}>
                {[0, 150, 300].map((d) => (
                  <span key={d} style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--muted)', animation: 'bounce 1.2s infinite', animationDelay: `${d}ms`, display: 'block' }} />
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Composer */}
        <div style={{ padding: '12px 0 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask about memory in this subject…"
            rows={1}
            style={{ flex: 1, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '10px', padding: '10px 12px', fontSize: '14px', color: 'var(--text)', resize: 'none', overflowY: 'hidden', lineHeight: '1.5', minHeight: '40px', maxHeight: '120px', transition: 'border-color 0.15s' }}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !draft.trim()}
            style={{ padding: '10px 16px', background: isLoading || !draft.trim() ? 'rgba(99,102,241,0.3)' : 'var(--accent)', border: 'none', borderRadius: '10px', color: '#fff', fontSize: '14px', fontWeight: 500, cursor: isLoading || !draft.trim() ? 'not-allowed' : 'pointer', transition: 'background 0.15s', flexShrink: 0 }}
          >
            {isLoading ? '…' : 'Send'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function btnStyle(variant: 'default' | 'accent'): React.CSSProperties {
  return {
    fontSize: '11px',
    padding: '5px 10px',
    borderRadius: '6px',
    cursor: 'pointer',
    border: '1px solid',
    background: variant === 'accent' ? 'var(--accent-bg)' : 'transparent',
    borderColor: variant === 'accent' ? 'var(--accent-border)' : 'var(--border)',
    color: variant === 'accent' ? 'var(--accent)' : 'var(--muted)',
    transition: 'background 0.1s, color 0.1s',
    lineHeight: 1.4,
  }
}
