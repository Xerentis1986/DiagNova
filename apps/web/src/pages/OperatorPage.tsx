import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState, type FormEvent } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { Badge, Field, Input, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

const TABS = [
  { id: 'overview', label: 'Übersicht' },
  { id: 'customers', label: 'Kunden' },
  { id: 'subscriptions', label: 'Abos' },
  { id: 'mollie', label: 'Mollie' },
  { id: 'invoices', label: 'Rechnungen' },
  { id: 'licenses', label: 'Lizenzen' },
  { id: 'updates', label: 'Updates' },
  { id: 'adapters', label: 'Adapter' },
  { id: 'audit', label: 'Audit' },
  { id: 'mfa', label: 'MFA' },
  { id: 'settings', label: 'Einstellungen' },
] as const

type TabId = (typeof TABS)[number]['id']

export function OperatorPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [params, setParams] = useSearchParams()
  const tab = (params.get('tab') as TabId) || 'overview'
  const setTab = (id: TabId) => {
    const next = new URLSearchParams(params)
    if (id === 'overview') next.delete('tab')
    else next.set('tab', id)
    setParams(next, { replace: true })
  }

  const enabled = !!user?.is_platform_admin
  const consoleQ = useQuery({
    queryKey: ['operator-console'],
    queryFn: () => api.operatorConsole(),
    enabled,
  })
  const mollieCfgQ = useQuery({
    queryKey: ['mollie-config'],
    queryFn: () => api.mollieConfig(),
    enabled,
  })
  const mfaQ = useQuery({
    queryKey: ['operator-mfa'],
    queryFn: () => api.adminMfaStatus(),
    enabled,
  })
  const swQ = useQuery({
    queryKey: ['operator-sw-updates'],
    queryFn: () => api.softwareUpdatesDashboard(),
    enabled: enabled && (tab === 'updates' || tab === 'overview'),
  })

  const [mollieMsg, setMollieMsg] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [liveFlag, setLiveFlag] = useState(false)
  const [mfaCode, setMfaCode] = useState('')
  const [mfaMsg, setMfaMsg] = useState('')
  const [probeMsg, setProbeMsg] = useState('')

  const saveMollie = useMutation({
    mutationFn: () =>
      api.mollieConfigSave({
        api_key: apiKey || undefined,
        webhook_secret: webhookSecret || undefined,
        webhook_url: webhookUrl || undefined,
        live_charges_allowed: liveFlag,
      }),
    onSuccess: (r) => {
      setMollieMsg(String(r.message_de ?? 'Gespeichert'))
      setApiKey('')
      setWebhookSecret('')
      void qc.invalidateQueries({ queryKey: ['mollie-config'] })
      void qc.invalidateQueries({ queryKey: ['operator-console'] })
    },
    onError: (e: Error) => setMollieMsg(e.message),
  })

  const testMollie = useMutation({
    mutationFn: () => api.mollieConnectionTest(),
    onSuccess: (r) => setMollieMsg(String(r.message_de ?? JSON.stringify(r))),
    onError: (e: Error) => setMollieMsg(e.message),
  })

  const mfaSetup = useMutation({
    mutationFn: () => api.adminMfaSetup(),
    onSuccess: (r) => {
      setMfaMsg(
        `Secret angelegt. otpauth: ${String(r.otpauth_url ?? '').slice(0, 80)}… Code bestätigen.`,
      )
      void qc.invalidateQueries({ queryKey: ['operator-mfa'] })
    },
    onError: (e: Error) => setMfaMsg(e.message),
  })

  const mfaConfirm = useMutation({
    mutationFn: () => api.adminMfaConfirm(mfaCode),
    onSuccess: (r) => {
      setMfaMsg(String(r.message_de ?? 'MFA aktiv'))
      setMfaCode('')
      void qc.invalidateQueries({ queryKey: ['operator-mfa'] })
    },
    onError: (e: Error) => setMfaMsg(e.message),
  })

  const hwProbe = useMutation({
    mutationFn: () => api.adminHardwareProbe(),
    onSuccess: (r) => {
      setProbeMsg(String(r.message_de ?? JSON.stringify(r).slice(0, 400)))
    },
    onError: (e: Error) => setProbeMsg(e.message),
  })

  const d = consoleQ.data
  const cfg = mollieCfgQ.data

  const customers = useMemo(() => d?.customers ?? [], [d])
  const invoices = useMemo(() => d?.invoices ?? [], [d])
  const devices = useMemo(() => d?.devices ?? [], [d])
  const users = useMemo(() => d?.users ?? [], [d])

  if (!user?.is_platform_admin) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Betreiberkonsole"
        description="Nur Plattform-Admin. Kundenportal und Diagnose sind getrennt. Keine Live-Charges ohne Freigabe."
      />

      <nav className="flex flex-wrap gap-2" aria-label="Betreiber-Bereiche">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`rounded border px-3 py-1.5 text-sm ${
              tab === t.id
                ? 'border-[var(--dn-accent)] bg-[var(--dn-surface-2)]'
                : 'border-[var(--dn-border)] hover:bg-[var(--dn-surface-2)]'
            }`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'overview' && (
        <>
          <Panel>
            <div className="mb-3 flex flex-wrap gap-2">
              <Badge tone="warn">BETREIBER / ADMIN</Badge>
              <Badge>{String(d?.payment_mode ?? '…')}</Badge>
              <Badge tone={cfg?.configured ? undefined : 'warn'}>
                Mollie {cfg?.configured ? 'Key gesetzt' : 'Key fehlt'}
              </Badge>
            </div>
            <p className="mb-3 text-sm text-[var(--dn-muted)]">{String(d?.payment_note_de ?? '')}</p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Mandanten" value={d?.workshops_count} />
              <Stat label="Nutzer" value={d?.users_count} />
              <Stat label="Kunden B2B/B2C" value={
                d?.customers_b2b != null ? `${d.customers_b2b} / ${d.customers_b2c}` : undefined
              } />
              <Stat label="Aktive Abos" value={d?.active_subscriptions} />
              <Stat label="Offene Rechnungen" value={d?.invoices_open} />
              <Stat label="Geräte/Lizenzen" value={d?.devices_bound} />
              <Stat label="MRR (Cent)" value={d?.mrr_cents} />
              <Stat label="Einladungen offen" value={d?.invitations_pending} />
            </div>
          </Panel>
          <Panel>
            <SectionTitle>Rechtliche offene Punkte</SectionTitle>
            <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
              {(d?.legal_open_items_de ?? []).map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </Panel>
        </>
      )}

      {tab === 'customers' && (
        <Panel>
          <SectionTitle>Kunden (Billing Accounts B2B/B2C)</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--dn-border)] text-[var(--dn-muted)]">
                  <th className="py-2 pr-3">Name</th>
                  <th className="py-2 pr-3">Typ</th>
                  <th className="py-2 pr-3">E-Mail</th>
                  <th className="py-2 pr-3">Land</th>
                  <th className="py-2">USt-ID</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => (
                  <tr key={String(c.id)} className="border-b border-[var(--dn-border)]">
                    <td className="py-2 pr-3">{String(c.display_name ?? '—')}</td>
                    <td className="py-2 pr-3">
                      <Badge>{String(c.customer_type ?? '—')}</Badge>
                    </td>
                    <td className="py-2 pr-3">{String(c.email ?? '—')}</td>
                    <td className="py-2 pr-3">{String(c.country ?? '—')}</td>
                    <td className="py-2">{String(c.vat_id ?? '—')}</td>
                  </tr>
                ))}
                {customers.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-3 text-[var(--dn-muted)]">
                      Keine Billing-Accounts.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {tab === 'subscriptions' && (
        <Panel>
          <SectionTitle>Abos (plattformweit)</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {(d?.subscriptions ?? []).map((s) => (
              <li key={String(s.id)} className="flex flex-wrap items-center gap-2 py-2">
                <Badge>{String(s.status)}</Badge>
                <span>{String(s.plan_code)}</span>
                <span className="text-[var(--dn-muted)]">
                  Mandant {String(s.workshop_id).slice(0, 8)}…
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm">
            Werkstatt-Selbstservice:{' '}
            <Link className="text-[var(--dn-accent)] underline" to="/subscriptions">
              /subscriptions
            </Link>{' '}
            (Kundenportal)
          </p>
        </Panel>
      )}

      {tab === 'mollie' && (
        <Panel>
          <SectionTitle>Mollie – Key & Verbindungstest</SectionTitle>
          <div className="mb-3 flex flex-wrap gap-2">
            <Badge>{String(cfg?.provider ?? 'mollie')}</Badge>
            <Badge tone={cfg?.configured ? undefined : 'warn'}>
              {cfg?.configured
                ? `Key: ${String(cfg.api_key_masked)} (${String(cfg.api_key_source)})`
                : 'Key fehlt'}
            </Badge>
            <Badge>{cfg?.test_mode ? 'Testmodus' : cfg?.live_keys_present ? 'Live-Key' : '—'}</Badge>
          </div>
          <p className="mb-3 text-sm text-[var(--dn-muted)]">{String(cfg?.security_de ?? '')}</p>
          <form
            className="max-w-xl space-y-3"
            onSubmit={(e: FormEvent) => {
              e.preventDefault()
              saveMollie.mutate()
            }}
          >
            <Field label="API-Key (test_… / live_…)">
              <Input
                type="password"
                autoComplete="off"
                placeholder={cfg?.configured ? 'Neuen Key eingeben (leer = unverändert)' : 'test_…'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </Field>
            <Field label="Webhook-Secret (optional)">
              <Input
                type="password"
                autoComplete="off"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
              />
            </Field>
            <Field label="Webhook-URL">
              <Input
                type="url"
                placeholder="https://…/api/billing/webhooks/mollie"
                value={webhookUrl || String(cfg?.webhook_url ?? '')}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
            </Field>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={liveFlag}
                onChange={(e) => setLiveFlag(e.target.checked)}
              />
              Live-Charges erlauben (nur mit live_-Key; Standard aus)
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="submit"
                className="rounded border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-surface-2)]"
                disabled={saveMollie.isPending}
              >
                {saveMollie.isPending ? 'Speichere…' : 'Speichern (Secret-Store)'}
              </button>
              <button
                type="button"
                className="rounded border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-surface-2)]"
                disabled={testMollie.isPending}
                onClick={() => testMollie.mutate()}
              >
                {testMollie.isPending ? 'Teste…' : 'Verbindungstest'}
              </button>
            </div>
          </form>
          {mollieMsg ? <p className="mt-3 text-sm text-[var(--dn-muted)]">{mollieMsg}</p> : null}
        </Panel>
      )}

      {tab === 'invoices' && (
        <Panel>
          <SectionTitle>Rechnungen</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {invoices.map((i) => (
              <li key={String(i.id)} className="flex flex-wrap gap-2 py-2">
                <Badge>{String(i.status)}</Badge>
                <span>{String(i.number ?? i.id).slice(0, 16)}</span>
                <span className="text-[var(--dn-muted)]">
                  {i.gross_cents != null ? `${i.gross_cents} Cent` : '—'} · {String(i.currency ?? 'EUR')}
                </span>
                {i.is_example_data ? <Badge tone="warn">Beispiel</Badge> : null}
              </li>
            ))}
            {invoices.length === 0 && (
              <li className="py-2 text-[var(--dn-muted)]">Keine Rechnungen.</li>
            )}
          </ul>
        </Panel>
      )}

      {tab === 'licenses' && (
        <Panel>
          <SectionTitle>Lizenzen / Geräte</SectionTitle>
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {devices.map((dev) => (
              <li key={String(dev.id)} className="flex flex-wrap gap-2 py-2">
                <Badge tone={dev.active ? undefined : 'warn'}>
                  {dev.active ? 'aktiv' : 'revoked'}
                </Badge>
                <span>{String(dev.device_name)}</span>
                <span className="text-[var(--dn-muted)]">
                  {String(dev.platform)} · {String(dev.device_fingerprint)}
                </span>
              </li>
            ))}
            {devices.length === 0 && (
              <li className="py-2 text-[var(--dn-muted)]">Keine Gerätebindungen.</li>
            )}
          </ul>
        </Panel>
      )}

      {tab === 'updates' && (
        <Panel>
          <SectionTitle>Software- / Connector-Updates</SectionTitle>
          <p className="mb-2 text-sm text-[var(--dn-muted)]">
            Kanäle und Pakete – produktive Auto-Installs gesperrt ohne Signing.
          </p>
          <ul className="space-y-1 text-sm">
            {(swQ.data?.channels ?? []).map((ch) => (
              <li key={String((ch as { key?: string }).key ?? Math.random())}>
                <Badge>{String((ch as { key?: string }).key ?? 'channel')}</Badge>{' '}
                {String((ch as { name_de?: string; name?: string }).name_de
                  ?? (ch as { name?: string }).name
                  ?? '')}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm">
            Detail:{' '}
            <Link className="text-[var(--dn-accent)] underline" to="/software-updates">
              /software-updates
            </Link>
          </p>
        </Panel>
      )}

      {tab === 'adapters' && (
        <Panel>
          <SectionTitle>Adapter-Status & Proben</SectionTitle>
          <ul className="mb-4 list-disc space-y-1 pl-5 text-sm text-[var(--dn-muted)]">
            {(d?.adapter_test_paths_de ?? []).map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          <ul className="mb-4 divide-y divide-[var(--dn-border)] text-sm">
            {(d?.adapter_summary ?? []).map((a, idx) => (
              <li key={idx} className="py-2">
                <Badge>{String(a.kind ?? 'item')}</Badge> {String(a.code ?? a.name ?? '—')}
                {a.note_de ? (
                  <div className="text-xs text-[var(--dn-muted)]">{String(a.note_de)}</div>
                ) : null}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="rounded border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-surface-2)]"
            disabled={hwProbe.isPending}
            onClick={() => hwProbe.mutate()}
          >
            {hwProbe.isPending ? 'Probe…' : 'Hardware-Probe (Connector)'}
          </button>
          {probeMsg ? <p className="mt-2 text-sm text-[var(--dn-muted)]">{probeMsg}</p> : null}
          <p className="mt-3 text-xs text-[var(--dn-muted)]">
            CDP+ / OBD-DIAG / Vgate iCar Pro 2S – nur dokumentierte Pfade, keine erfundenen Protokolle,
            keine Live-Charges.
          </p>
        </Panel>
      )}

      {tab === 'audit' && (
        <Panel>
          <SectionTitle>Audit</SectionTitle>
          <ul className="max-h-96 overflow-y-auto divide-y divide-[var(--dn-border)] text-sm">
            {(d?.recent_audit ?? []).map((a) => (
              <li key={String(a.id)} className="py-2">
                <span className="font-medium">{String(a.action)}</span> · {String(a.resource)}
                <div className="text-xs text-[var(--dn-muted)]">
                  {String(a.detail ?? '')} · {String(a.created_at ?? '')}
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      )}

      {tab === 'mfa' && (
        <Panel>
          <SectionTitle>MFA (Betreiber)</SectionTitle>
          <div className="mb-3 flex flex-wrap gap-2">
            <Badge tone={mfaQ.data?.mfa_enabled ? undefined : 'warn'}>
              {mfaQ.data?.mfa_enabled ? 'MFA aktiv' : 'MFA nicht aktiv'}
            </Badge>
          </div>
          <p className="mb-3 text-sm text-[var(--dn-muted)]">{String(mfaQ.data?.message_de ?? '')}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-surface-2)]"
              onClick={() => mfaSetup.mutate()}
              disabled={mfaSetup.isPending}
            >
              MFA einrichten
            </button>
          </div>
          <form
            className="mt-4 flex max-w-sm flex-wrap items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              mfaConfirm.mutate()
            }}
          >
            <Field label="TOTP-Code">
              <Input
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                minLength={6}
                maxLength={8}
                required
              />
            </Field>
            <button
              type="submit"
              className="rounded border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-surface-2)]"
            >
              Bestätigen
            </button>
          </form>
          {mfaMsg ? <p className="mt-2 text-sm text-[var(--dn-muted)]">{mfaMsg}</p> : null}
        </Panel>
      )}

      {tab === 'settings' && (
        <Panel>
          <SectionTitle>Seiteneinstellungen (technisch AT)</SectionTitle>
          <ul className="space-y-1 text-sm text-[var(--dn-muted)]">
            <li>Lieferland: {String(d?.site_settings?.supplier_country ?? 'AT')}</li>
            <li>Währung: {String(d?.site_settings?.currency ?? 'EUR')}</li>
            <li>Steuerstatus: {String(d?.site_settings?.tax_review_status ?? 'draft_needs_review')}</li>
            <li>{String(d?.site_settings?.legal_note_de ?? '')}</li>
          </ul>
          <div className="mt-4">
            <SectionTitle>Nutzer (Plattform)</SectionTitle>
            <ul className="divide-y divide-[var(--dn-border)] text-sm">
              {users.map((u) => (
                <li key={String(u.id)} className="flex flex-wrap gap-2 py-2">
                  <span>{String(u.full_name)}</span>
                  <span className="text-[var(--dn-muted)]">{String(u.email)}</span>
                  <Badge>{String(u.role)}</Badge>
                  {u.is_platform_admin ? <Badge tone="accent">Platform</Badge> : null}
                </li>
              ))}
            </ul>
          </div>
        </Panel>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value?: number | string }) {
  return (
    <div className="rounded-md border border-[var(--dn-border)] px-3 py-2">
      <div className="text-xs text-[var(--dn-muted)]">{label}</div>
      <div className="text-xl font-semibold tabular-nums">{value ?? '—'}</div>
    </div>
  )
}

/** Alias für Alt-Route /admin */
export { OperatorPage as AdminPage }
