import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Badge, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api, type SecurityFinding, type SecurityThreatNode } from '../lib/api'
import { useAuth } from '../lib/auth'

function toneForSeverity(sev: string): 'default' | 'ok' | 'warn' | 'danger' | 'accent' {
  if (sev === 'critical' || sev === 'high') return 'danger'
  if (sev === 'medium') return 'warn'
  if (sev === 'ok' || sev === 'mitigated' || sev === 'info') return 'ok'
  return 'default'
}

function toneForStatus(status: string): 'default' | 'ok' | 'warn' | 'danger' | 'accent' {
  if (status === 'mitigated') return 'ok'
  if (status === 'open') return 'danger'
  if (status === 'partial' || status === 'accepted' || status === 'documented') return 'warn'
  return 'default'
}

export function SecurityPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin' || !!user?.is_platform_admin

  const dash = useQuery({
    queryKey: ['security-dashboard'],
    queryFn: () => api.securityDashboard(),
    enabled: isAdmin,
  })
  const privacy = useQuery({
    queryKey: ['security-privacy'],
    queryFn: () => api.securityPrivacy(),
  })
  const backup = useQuery({
    queryKey: ['security-backup'],
    queryFn: () => api.securityBackup(),
    enabled: isAdmin,
  })
  const audit = useQuery({
    queryKey: ['security-audit'],
    queryFn: () => api.securityAudit(30),
    enabled: isAdmin,
  })

  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Sicherheit & Datenschutz"
          description="Übersicht der DSGVO-Prozesse (technisch). Threat Model nur für Administratoren."
        />
        <Panel>
          <Badge tone="warn">Eingeschränkte Ansicht</Badge>
          <p className="mt-3 text-sm text-[var(--dn-muted)]">{privacy.data?.disclaimer_de}</p>
          <ul className="mt-4 space-y-3">
            {(privacy.data?.processes ?? []).map((p) => (
              <li key={p.id}>
                <div className="font-medium">{p.title_de}</div>
                <p className="text-sm text-[var(--dn-muted)]">{p.description_de}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    )
  }

  const d = dash.data

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sicherheit & Datenschutz"
        description="Threat Model, Rate Limits, Audit-Redaction, DSGVO-Prozesse und Backup-Hinweise. Keine Rechtskonformität behauptet."
      />

      <Panel>
        <div className="mb-3 flex flex-wrap gap-2">
          <Badge tone="warn">PHASE 15</Badge>
          <Badge>{d?.version ?? '…'}</Badge>
          {d?.demo_mode && <Badge tone="accent">DEMO</Badge>}
          {d?.jwt_secret_insecure_default ? (
            <Badge tone="danger">JWT Default unsicher</Badge>
          ) : (
            <Badge tone="ok">JWT gesetzt</Badge>
          )}
          {d?.productive_auto_updates_blocked && <Badge tone="warn">Auto-Updates gesperrt</Badge>}
        </div>
        <p className="text-sm text-[var(--dn-muted)]">{d?.disclaimer_de}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Audit-Redaction" value={d?.audit_redaction ? 'Aktiv' : '—'} />
          <Stat label="Security-Header" value={d?.security_headers ? 'Aktiv' : '—'} />
          <Stat label="SSRF-Schutz Updates" value={d?.ssrf_protection_data_updates ? 'Aktiv' : '—'} />
          <Stat label="Connector Loopback" value={d?.connector_loopback_only ? 'Nur lokal' : '—'} />
          <Stat label="Login-Limit" value={d ? `${d.rate_limits.login_max}/${d.rate_limits.login_window_sec}s` : '—'} />
          <Stat label="Rollen" value={d?.rbac_roles?.join(', ') ?? '—'} />
        </div>
        <p className="mt-3 flex flex-wrap gap-3 text-sm">
          <Link to="/customers" className="text-[var(--dn-accent)] underline">
            Kunden / Export
          </Link>
          <Link to="/software-updates" className="text-[var(--dn-accent)] underline">
            Software-Updates
          </Link>
          {user?.is_platform_admin ? (
            <Link to="/operator" className="text-[var(--dn-accent)] underline">
              Betreiberkonsole
            </Link>
          ) : null}
        </p>
      </Panel>

      <Panel>
        <SectionTitle>Befunde</SectionTitle>
        <ul className="space-y-3">
          {(d?.findings ?? []).map((f: SecurityFinding) => (
            <li key={f.id} className="border-b border-[var(--dn-border)] pb-3 last:border-0">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-medium">{f.title_de}</span>
                <Badge tone={toneForSeverity(f.severity)}>{f.severity}</Badge>
                <Badge tone={toneForStatus(f.status)}>{f.status}</Badge>
              </div>
              <p className="text-sm text-[var(--dn-muted)]">{f.detail_de}</p>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel>
        <SectionTitle>Threat Model</SectionTitle>
        <div className="space-y-3">
          {(d?.threat_model ?? []).map((t: SecurityThreatNode) => (
            <div key={t.id} className="rounded-[var(--dn-radius)] border border-[var(--dn-border)] p-3">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="text-xs text-[var(--dn-muted)]">{t.id}</span>
                <Badge tone={toneForSeverity(t.severity)}>{t.severity}</Badge>
                <Badge tone={toneForStatus(t.status)}>{t.status}</Badge>
              </div>
              <div className="font-medium">
                {t.surface}: {t.threat}
              </div>
              <p className="mt-1 text-sm text-[var(--dn-muted)]">{t.mitigation_de}</p>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>DSGVO-Prozesse (technisch)</SectionTitle>
          <p className="mb-3 text-sm text-[var(--dn-muted)]">{privacy.data?.disclaimer_de}</p>
          <ul className="space-y-3">
            {(privacy.data?.processes ?? []).map((p) => (
              <li key={p.id}>
                <div className="font-medium">{p.title_de}</div>
                <p className="text-sm text-[var(--dn-muted)]">{p.description_de}</p>
                {p.api_hint && (
                  <code className="mt-1 block text-xs text-[var(--dn-accent)]">{p.api_hint}</code>
                )}
                <p className="mt-1 text-xs text-[var(--dn-muted)]">{p.legal_note_de}</p>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel>
          <SectionTitle>Backup / Monitoring</SectionTitle>
          <p className="mb-3 text-sm text-[var(--dn-muted)]">{backup.data?.disclaimer_de}</p>
          <p className="mb-1 text-sm font-medium">Backup</p>
          <ul className="mb-3 list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
            {(backup.data?.recommended_steps_de ?? []).map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
          <p className="mb-1 text-sm font-medium">Restore</p>
          <ul className="mb-3 list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
            {(backup.data?.restore_steps_de ?? []).map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
          <p className="mb-1 text-sm font-medium">Monitoring</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
            {(backup.data?.monitoring_hints_de ?? []).map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-[var(--dn-muted)]">{backup.data?.phase16_checklist_hint}</p>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Audit (Mandant, redaktiert)</SectionTitle>
        <p className="mb-3 text-sm text-[var(--dn-muted)]">{audit.data?.note_de}</p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--dn-border)] text-[var(--dn-muted)]">
                <th className="py-2 pr-3 font-medium">Zeit</th>
                <th className="py-2 pr-3 font-medium">Aktion</th>
                <th className="py-2 pr-3 font-medium">Ressource</th>
                <th className="py-2 font-medium">Detail</th>
              </tr>
            </thead>
            <tbody>
              {(audit.data?.items ?? []).map((row) => (
                <tr key={row.id} className="border-b border-[var(--dn-border)]/60">
                  <td className="py-2 pr-3 whitespace-nowrap text-[var(--dn-muted)]">
                    {row.created_at
                      ? new Date(row.created_at).toLocaleString('de-AT', { timeZone: 'Europe/Vienna' })
                      : '—'}
                  </td>
                  <td className="py-2 pr-3">{row.action}</td>
                  <td className="py-2 pr-3">{row.resource}</td>
                  <td className="py-2 text-[var(--dn-muted)]">{row.detail ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--dn-radius)] border border-[var(--dn-border)] px-3 py-2">
      <div className="text-xs text-[var(--dn-muted)]">{label}</div>
      <div className="mt-0.5 text-sm font-medium">{value}</div>
    </div>
  )
}
