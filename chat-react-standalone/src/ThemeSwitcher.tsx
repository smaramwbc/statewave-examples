/**
 * ThemeSwitcher — pixel-exact port of statewave-web's ThemeSwitcher.
 * Three-button pill: monitor (auto) · sun (light) · moon (dark).
 */

import { useTheme, type ThemeMode } from './theme'

const MODES: { value: ThemeMode; label: string; icon: React.ReactNode }[] = [
  {
    value: 'auto',
    label: 'Auto',
    icon: (
      <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    value: 'light',
    label: 'Light',
    icon: (
      <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
  },
  {
    value: 'dark',
    label: 'Dark',
    icon: (
      <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    ),
  },
]

export function ThemeSwitcher() {
  const { mode, setMode } = useTheme()

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '2px',
      borderRadius: '999px',
      border: '1px solid var(--border)',
      background: 'var(--surface)',
      padding: '3px',
    }}>
      {MODES.map((m) => {
        const active = mode === m.value
        return (
          <button
            key={m.value}
            onClick={() => setMode(m.value)}
            aria-label={`Switch to ${m.label} theme`}
            title={m.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              border: 'none',
              cursor: 'pointer',
              background: active ? 'var(--accent)' : 'transparent',
              color: active ? '#fff' : 'var(--muted)',
              boxShadow: active ? '0 1px 3px rgba(99,102,241,0.35)' : 'none',
              transition: 'background 0.2s, color 0.2s, box-shadow 0.2s',
            }}
          >
            {m.icon}
          </button>
        )
      })}
    </div>
  )
}
