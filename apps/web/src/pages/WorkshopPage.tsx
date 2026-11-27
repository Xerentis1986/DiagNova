import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function WorkshopPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const isAdmin = user?.role === 'admin'
  const [msg, setMsg] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [city, setCity] = useState('')
  const [retention, setRetention] = useState(365)
  const [loaded, setLoaded] = useState(false)

  const workshop = useQuery({
    queryKey: ['workshop-me'],
    queryFn: async () => {
      const w = await api.workshopMe()
      if (!loaded) {
        setName(w.name)
        setPhone(w.phone || '')
        setEmail(w.email || '')
        setCity(w.city || '')
        setRetention(w.retention_days)
        setLoaded(true)
      }
      return w
    },
  })

  const members = useQuery({
    queryKey: ['workshop-members'],
    queryFn: () => api.workshopMembers(),
  })

  const save = useMutation({
    mutationFn: () =>
      api.updateWorkshop({
        name,
        phone: phone || null,
        email: email || null,
        city: city || null,
        retention_days: retention,
      }),
    onSuccess: () => {
      setMsg('Werkstattprofil gespeichert')
      void qc.invalidateQueries({ queryKey: ['workshop-me'] })
    },
    onError: (e: Error) => setMsg(e.message),
  })

  if (workshop.isLoading) return <p className="text-[var(--dn-muted)]">Werkstatt wird geladen…</p>
  if (workshop.error || !workshop.data) {
    return <p className="text-[var(--dn-danger)]">Werkstatt konnte nicht geladen werden.</p>
  }

  const w = workshop.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Werkstattprofil</h1>
        <p className="text-sm text-[var(--dn-muted)]">
          Mandant serverseitig gebunden. Nur minimale Kontaktdaten – keine erfundenen Produktivdaten.
        </p>
      </div>

      {msg && (
        <p className="rounded-md border border-[var(--dn-border)] bg-[var(--dn-hover)] px-3 py-2 text-sm" role="status">
          {msg}
        </p>
      )}

      <section className="dn-panel space-y-3 p-4">
        <h2 className="text-lg font-medium">{w.name}</h2>
        {w.is_example_data && (
          <p className="text-xs text-[var(--dn-warn)]">Beispieldaten / Demo-Werkstatt</p>
        )}
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-[var(--dn-muted)]">Mandanten-ID</dt>
            <dd className="font-mono text-xs">{w.id}</dd>
          </div>
          <div>
            <dt className="text-[var(--dn-muted)]">Aufbewahrung (Tage)</dt>
            <dd>{w.retention_days}</dd>
          </div>
          <div>
            <dt className="text-[var(--dn-muted)]">Adresse</dt>
            <dd>
              {[w.street, w.postal_code, w.city, w.country].filter(Boolean).join(', ') || '—'}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--dn-muted)]">Logo</dt>
            <dd>{w.has_logo ? 'hinterlegt' : 'keins'}</dd>
          </div>
        </dl>

        {isAdmin ? (
          <form
            className="mt-4 grid gap-3 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault()
              save.mutate()
            }}
          >
            <label className="text-sm">
              Name
              <input
                className="mt-1 w-full rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </label>
            <label className="text-sm">
              E-Mail
              <input
                type="email"
                className="mt-1 w-full rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label className="text-sm">
              Telefon
              <input
                className="mt-1 w-full rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </label>
            <label className="text-sm">
              Ort
              <input
                className="mt-1 w-full rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </label>
            <label className="text-sm">
              Aufbewahrungstage
              <input
                type="number"
                min={30}
                max={3650}
                className="mt-1 w-full rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2"
                value={retention}
                onChange={(e) => setRetention(Number(e.target.value))}
              />
            </label>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={save.isPending}
                className="rounded-md bg-[var(--dn-accent)] px-4 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
              >
                Speichern
              </button>
            </div>
          </form>
        ) : (
          <p className="text-sm text-[var(--dn-muted)]">Profiländerung nur für Werkstatt-Admin.</p>
        )}
      </section>

      <section className="dn-panel p-4">
        <h2 className="mb-3 text-lg font-medium">Rollen / Mitglieder</h2>
        {members.isLoading ? (
          <p className="text-sm text-[var(--dn-muted)]">Laden…</p>
        ) : (
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {(members.data || []).map((m) => (
              <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <span>
                  {m.full_name} · {m.email}
                </span>
                <span className="rounded bg-[var(--dn-hover)] px-2 py-0.5 text-xs uppercase">
                  {m.role}
                  {!m.is_active ? ' · inaktiv' : ''}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
