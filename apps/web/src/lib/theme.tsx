import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, type ThemePreference } from './api'
import { useAuth } from './auth'

const STORAGE_KEY = 'dn_theme'

interface ThemeState {
  preference: ThemePreference
  resolved: 'light' | 'dark'
  setPreference: (value: ThemePreference) => Promise<void>
}

const ThemeContext = createContext<ThemeState | null>(null)

function systemPrefersDark(): boolean {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

function resolve(pref: ThemePreference): 'light' | 'dark' {
  if (pref === 'system') return systemPrefersDark() ? 'dark' : 'light'
  return pref
}

function applyDom(resolved: 'light' | 'dark') {
  document.documentElement.dataset.theme = resolved
  document.documentElement.style.colorScheme = resolved
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { user, token } = useAuth()
  const [preference, setPreferenceState] = useState<ThemePreference>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemePreference | null
    return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system'
  })

  const resolved = resolve(preference)

  useEffect(() => {
    applyDom(resolved)
  }, [resolved])

  useEffect(() => {
    if (preference !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => applyDom(resolve('system'))
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [preference])

  useEffect(() => {
    if (!user?.theme_preference) return
    const remote = user.theme_preference
    if (remote === preference) return
    setPreferenceState(remote)
    localStorage.setItem(STORAGE_KEY, remote)
  }, [user?.theme_preference]) // eslint-disable-line react-hooks/exhaustive-deps

  const setPreference = useCallback(
    async (value: ThemePreference) => {
      setPreferenceState(value)
      localStorage.setItem(STORAGE_KEY, value)
      applyDom(resolve(value))
      if (token) {
        try {
          await api.updatePreferences(value)
        } catch {
          /* lokal bleibt erhalten; Sync später erneut */
        }
      }
    },
    [token],
  )

  const value = useMemo(
    () => ({ preference, resolved, setPreference }),
    [preference, resolved, setPreference],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme außerhalb von ThemeProvider')
  return ctx
}
