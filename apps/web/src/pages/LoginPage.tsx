import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { ThemeToggle } from '../components/ThemeToggle'
import { Button, Field, Input } from '../components/ui'
import { useAuth } from '../lib/auth'
import { ApiError } from '../lib/api'

export function LoginPage() {
  const { user, login, loading } = useAuth()
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('AdminDemo123!')
  const [mfaCode, setMfaCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!loading && user) {
    if (user.is_platform_admin) return <Navigate to="/operator" replace />
    return <Navigate to="/" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password, mfaCode.trim() || undefined)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login fehlgeschlagen')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="dn-login-hero flex min-h-screen flex-col">
      <div className="flex justify-end px-4 py-3">
        <ThemeToggle />
      </div>
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-16">
        <div className="mb-10 flex w-full max-w-lg flex-col items-center text-center">
          <BrandMark variant="wordmark" height="4.5rem" priority className="mb-4 max-w-full" />
          <p className="max-w-sm text-base text-[var(--dn-muted)]">
            Werkstatt-Diagnose · Mehrmarken · Demo-Anmeldung
          </p>
        </div>
        <div className="dn-panel relative z-[1] w-full max-w-md p-8 shadow-2xl shadow-[color-mix(in_srgb,var(--diagnova-charcoal)_28%,transparent)]">
          <div className="mb-5 flex justify-center">
            <BrandMark variant="symbol" height="3rem" priority />
          </div>
          <h1 className="sr-only">DiagNova Anmeldung</h1>
          <div className="dn-banner-sim mb-4 rounded-lg px-3 py-2 text-xs">
            Demo-Zugang vorkonfiguriert. Alle Diagnosedaten sind <strong>simuliert</strong>.
          </div>
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="E-Mail">
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Field>
            <Field label="Passwort">
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </Field>
            <Field label="MFA-Code (falls aktiv)">
              <Input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                maxLength={8}
                placeholder="nur wenn MFA aktiv"
              />
            </Field>
            {error && <p className="text-sm text-[var(--dn-danger)]">{error}</p>}
            <Button type="submit" variant="primary" disabled={busy} className="w-full">
              {busy ? 'Anmelden…' : 'Anmelden'}
            </Button>
          </form>
          <p className="mt-4 text-xs text-[var(--dn-muted)]">
            Seed: admin@example.com / AdminDemo123! · tech@example.com / TechDemo123!
          </p>
        </div>
      </div>
    </div>
  )
}
