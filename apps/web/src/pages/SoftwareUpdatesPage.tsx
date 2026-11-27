import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, PageHeader, Panel, SectionTitle } from '../components/ui'
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

export function SoftwareUpdatesPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [msg, setMsg] = useState<string | null>(null)
  const isAdmin = user?.role === 'admin'

  const dash = useQuery({
    queryKey: ['software-updates-dashboard'],
    queryFn: () => api.softwareUpdatesDashboard(),
    enabled: isAdmin,
  })

  const refresh = () => qc.invalidateQueries({ queryKey: ['software-updates-dashboard'] })

  const ingest = useMutation({
    mutationFn: (body: { fixture_name: string; tamper?: boolean; channel_key?: string }) =>
      api.ingestSoftwarePackage(body),
    onSuccess: (p) => {
      setMsg(`Ingest ${p.component}@${p.version}: ${p.status}${p.error_de ? ` – ${p.error_de}` : ''}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const approve = useMutation({
    mutationFn: ({ id, fail }: { id: string; fail?: boolean }) =>
      api.approveSoftwarePackage(id, !!fail),
    onSuccess: (r) => {
      setMsg(`Installation: ${r.status}${r.error_de ? ` – ${r.error_de}` : ''}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const reject = useMutation({
    mutationFn: (id: string) => api.rejectSoftwarePackage(id, 'Admin abgelehnt'),
    onSuccess: (p) => {
      setMsg(`Ablehnung: ${p.status}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const rollback = useMutation({
    mutationFn: (component: string) => api.rollbackSoftwareComponent(component),
    onSuccess: (r) => {
      setMsg(`Rollback ${r.component}: ${r.status}`)
      refresh()
    },
    onError: (e: Error) => setMsg(e.message),
  })

  if (!isAdmin) {
    return (
      <div className="space-y-3">
        <PageHeader title="Software-Updates" description="Nur Administratoren." />
        <p className="text-sm text-[var(--dn-muted)]">
          Keine Berechtigung. Diagnosedaten-Updates:{' '}
          <Link className="text-[var(--dn-accent)] underline" to="/data-updates">
            /data-updates
          </Link>
        </p>
      </div>
    )
  }

  if (dash.isLoading) return <p className="text-[var(--dn-muted)]">Laden…</p>
  if (dash.isError) return <p className="text-[var(--dn-danger)]">{(dash.error as Error).message}</p>
  const d = dash.data!

  return (
    <div className="space-y-6">
      <PageHeader
        title="Software- & Connector-Updates"
        description="Versionierung, Signatur/Checksum, Staging, Admin-Freigabe, Healthcheck und Rollback. Getrennt von Diagnosedaten-Updates."
      />

      <Panel>
        <div className="mb-3 flex flex-wrap gap-2">
          <Badge tone="warn">SIMULATION</Badge>
          <Badge tone={d.productive_auto_updates_blocked ? 'danger' : 'ok'}>
            {d.productive_auto_updates_blocked
              ? 'Prod-Auto-Updates gesperrt (kein Zertifikat)'
              : 'Zertifikat konfiguriert'}
          </Badge>
          <Badge>Auto-Install: {d.auto_install_enabled ? 'an' : 'aus'}</Badge>
          <Badge tone={d.busy.allowed ? 'ok' : 'warn'}>
            {d.busy.allowed ? 'Update erlaubt' : 'Busy – Update gesperrt'}
          </Badge>
        </div>
        <p className="text-sm text-[var(--dn-muted)]">{d.disclaimer_de}</p>
        <p className="mt-2 text-sm">
          <Link className="text-[var(--dn-accent)] underline" to="/data-updates">
            Zu Diagnosedaten-Updates (Phase 07)
          </Link>
        </p>
      </Panel>

      {msg && (
        <p className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm" role="status">
          {msg}
        </p>
      )}

      {!d.busy.allowed && (
        <Panel>
          <SectionTitle>Busy-Gate</SectionTitle>
          <p className="mb-2 text-sm text-[var(--dn-danger)]">{d.busy.reason_de}</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
            {d.busy.blockers.map((b) => (
              <li key={b.ref}>
                <Badge>{b.kind}</Badge> {b.detail_de}
              </li>
            ))}
          </ul>
        </Panel>
      )}

      <Panel>
        <SectionTitle>Komponentenversionen</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--dn-border)] text-[var(--dn-muted)]">
                <th className="py-2 pr-3">Komponente</th>
                <th className="py-2 pr-3">Aktuell</th>
                <th className="py-2 pr-3">Vorher</th>
                <th className="py-2 pr-3">Health</th>
                <th className="py-2">Aktion</th>
              </tr>
            </thead>
            <tbody>
              {d.components.map((c) => (
                <tr key={c.key} className="border-b border-[var(--dn-border)]">
                  <td className="py-2 pr-3">{c.label_de}</td>
                  <td className="py-2 pr-3 font-mono">{c.current_version}</td>
                  <td className="py-2 pr-3 font-mono">{c.previous_version ?? '—'}</td>
                  <td className="py-2 pr-3">
                    <Badge tone={c.health_status === 'ok' ? 'ok' : 'danger'}>{c.health_status}</Badge>
                    {c.last_error_de ? (
                      <div className="text-xs text-[var(--dn-muted)]">{c.last_error_de}</div>
                    ) : null}
                  </td>
                  <td className="py-2">
                    <button
                      type="button"
                      className="dn-btn dn-btn--secondary text-xs"
                      disabled={!c.previous_version || rollback.isPending}
                      onClick={() => rollback.mutate(c.key)}
                    >
                      Rollback
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Demo-Ingest (Fixture)</SectionTitle>
          <p className="mb-3 text-sm text-[var(--dn-muted)]">
            Keine ungeprüften Auto-Installs – nach Ingest immer Admin-Freigabe.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="dn-btn dn-btn--primary text-sm"
              disabled={ingest.isPending}
              onClick={() =>
                ingest.mutate({ fixture_name: 'phase15_web_0.15.1.json', channel_key: 'stable-fixture' })
              }
            >
              Web 0.15.1
            </button>
            <button
              type="button"
              className="dn-btn dn-btn--secondary text-sm"
              disabled={ingest.isPending}
              onClick={() =>
                ingest.mutate({
                  fixture_name: 'phase15_connector_0.15.1.json',
                  channel_key: 'stable-fixture',
                })
              }
            >
              Connector 0.15.1
            </button>
            <button
              type="button"
              className="dn-btn dn-btn--secondary text-sm"
              disabled={ingest.isPending}
              onClick={() =>
                ingest.mutate({
                  fixture_name: 'phase15_web_0.16.0_incompat.json',
                  channel_key: 'stable-fixture',
                })
              }
            >
              Web 0.16 (inkompatibel)
            </button>
            <button
              type="button"
              className="dn-btn dn-btn--secondary text-sm"
              disabled={ingest.isPending}
              onClick={() =>
                ingest.mutate({
                  fixture_name: 'phase15_web_0.15.1.json',
                  channel_key: 'stable-fixture',
                  tamper: true,
                })
              }
            >
              Manipuliertes Paket
            </button>
            <button
              type="button"
              className="dn-btn dn-btn--secondary text-sm"
              disabled={ingest.isPending}
              onClick={() =>
                ingest.mutate({
                  fixture_name: 'phase15_web_0.15.1.json',
                  channel_key: 'production-blocked',
                })
              }
            >
              Production-Kanal (gesperrt)
            </button>
          </div>
        </Panel>

        <Panel>
          <SectionTitle>Kanäle</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {d.channels.map((c) => (
              <li key={c.key} className="py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{c.name}</span>
                  <Badge>{c.channel_type}</Badge>
                  <Badge tone={c.enabled ? 'ok' : 'default'}>{c.enabled ? 'an' : 'aus'}</Badge>
                  {c.require_signing_cert && <Badge tone="warn">Zertifikat nötig</Badge>}
                </div>
                <p className="text-xs text-[var(--dn-muted)]">{c.notes_de}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Wartende Freigaben</SectionTitle>
        {d.pending_packages.length === 0 ? (
          <p className="text-sm text-[var(--dn-muted)]">Keine Pakete in Freigabe.</p>
        ) : (
          <ul className="space-y-3">
            {d.pending_packages.map((p) => (
              <li key={p.id} className="border-b border-[var(--dn-border)] pb-3">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <span className="font-medium">
                      {p.component}@{p.version}
                    </span>{' '}
                    <Badge tone="warn">{p.status}</Badge>
                    <div className="text-xs text-[var(--dn-muted)]">
                      SHA-256: {p.content_sha256.slice(0, 16)}… · Sig:{' '}
                      {p.signature_ok == null ? '—' : p.signature_ok ? 'OK' : 'FAIL'}
                    </div>
                    <p className="mt-1 text-sm">{p.release_notes_de}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="dn-btn dn-btn--primary text-xs"
                      disabled={approve.isPending}
                      onClick={() => approve.mutate({ id: p.id })}
                    >
                      Freigeben & installieren
                    </button>
                    <button
                      type="button"
                      className="dn-btn dn-btn--secondary text-xs"
                      disabled={approve.isPending}
                      onClick={() => approve.mutate({ id: p.id, fail: true })}
                    >
                      Healthcheck-Fail (Rollback)
                    </button>
                    <button
                      type="button"
                      className="dn-btn dn-btn--secondary text-xs"
                      disabled={reject.isPending}
                      onClick={() => reject.mutate(p.id)}
                    >
                      Ablehnen
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Letzte Läufe / Fehler</SectionTitle>
          <ul className="max-h-64 overflow-y-auto divide-y divide-[var(--dn-border)] text-sm">
            {d.recent_runs.map((r) => (
              <li key={r.id} className="py-2">
                <Badge
                  tone={
                    r.status === 'succeeded'
                      ? 'ok'
                      : r.status === 'blocked_busy' || r.status === 'rolled_back'
                        ? 'warn'
                        : r.status === 'failed' || r.status === 'aborted'
                          ? 'danger'
                          : 'default'
                  }
                >
                  {r.status}
                </Badge>{' '}
                {r.action} {r.component} {r.from_version ?? '—'} → {r.to_version ?? '—'}
                {r.error_de ? <div className="text-xs text-[var(--dn-muted)]">{r.error_de}</div> : null}
                <div className="text-xs text-[var(--dn-muted)]">{fmt(r.started_at)}</div>
              </li>
            ))}
            {d.recent_runs.length === 0 && (
              <li className="py-2 text-[var(--dn-muted)]">Noch keine Läufe.</li>
            )}
          </ul>
        </Panel>

        <Panel>
          <SectionTitle>Ereignisse</SectionTitle>
          <ul className="max-h-64 overflow-y-auto divide-y divide-[var(--dn-border)] text-sm">
            {d.recent_events.map((e) => (
              <li key={e.id} className="py-2">
                <span className="font-medium">{e.event}</span>
                <div className="text-xs text-[var(--dn-muted)]">{e.detail_de}</div>
                <div className="text-xs text-[var(--dn-muted)]">{fmt(e.created_at)}</div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Kompatibilitätsmatrix</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {d.compatibility_rules.map((r) => (
              <li key={r.id} className="py-2">
                <span className="font-mono">
                  {r.component}@{r.version}
                </span>
                <div className="text-xs text-[var(--dn-muted)]">
                  braucht{' '}
                  {Object.entries(r.requires)
                    .map(([k, v]) => `${k}≥${v}`)
                    .join(', ')}
                </div>
                {r.notes_de ? <div className="text-xs text-[var(--dn-muted)]">{r.notes_de}</div> : null}
              </li>
            ))}
          </ul>
        </Panel>

        <Panel>
          <SectionTitle>DB-Migrationsplan / Backup</SectionTitle>
          {d.migration_plan.map((m) => (
            <div key={m.revision} className="mb-3 text-sm">
              <div className="font-medium">
                {m.from_revision} → {m.revision}{' '}
                {m.backup_required && <Badge tone="warn">Backup Pflicht</Badge>}
              </div>
              <p className="text-xs text-[var(--dn-muted)]">{m.notes_de}</p>
              <ol className="mt-1 list-decimal pl-5 text-xs text-[var(--dn-muted)]">
                {m.backup_steps_de.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  )
}
