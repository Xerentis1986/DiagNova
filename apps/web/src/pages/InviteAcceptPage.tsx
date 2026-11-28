import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { Button, Field, Input } from '../components/ui'
import { ApiError, api } from '../lib/api'
import { useAuth } from '../lib/auth'

/** Team-Einladung annehmen: /invite?token=… */
export function InviteAcceptPage() {
  const { user, loading, login } = useAuth()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!loading && user) return <Navigate to="/dashboard" replace />
  if (!token) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6">
        <p className="text-sm text-[var(--dn-danger)]">Einladungs-Token fehlt (?token=…).</p>
        <Link to="/register" className="text-[var(--dn-accent)] underline">
          Stattdessen Werkstatt registrieren
        </Link>
      </div>
    )
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const inv = await api.acceptInvitation({ token, full_name: fullName, password })
      await login(String(inv.email), password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Einladung fehlgeschlagen')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <BrandMark variant="wordmark" height="3rem" className="mb-6" />
      <div className="dn-panel w-full max-w-md p-8">
        <h1 className="mb-4 text-lg font-semibold">Einladung annehmen</h1>
        <form onSubmit={onSubmit} className="space-y-3">
          <Field label="Vollständiger Name">
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </Field>
          <Field label="Passwort setzen">
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </Field>
          {error && <p className="text-sm text-[var(--dn-danger)]">{error}</p>}
          <Button type="submit" variant="primary" disabled={busy} className="w-full">
            {busy ? '…' : 'Einladung annehmen'}
          </Button>
        </form>
      </div>
    </div>
  )
}
