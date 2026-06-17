/**
 * Theme provider + hook — ported from statewave-web/src/lib/theme.tsx.
 * Three modes: auto (follows OS), light, dark.  Persisted to localStorage.
 * Sets data-theme="dark"|"light" on <html> with transition suppression.
 */

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

export type ThemeMode = 'auto' | 'light' | 'dark'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'statewave-theme-mode'

interface ThemeContextValue {
  mode: ThemeMode
  resolvedTheme: ResolvedTheme | null
  setMode: (mode: ThemeMode) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function getSystemTheme(): ResolvedTheme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function resolveTheme(mode: ThemeMode): ResolvedTheme {
  return mode === 'auto' ? getSystemTheme() : mode
}

function readStoredMode(): ThemeMode {
  const v = localStorage.getItem(STORAGE_KEY)
  return v === 'light' || v === 'dark' || v === 'auto' ? v : 'auto'
}

function applyTheme(resolved: ResolvedTheme) {
  const html = document.documentElement
  html.style.setProperty('transition', 'none')
  html.setAttribute('data-theme', resolved)
  void html.offsetWidth
  requestAnimationFrame(() => html.style.removeProperty('transition'))
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>('auto')
  const [resolvedTheme, setResolved] = useState<ResolvedTheme | null>(null)

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode)
    localStorage.setItem(STORAGE_KEY, newMode)
    const resolved = resolveTheme(newMode)
    setResolved(resolved)
    applyTheme(resolved)
  }, [])

  useEffect(() => {
    const storedMode = readStoredMode()
    const resolved = resolveTheme(storedMode)
    setModeState(storedMode)
    setResolved(resolved)
    applyTheme(resolved)
  }, [])

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (mode === 'auto') {
        const resolved = getSystemTheme()
        setResolved(resolved)
        applyTheme(resolved)
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [mode])

  return (
    <ThemeContext.Provider value={{ mode, resolvedTheme, setMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
