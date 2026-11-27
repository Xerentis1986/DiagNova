import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

function fmt(ts: string | null | undefined) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString('de-AT', { timeZone: 'Europe/Vienna' })
  } catch {
    return ts
  }
}

export function DataUpdatesPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [msg, setMsg] = useState<string | null>(null)
  const isAdmin = user?.role === 'admin'

  const dash = useQuery({
    queryKey: ['data-updates-dashboard'],
    queryFn: () => api.dataUpdatesDashboard(),
    enabled: isAdmin,
  })

  const refresh = () => qc.invalidateQueries({ queryKey: ['data-updates-dashboard'] })

  const runChannel = useMutation({
    mutationFn: ({ key, force }: { key: string; force: boolean }) => api.runUpdateChannel(key, force),
    onSuccess: (r) => {
      setMsg(`Lauf ${r.status}${r.version_label ? ` · ${r.version_label}` : ''}${r.error_de ? ` – ${r.error_de}` : ''}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const patchChannel = useMutation({
    mutationFn: ({ key, enabled }: { key: string; enabled: boolean }) =>
      api.patchUpdateChannel(key, { enabled }),
    onSuccess: () => {
      setMsg('Kanal aktualisiert')
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const approve = useMutation({
    mutationFn: (id: string) => api.approveUpdateRun(id),
    onSuccess: (r) => {
      setMsg(`Freigabe: ${r.status}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const reject = useMutation({
    mutationFn: (id: string) => api.rejectUpdateRun(id, 'Admin abgelehnt'),
    onSuccess: (r) => {
      setMsg(`Ablehnung: ${r.status}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const rollback = useMutation({
    mutationFn: (id: string) => api.rollbackUpdateRun(id),
    onSuccess: (r) => {
      setMsg(`Rollback: ${r.status}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  if (!isAdmin) {
    return (
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold">Daten-Updates</h1>
        <p className="text-sm text-[var(--dn-muted)]">Nur Administratoren können Update-Kanäle verwalten.</p>
      </div>
    )
  }

  if (dash.isLoading) return <p className="text-[var(--dn-muted)]">Laden…</p>
  if (dash.isError) return <p className="text-[var(--dn-danger)]">{(dash.error as Error).message}</p>
  const d = dash.data!

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-[var(--dn-muted)]">Phase 07 · simuliert</p>
        <h1 className="text-2xl font-semibold text-[var(--dn-text)]">Diagnosedaten-Updates</h1>
        <p className="max-w-3xl text-sm text-[var(--dn-muted)]">{d.disclaimer_de}</p>
      </header>

      {msg && (
        <p className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm" role="status">
          {msg}
        </p>
      )}

      <section className="space-y-2 border-b border-[var(--dn-border)] pb-6">
        <h2 className="text-lg font-medium">Scheduler</h2>
        <p className="text-sm text-[var(--dn-text)]">
          Aktiv: {d.scheduler_enabled ? 'ja' : 'nein'} · Intervall-Standard: {d.default_interval_hours}h · Sperre:{' '}
          {d.lock_held ? `gehalten (${d.lock_by})` : 'frei'}
        </p>
        <p className="text-sm text-[var(--dn-muted)]">
          Letzter Lauf: {fmt(d.last_run_at)} · Nächster: {fmt(d.next_scheduled_at)}
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Kanäle</h2>
        <ul className="space-y-4">
          {d.channels.map((c) => (
            <li key={c.key} className="border-b border-[var(--dn-border)] pb-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div>
                  <div className="font-medium">{c.name}</div>
                  <div className="text-xs text-[var(--dn-muted)]">
                    {c.key} · {c.fetch_mode} · {c.content_kind} · Lizenz erwartet: {c.expected_license}
                  </div>
                  <div className="mt-1 text-xs text-[var(--dn-muted)]">
                    enabled={String(c.enabled)} · rights={String(c.rights_verified)} · auto=
                    {String(c.auto_activate_allowed)} · sig={String(c.require_signature)}
                  </div>
                  {c.notes_de && <p className="mt-1 max-w-2xl text-sm text-[var(--dn-muted)]">{c.notes_de}</p>}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-hover)]"
                    onClick={() => patchChannel.mutate({ key: c.key, enabled: !c.enabled })}
                    disabled={c.fetch_mode === 'https' && !c.rights_verified && !c.enabled}
                  >
                    {c.enabled ? 'Deaktivieren' : 'Aktivieren'}
                  </button>
                  <button
                    type="button"
                    className="rounded-md bg-[var(--dn-accent)] px-3 py-1.5 text-sm font-medium text-white"
                    onClick={() => runChannel.mutate({ key: c.key, force: true })}
                  >
                    Manuell starten
                  </button>
                </div>
              </div>
              <p className="mt-1 text-xs text-[var(--dn-muted)]">
                Letzte Version: {c.last_version || '—'} · Hash: {c.last_content_hash?.slice(0, 12) || '—'} · nächster
                Lauf: {fmt(c.next_run_at)}
              </p>
            </li>
          ))}
        </ul>
      </section>

      {d.pending_approvals.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium">Manuelle Freigabe</h2>
          <ul className="space-y-3">
            {d.pending_approvals.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <span>
                  {r.channel_key} · {r.version_label || r.id.slice(0, 8)}
                  {r.license_changed ? ' · Lizenzänderung' : ''}
                </span>
                <span className="flex gap-2">
                  <button
                    type="button"
                    className="rounded-md bg-[var(--dn-accent)] px-3 py-1.5 text-white"
                    onClick={() => approve.mutate(r.id)}
                  >
                    Freigeben
                  </button>
                  <button
                    type="button"
                    className="rounded-md border border-[var(--dn-border)] px-3 py-1.5"
                    onClick={() => reject.mutate(r.id)}
                  >
                    Ablehnen
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Letzte Läufe</h2>
        <ul className="space-y-2 text-sm">
          {d.recent_runs.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--dn-border)] pb-2">
              <span>
                {fmt(r.started_at)} · {r.channel_key} · <strong>{r.status}</strong>
                {r.error_de ? ` – ${r.error_de}` : ''}
              </span>
              {r.status === 'published' && (
                <button
                  type="button"
                  className="rounded-md border border-[var(--dn-border)] px-2 py-1 text-xs"
                  onClick={() => rollback.mutate(r.id)}
                >
                  Rollback
                </button>
              )}
            </li>
          ))}
          {d.recent_runs.length === 0 && <li className="text-[var(--dn-muted)]">Noch keine Läufe.</li>}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Änderungsprotokoll</h2>
        <ul className="space-y-1 text-sm text-[var(--dn-muted)]">
          {d.recent_changelog.map((e) => (
            <li key={e.id}>
              {fmt(e.created_at)} · {e.channel_key} · {e.event}: {e.detail_de}
            </li>
          ))}
          {d.recent_changelog.length === 0 && <li>Leer.</li>}
        </ul>
      </section>
    </div>
  )
}
