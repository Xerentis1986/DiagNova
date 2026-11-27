import { useQuery } from '@tanstack/react-query'
import { Link, Navigate } from 'react-router-dom'
import { Badge, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function AdminPage() {
  const { user } = useAuth()
  const dashQ = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => api.adminDashboard(),
    enabled: !!user?.is_platform_admin,
  })
  const usersQ = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.adminUsers(),
    enabled: !!user?.is_platform_admin,
  })
  const supportQ = useQuery({
    queryKey: ['admin-support'],
    queryFn: () => api.adminSupport(),
    enabled: !!user?.is_platform_admin,
  })

  if (!user?.is_platform_admin) {
    return <Navigate to="/subscriptions" replace />
  }

  const d = dashQ.data

  return (
    <div className="space-y-6">
      <PageHeader
        title="Administration"
        description="Nutzer, Abos, Datenversionen, Software-Updates, Adapter, Support und Audit. Zahlung nur Stub."
      />

      <Panel>
        <div className="mb-3 flex flex-wrap gap-2">
          <Badge tone="warn">SIMULATION / STUB</Badge>
          <Badge>{d?.payment_mode ?? '…'}</Badge>
        </div>
        <p className="mb-3 text-sm text-[var(--dn-muted)]">{d?.payment_note_de}</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Mandanten" value={d?.workshops_count} />
          <Stat label="Nutzer" value={d?.users_count} />
          <Stat label="Aktive Abos" value={d?.active_subscriptions} />
          <Stat label="Past due" value={d?.past_due_subscriptions} />
          <Stat label="Gekündigt/abgelaufen" value={d?.canceled_subscriptions} />
          <Stat label="Offene Einladungen" value={d?.invitations_pending} />
          <Stat label="Geräte" value={d?.devices_bound} />
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Rechtliche offene Punkte</SectionTitle>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
            {(d?.legal_open_items_de ?? []).map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          <p className="mt-3 flex flex-wrap gap-3 text-sm">
            <Link to="/subscriptions" className="text-[var(--dn-accent)] underline">
              Zur Abo-Verwaltung
            </Link>
            <Link to="/software-updates" className="text-[var(--dn-accent)] underline">
              Software-Updates
            </Link>
          </p>
        </Panel>

        <Panel>
          <SectionTitle>Support</SectionTitle>
          <p className="mb-2 text-sm">
            Offene Einladungen: {supportQ.data?.pending_invitations ?? '—'}
          </p>
          <p className="mb-2 text-sm">
            Laufende kritische Ops: {supportQ.data?.running_critical_ops?.length ?? 0}
          </p>
          <ul className="space-y-1 text-sm">
            {(supportQ.data?.past_due ?? []).map((s) => (
              <li key={s.id}>
                <Badge tone="warn">past_due</Badge> {s.plan_code} · {s.workshop_id.slice(0, 8)}…
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Nutzer</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--dn-border)] text-[var(--dn-muted)]">
                <th className="py-2 pr-3">Name</th>
                <th className="py-2 pr-3">E-Mail</th>
                <th className="py-2 pr-3">Rolle</th>
                <th className="py-2 pr-3">Mandant</th>
                <th className="py-2">Flags</th>
              </tr>
            </thead>
            <tbody>
              {(usersQ.data ?? []).map((u) => (
                <tr key={u.id} className="border-b border-[var(--dn-border)]">
                  <td className="py-2 pr-3">{u.full_name}</td>
                  <td className="py-2 pr-3">{u.email}</td>
                  <td className="py-2 pr-3">
                    <Badge>{u.role}</Badge>
                  </td>
                  <td className="py-2 pr-3">{u.workshop_name ?? '—'}</td>
                  <td className="py-2">
                    {u.is_platform_admin && <Badge tone="accent">Platform</Badge>}{' '}
                    {!u.is_active && <Badge tone="danger">inaktiv</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Datenversionen</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {(d?.data_versions ?? []).map((v) => (
              <li key={v.id} className="flex justify-between gap-2 py-2">
                <span>{v.label}</span>
                <Badge>{v.status}</Badge>
              </li>
            ))}
            {(d?.data_versions ?? []).length === 0 && (
              <li className="py-2 text-[var(--dn-muted)]">Keine Versionen.</li>
            )}
          </ul>
        </Panel>

        <Panel>
          <SectionTitle>Adapter / Kanäle</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {(d?.adapter_summary ?? []).map((a, idx) => (
              <li key={idx} className="py-2">
                <Badge>{String(a.kind ?? 'item')}</Badge>{' '}
                {String(a.code ?? a.name ?? '—')}
                {a.note_de ? (
                  <div className="text-xs text-[var(--dn-muted)]">{String(a.note_de)}</div>
                ) : null}
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Audit (aktuell)</SectionTitle>
        <ul className="max-h-64 overflow-y-auto divide-y divide-[var(--dn-border)] text-sm">
          {(d?.recent_audit ?? []).map((a) => (
            <li key={String(a.id)} className="py-2">
              <span className="font-medium">{String(a.action)}</span> · {String(a.resource)}
              <div className="text-xs text-[var(--dn-muted)]">{String(a.created_at ?? '')}</div>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel>
        <SectionTitle>Payment-Stub Webhooks</SectionTitle>
        <ul className="divide-y divide-[var(--dn-border)] text-sm">
          {(d?.recent_webhooks ?? []).map((h) => (
            <li key={String(h.id)} className="flex flex-wrap items-center gap-2 py-2">
              <Badge>{String(h.event_type)}</Badge>
              <Badge tone={h.status === 'processed' ? 'ok' : h.status === 'duplicate' ? 'warn' : 'default'}>
                {String(h.status)}
              </Badge>
              <span className="text-[var(--dn-muted)]">{String(h.event_id)}</span>
            </li>
          ))}
          {(d?.recent_webhooks ?? []).length === 0 && (
            <li className="py-2 text-[var(--dn-muted)]">Noch keine Stub-Webhooks.</li>
          )}
        </ul>
      </Panel>
    </div>
  )
}

function Stat({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded-md border border-[var(--dn-border)] px-3 py-2">
      <div className="text-xs text-[var(--dn-muted)]">{label}</div>
      <div className="text-xl font-semibold tabular-nums">{value ?? '—'}</div>
    </div>
  )
}
