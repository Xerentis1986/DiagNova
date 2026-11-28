import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api, type SubscriptionPlan } from '../lib/api'
import { useAuth } from '../lib/auth'

function statusTone(status: string): 'ok' | 'warn' | 'danger' | 'default' | 'accent' {
  if (status === 'active' || status === 'trialing') return 'ok'
  if (status === 'past_due') return 'warn'
  if (status === 'canceled' || status === 'expired' || status === 'unpaid') return 'danger'
  return 'default'
}

function formatPrice(plan: SubscriptionPlan) {
  if (plan.price_cents_demo == null) return '—'
  if (plan.price_cents_demo === 0) return '0 € (Demo)'
  return `${(plan.price_cents_demo / 100).toFixed(2)} € / Demo`
}

export function SubscriptionsPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [inviteEmail, setInviteEmail] = useState('')
  const [deviceName, setDeviceName] = useState('Werkstatt-PC Demo')
  const [deviceFp, setDeviceFp] = useState('demo-fp-windows-001')
  const isAdmin = user?.role === 'admin'

  const subQ = useQuery({ queryKey: ['subscription-me'], queryFn: () => api.mySubscription() })
  const plansQ = useQuery({ queryKey: ['subscription-plans'], queryFn: () => api.subscriptionPlans() })
  const devicesQ = useQuery({ queryKey: ['devices'], queryFn: () => api.listDevices() })
  const invQ = useQuery({
    queryKey: ['invitations'],
    queryFn: () => api.listInvitations(),
    enabled: isAdmin,
  })
  const stubQ = useQuery({ queryKey: ['billing-stub'], queryFn: () => api.billingStubInfo() })

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['subscription-me'] })
    void qc.invalidateQueries({ queryKey: ['devices'] })
    void qc.invalidateQueries({ queryKey: ['invitations'] })
  }

  const activateMut = useMutation({
    mutationFn: (code: string) => api.activateStubPlan(code, true),
    onSuccess: (s) => {
      setMsg(s.message_de)
      setErr(null)
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const trialMut = useMutation({
    mutationFn: () => api.startTrial('pkw_trial'),
    onSuccess: (s) => {
      setMsg(s.message_de)
      setErr(null)
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const cancelMut = useMutation({
    mutationFn: () => api.cancelSubscription(true, 'Demo-Kündigung UI'),
    onSuccess: (s) => {
      setMsg(s.message_de)
      setErr(null)
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const deviceMut = useMutation({
    mutationFn: () =>
      api.bindDevice({
        device_name: deviceName,
        device_fingerprint: deviceFp,
        platform: 'windows',
      }),
    onSuccess: () => {
      setMsg('Gerät gebunden (Demo).')
      setErr(null)
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const inviteMut = useMutation({
    mutationFn: () => api.createInvitation(inviteEmail, 'technician'),
    onSuccess: (inv) => {
      setMsg(`Einladung erstellt${inv.token ? ` – Token: ${inv.token}` : ''}`)
      setErr(null)
      setInviteEmail('')
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const failPayMut = useMutation({
    mutationFn: async () => {
      const sub = subQ.data
      if (!sub?.id) throw new Error('Kein Abo')
      const body = {
        event_id: `evt_fail_${Date.now()}`,
        event_type: 'invoice.payment_failed',
        subscription_id: sub.id,
        workshop_id: sub.workshop_id,
        meta: { source: 'ui_demo' },
      }
      const signed = await api.signStubWebhook(body)
      return api.postStubWebhook(signed.body_raw, signed.header)
    },
    onSuccess: (r) => {
      setMsg(r.message_de)
      setErr(null)
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const criticalMut = useMutation({
    mutationFn: async () => {
      const op = await api.startCriticalOp('coding_sim', 'demo-resource', 'Demo kritische Op')
      return op
    },
    onSuccess: (op) => {
      setMsg(`Kritische Op gestartet: ${op.id} (${op.status})`)
      setErr(null)
      invalidate()
    },
    onError: (e: Error) => setErr(e.message),
  })

  const sub = subQ.data

  return (
    <div className="space-y-6">
      <PageHeader
        title="Abonnements & Lizenzen"
        description="Tarife, Entitlements und Gerätebindung. Zahlung nur Stub/Simulation – keine echten Abbuchungen."
      />

      <Panel>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Badge tone="warn">SIMULATION / STUB</Badge>
          <Badge>{stubQ.data?.provider ?? 'mock'}</Badge>
          <span className="text-sm text-[var(--dn-muted)]">
            {stubQ.data?.message_de ?? 'Kein echter Payment-Provider.'}
          </span>
        </div>
        {msg && <p className="mb-2 text-sm text-[var(--dn-accent)]">{msg}</p>}
        {err && <p className="mb-2 text-sm text-[var(--dn-danger)]">{err}</p>}
        {sub && (
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[var(--dn-muted)]">Status</dt>
              <dd>
                <Badge tone={statusTone(sub.status)}>{sub.status}</Badge>
              </dd>
            </div>
            <div>
              <dt className="text-[var(--dn-muted)]">Tarif</dt>
              <dd>
                {sub.plan_name_de ?? sub.plan_code}{' '}
                {sub.license_active ? (
                  <Badge tone="ok">Lizenz aktiv</Badge>
                ) : (
                  <Badge tone="danger">inaktiv</Badge>
                )}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-[var(--dn-muted)]">Hinweis</dt>
              <dd>{sub.message_de}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-[var(--dn-muted)]">Entitlements</dt>
              <dd className="flex flex-wrap gap-1">
                {sub.entitlements.map((e) => (
                  <Badge key={e}>{e}</Badge>
                ))}
              </dd>
            </div>
          </dl>
        )}
        {isAdmin && (
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              variant="secondary"
              disabled={trialMut.isPending}
              onClick={() => trialMut.mutate()}
            >
              Testzeitraum starten
            </Button>
            <Button
              variant="secondary"
              disabled={cancelMut.isPending}
              onClick={() => cancelMut.mutate()}
            >
              Zum Periodenende kündigen
            </Button>
            <Button
              variant="secondary"
              disabled={failPayMut.isPending}
              onClick={() => failPayMut.mutate()}
            >
              Stub: Zahlungsausfall
            </Button>
            <Button
              variant="secondary"
              disabled={criticalMut.isPending}
              onClick={() => criticalMut.mutate()}
            >
              Kritische Op starten
            </Button>
          </div>
        )}
      </Panel>

      <Panel>
        <SectionTitle>Tarife (Demo-Preise)</SectionTitle>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(plansQ.data ?? []).map((p) => (
            <div
              key={p.code}
              className="rounded-md border border-[var(--dn-border)] p-3"
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <strong>{p.name_de}</strong>
                <Badge tone={p.release_status === 'available' ? 'accent' : 'default'}>
                  {p.release_status}
                </Badge>
              </div>
              <p className="mb-2 text-sm text-[var(--dn-muted)]">{p.description_de}</p>
              <p className="mb-2 text-sm">{formatPrice(p)}</p>
              {isAdmin && p.release_status === 'available' && p.trial_days === 0 && (
                <Button
                  size="sm"
                  disabled={activateMut.isPending}
                  onClick={() => activateMut.mutate(p.code)}
                >
                  Stub-Aktivierung
                </Button>
              )}
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Gerätebindung</SectionTitle>
          {isAdmin && (
            <div className="mb-3 flex flex-wrap gap-2">
              <input
                className="dn-input"
                value={deviceName}
                onChange={(e) => setDeviceName(e.target.value)}
                placeholder="Gerätename"
              />
              <input
                className="dn-input"
                value={deviceFp}
                onChange={(e) => setDeviceFp(e.target.value)}
                placeholder="Fingerprint"
              />
              <Button disabled={deviceMut.isPending} onClick={() => deviceMut.mutate()}>
                Binden
              </Button>
            </div>
          )}
          <ul className="divide-y divide-[var(--dn-border)] text-sm">
            {(devicesQ.data ?? []).map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-2 py-2">
                <span>
                  {d.device_name} · {d.platform}
                  {d.revoked_at && <Badge tone="danger">widerrufen</Badge>}
                </span>
                {isAdmin && !d.revoked_at && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      api.revokeDevice(d.id).then(() => {
                        invalidate()
                        setMsg('Gerät freigegeben')
                      })
                    }
                  >
                    Freigeben
                  </Button>
                )}
              </li>
            ))}
            {(devicesQ.data ?? []).length === 0 && (
              <li className="py-2 text-[var(--dn-muted)]">Keine Geräte gebunden.</li>
            )}
          </ul>
        </Panel>

        <Panel>
          <SectionTitle>Einladungen</SectionTitle>
          {isAdmin ? (
            <>
              <div className="mb-3 flex flex-wrap gap-2">
                <input
                  className="dn-input"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="kollege@example.com"
                />
                <Button disabled={!inviteEmail || inviteMut.isPending} onClick={() => inviteMut.mutate()}>
                  Einladen
                </Button>
              </div>
              <ul className="divide-y divide-[var(--dn-border)] text-sm">
                {(invQ.data ?? []).map((i) => (
                  <li key={i.id} className="py-2">
                    {i.email} · <Badge>{i.role}</Badge> · <Badge tone="default">{i.status}</Badge>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-[var(--dn-muted)]">Nur Werkstatt-Admin.</p>
          )}
          {user?.is_platform_admin && (
            <p className="mt-3 text-sm">
              <Link className="text-[var(--dn-accent)] underline" to="/admin">
                Zur Plattform-Administration
              </Link>
            </p>
          )}
        </Panel>
      </div>
    </div>
  )
}
