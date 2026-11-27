import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { ApiError } from '../lib/api'

export function LoginPage() {
  const { user, login, loading } = useAuth()
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('AdminDemo123!')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!loading && user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login fehlgeschlagen')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="dn-panel w-full max-w-md p-8 shadow-2xl shadow-blue-950/40">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-xl bg-blue-600 text-xl font-bold">
            DN
          </div>
          <h1 className="text-2xl font-semibold">DiagNova</h1>
          <p className="mt-1 text-sm text-[var(--dn-muted)]">Werkstatt-Diagnose · Demo-Anmeldung</p>
        </div>
        <div className="dn-banner-sim mb-4 rounded-lg px-3 py-2 text-xs">
          Demo-Zugang vorkonfiguriert. Alle Diagnosedaten sind <strong>simuliert</strong>.
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--dn-muted)]">E-Mail</span>
            <input
              className="dn-input w-full"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--dn-muted)]">Passwort</span>
            <input
              className="dn-input w-full"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          {error && <p className="text-sm text-[var(--dn-danger)]">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-blue-600 px-4 py-2.5 font-medium text-white hover:bg-blue-500 disabled:opacity-60"
          >
            {busy ? 'Anmelden…' : 'Anmelden'}
          </button>
        </form>
        <p className="mt-4 text-xs text-slate-500">
          Seed: admin@example.com / AdminDemo123! · tech@example.com / TechDemo123!
        </p>
      </div>
    </div>
  )
}
