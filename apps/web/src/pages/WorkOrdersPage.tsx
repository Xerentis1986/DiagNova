import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api, type WorkOrder } from '../lib/api'
import { useAuth } from '../lib/auth'

const STATUSES: WorkOrder['status'][] = ['open', 'in_progress', 'done', 'cancelled']

export function WorkOrdersPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'technician'
  const qc = useQueryClient()
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [title, setTitle] = useState('')
  const [notes, setNotes] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [msg, setMsg] = useState<string | null>(null)

  const orders = useQuery({
    queryKey: ['work-orders', status, q],
    queryFn: () =>
      api.workOrders({
        status: status || undefined,
        q: q || undefined,
      }),
  })

  const customers = useQuery({
    queryKey: ['customers', 'for-orders'],
    queryFn: () => api.customers(),
    enabled: canWrite,
  })

  const refresh = () => void qc.invalidateQueries({ queryKey: ['work-orders'] })

  const create = useMutation({
    mutationFn: () =>
      api.createWorkOrder({
        title,
        notes: notes || null,
        customer_id: customerId || null,
        status: 'open',
      }),
    onSuccess: () => {
      setMsg('Auftrag angelegt')
      setTitle('')
      setNotes('')
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const setOrderStatus = useMutation({
    mutationFn: ({ id, next }: { id: string; next: WorkOrder['status'] }) =>
      api.updateWorkOrder(id, { status: next }),
    onSuccess: () => {
      setMsg('Status aktualisiert')
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  if (orders.isLoading) return <p className="text-[var(--dn-muted)]">Aufträge werden geladen…</p>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Werkstattaufträge</h1>
        <p className="text-sm text-[var(--dn-muted)]">
          Status, Notizen und Reparaturhinweise – mandantengebunden.
        </p>
      </div>

      {msg && (
        <p className="rounded-md border border-[var(--dn-border)] bg-[var(--dn-hover)] px-3 py-2 text-sm" role="status">
          {msg}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <input
          className="min-w-[10rem] flex-1 rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
          placeholder="Suche Titel…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          aria-label="Statusfilter"
        >
          <option value="">Alle Status</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {canWrite && (
        <section className="dn-panel space-y-3 p-4">
          <h2 className="text-lg font-medium">Neuer Auftrag</h2>
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault()
              create.mutate()
            }}
          >
            <input
              required
              placeholder="Titel *"
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm sm:col-span-2"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <select
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
            >
              <option value="">Kein Kunde</option>
              {(customers.data || []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.display_name}
                </option>
              ))}
            </select>
            <input
              placeholder="Notizen"
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <button
              type="submit"
              className="rounded-md bg-[var(--dn-accent)] px-3 py-2 text-sm text-white hover:opacity-90 sm:col-span-2 sm:w-fit"
            >
              Anlegen
            </button>
          </form>
        </section>
      )}

      {!orders.data?.length ? (
        <div className="dn-panel p-8 text-center" role="status">
          <p className="text-lg font-medium">Keine Aufträge</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {orders.data.map((o) => (
            <li key={o.id} className="dn-panel p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-lg font-semibold">{o.title}</h2>
                  <p className="mt-1 text-xs uppercase tracking-wide text-[var(--dn-accent)]">{o.status}</p>
                  {o.notes && <p className="mt-2 text-sm text-[var(--dn-muted)]">{o.notes}</p>}
                  {o.repair_summary && (
                    <p className="mt-1 text-sm">Reparatur: {o.repair_summary}</p>
                  )}
                  {o.is_example_data && (
                    <p className="mt-2 text-xs text-[var(--dn-warn)]">Beispieldaten</p>
                  )}
                </div>
                {canWrite && (
                  <select
                    className="rounded-md border border-[var(--dn-border)] bg-transparent px-2 py-1 text-sm"
                    value={o.status}
                    onChange={(e) =>
                      setOrderStatus.mutate({
                        id: o.id,
                        next: e.target.value as WorkOrder['status'],
                      })
                    }
                    aria-label={`Status für ${o.title}`}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
