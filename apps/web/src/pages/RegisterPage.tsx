import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { ThemeToggle } from '../components/ThemeToggle'
import { Button, Field, Input } from '../components/ui'
import { ApiError, api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function RegisterPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const [workshopName, setWorkshopName] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [country, setCountry] = useState('AT')
  const [ackDemo, setAckDemo] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!loading && user) {
    return <Navigate to={user.is_platform_admin ? '/operator' : '/dashboard'} replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.registerTenant({
        workshop_name: workshopName,
        admin_email: email,
        admin_full_name: fullName,
        password,
        country,
        plan_code: 'pkw_trial',
        acknowledge_demo: ackDemo,
      })
      await login(email, password)
      navigate('/commerce', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Registrierung fehlgeschlagen')
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
        <div className="mb-8 flex w-full max-w-lg flex-col items-center text-center">
          <BrandMark variant="wordmark" height="3.5rem" priority className="mb-3 max-w-full" />
          <p className="max-w-md text-sm text-[var(--dn-muted)]">
            Werkstatt-Konto anlegen (Pilot). Kein kommerzielles Voll-GO.
          </p>
        </div>
        <div className="dn-panel relative z-[1] w-full max-w-md p-8 shadow-2xl">
          <div className="dn-banner-sim mb-4 rounded-lg px-3 py-2 text-xs">
            <strong>PILOT</strong> – Demo/Trial. Nach der Anmeldung unter{' '}
            <em>/commerce</em> B2B- oder B2C-Abrechnungskonto anlegen. Keine Live-Zahlung ohne Mollie-Key.
          </div>
          <h1 className="mb-4 text-lg font-semibold text-[var(--dn-text)]">Registrierung</h1>
          <form onSubmit={onSubmit} className="space-y-3">
            <Field label="Werkstattname">
              <Input value={workshopName} onChange={(e) => setWorkshopName(e.target.value)} required minLength={2} />
            </Field>
            <Field label="Ihr Name">
              <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} />
            </Field>
            <Field label="E-Mail (Admin)">
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
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
            <Field label="Land">
              <Input value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} maxLength={2} required />
            </Field>
            <label className="flex items-start gap-2 text-xs text-[var(--dn-muted)]">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={ackDemo}
                onChange={(e) => setAckDemo(e.target.checked)}
                required
              />
              Ich verstehe: Pilot/Demo-Registrierung, Beispieldaten, keine produktive Zahlung, Rechts-/Steuerfreigabe offen.
            </label>
            {error && <p className="text-sm text-[var(--dn-danger)]">{error}</p>}
            <Button type="submit" variant="primary" disabled={busy || !ackDemo} className="w-full">
              {busy ? 'Registriere…' : 'Werkstatt registrieren'}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-[var(--dn-muted)]">
            Schon Konto?{' '}
            <Link to="/login" className="text-[var(--dn-accent)] underline">
              Anmelden
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
