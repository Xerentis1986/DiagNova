import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api, ApiError, type Customer } from '../lib/api'
import { useAuth } from '../lib/auth'

export function CustomersPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'technician'
  const qc = useQueryClient()
  const [q, setQ] = useState('')
  const [msg, setMsg] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [city, setCity] = useState('')
  const [mergeSource, setMergeSource] = useState('')
  const [mergeTarget, setMergeTarget] = useState('')

  const customers = useQuery({
    queryKey: ['customers', q],
    queryFn: () => api.customers({ q: q || undefined }),
  })

  const refresh = () => void qc.invalidateQueries({ queryKey: ['customers'] })

  const create = useMutation({
    mutationFn: (force: boolean) =>
      api.createCustomer({
        display_name: name,
        email: email || null,
        phone: phone || null,
        city: city || null,
        force,
      }),
    onSuccess: () => {
      setMsg('Kunde angelegt')
      setName('')
      setEmail('')
      setPhone('')
      setCity('')
      refresh()
    },
    onError: (e: Error) => {
      if (e instanceof ApiError && e.status === 409) {
        setMsg(`${e.message} – erneut mit „Trotzdem anlegen“ möglich.`)
      } else {
        setMsg(e.message)
      }
    },
  })

  const merge = useMutation({
    mutationFn: () => api.mergeCustomer(mergeTarget, mergeSource),
    onSuccess: () => {
      setMsg('Kunden zusammengeführt')
      setMergeSource('')
      setMergeTarget('')
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  async function onExport(c: Customer) {
    try {
      await api.exportCustomer(c.id)
      setMsg(`Export: ${c.display_name}`)
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Export fehlgeschlagen')
    }
  }

  const archive = useMutation({
    mutationFn: (id: string) => api.deleteCustomer(id, 'archive'),
    onSuccess: () => {
      setMsg('Kunde archiviert')
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  if (customers.isLoading) return <p className="text-[var(--dn-muted)]">Kunden werden geladen…</p>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Kunden</h1>
        <p className="text-sm text-[var(--dn-muted)]">
          Suche, Archivierung, Dubletten-Merge und DSGVO-Export – nur eigener Mandant.
        </p>
      </div>

      {msg && (
        <p className="rounded-md border border-[var(--dn-border)] bg-[var(--dn-hover)] px-3 py-2 text-sm" role="status">
          {msg}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <input
          className="min-w-[12rem] flex-1 rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
          placeholder="Suche Name, E-Mail, Telefon, Ort…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Kundensuche"
        />
      </div>

      {canWrite && (
        <section className="dn-panel space-y-3 p-4">
          <h2 className="text-lg font-medium">Neuer Kunde</h2>
          <form
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
            onSubmit={(e) => {
              e.preventDefault()
              create.mutate(false)
            }}
          >
            <input
              required
              placeholder="Name *"
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <input
              placeholder="E-Mail"
              type="email"
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              placeholder="Telefon"
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
            <input
              placeholder="Ort"
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
            <div className="flex flex-wrap gap-2 sm:col-span-2 lg:col-span-4">
              <button
                type="submit"
                className="rounded-md bg-[var(--dn-accent)] px-3 py-2 text-sm text-white hover:opacity-90"
              >
                Anlegen
              </button>
              <button
                type="button"
                className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)]"
                onClick={() => create.mutate(true)}
              >
                Trotzdem anlegen (Dublette)
              </button>
            </div>
          </form>

          <div className="border-t border-[var(--dn-border)] pt-3">
            <h3 className="mb-2 text-sm font-medium">Manuelle Zusammenführung</h3>
            <div className="flex flex-wrap gap-2">
              <input
                placeholder="Ziel-Kunden-ID"
                className="min-w-[14rem] flex-1 rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 font-mono text-xs"
                value={mergeTarget}
                onChange={(e) => setMergeTarget(e.target.value)}
              />
              <input
                placeholder="Quell-Kunden-ID (wird archiviert)"
                className="min-w-[14rem] flex-1 rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 font-mono text-xs"
                value={mergeSource}
                onChange={(e) => setMergeSource(e.target.value)}
              />
              <button
                type="button"
                className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)]"
                onClick={() => merge.mutate()}
                disabled={!mergeSource || !mergeTarget}
              >
                Zusammenführen
              </button>
            </div>
          </div>
        </section>
      )}

      {!customers.data?.length ? (
        <div className="dn-panel p-8 text-center" role="status">
          <p className="text-lg font-medium">Keine Kunden</p>
          <p className="mt-1 text-sm text-[var(--dn-muted)]">Leerer Zustand – Suche anpassen oder anlegen.</p>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {customers.data.map((c) => (
            <article key={c.id} className="dn-panel flex flex-col p-4">
              <h2 className="text-lg font-semibold">{c.display_name}</h2>
              <p className="mt-1 text-sm text-[var(--dn-muted)]">
                {[c.email, c.phone, c.city].filter(Boolean).join(' · ') || 'Keine Kontaktdaten'}
              </p>
              <p className="mt-1 font-mono text-[10px] text-[var(--dn-muted)]">{c.id}</p>
              {c.is_example_data && (
                <p className="mt-2 text-xs text-[var(--dn-warn)]">Beispieldaten</p>
              )}
              <div className="mt-auto flex flex-wrap gap-2 pt-4">
                <button
                  type="button"
                  className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-hover)]"
                  onClick={() => void onExport(c)}
                >
                  DSGVO-Export
                </button>
                {canWrite && (
                  <button
                    type="button"
                    className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-hover)]"
                    onClick={() => archive.mutate(c.id)}
                  >
                    Archivieren
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
