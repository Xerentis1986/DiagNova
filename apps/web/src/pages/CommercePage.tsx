import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Badge, Button, Field, Input, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function CommercePage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const isAdmin = user?.role === 'admin'
  const [customerType, setCustomerType] = useState<'b2b' | 'b2c'>('b2b')
  const [contactName, setContactName] = useState('')
  const [billingEmail, setBillingEmail] = useState(user?.email ?? '')
  const [companyName, setCompanyName] = useState('')
  const [vatId, setVatId] = useState('')
  const [ackTerms, setAckTerms] = useState(false)

  const overviewQ = useQuery({ queryKey: ['commerce-overview'], queryFn: () => api.commerceOverview() })
  const accountsQ = useQuery({ queryKey: ['commerce-accounts'], queryFn: () => api.commerceAccounts() })
  const invoicesQ = useQuery({ queryKey: ['commerce-invoices'], queryFn: () => api.commerceInvoices() })

  const cancelMut = useMutation({
    mutationFn: (accountId: string) => api.commerceCancel(accountId, true),
    onSuccess: (r) => {
      setMsg(String(r.message_de || 'Kündigung vorgemerkt'))
      setErr(null)
      void qc.invalidateQueries({ queryKey: ['commerce-accounts'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  const createMut = useMutation({
    mutationFn: () =>
      api.commerceCreateAccount({
        customer_type: customerType,
        contact_name: contactName,
        billing_email: billingEmail,
        country: 'AT',
        company_name: customerType === 'b2b' ? companyName || undefined : undefined,
        vat_id: customerType === 'b2b' ? vatId || undefined : undefined,
        preferred_plan_code: 'pkw_trial',
        accept_terms: ackTerms,
        accept_privacy: ackTerms,
        ack_withdrawal: ackTerms,
      }),
    onSuccess: () => {
      setMsg('Billing-Konto angelegt (Pilot/Simulation).')
      setErr(null)
      setContactName('')
      void qc.invalidateQueries({ queryKey: ['commerce-accounts'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  async function downloadInvoice(id: string, number: string) {
    try {
      const token = localStorage.getItem('dn_token')
      const res = await fetch(api.commerceInvoiceDownloadUrl(id), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(await res.text())
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${number || id}.json`
      a.click()
      URL.revokeObjectURL(url)
      setMsg('Rechnung heruntergeladen (JSON-Simulation).')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Download fehlgeschlagen')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Konto & Abrechnung"
        description="B2B/B2C – Simulation. Kein echter Payment-Provider. Steuer draft_needs_review."
      />

      {overviewQ.data && (
        <Panel className="space-y-2 p-4">
          <div className="flex flex-wrap gap-2">
            <Badge>Phase {overviewQ.data.phase}</Badge>
            <Badge tone="warn">{overviewQ.data.tax_review_status}</Badge>
            <Badge tone={overviewQ.data.live_payments ? 'danger' : 'ok'}>
              {overviewQ.data.live_payments ? 'Live-Zahlung' : 'Simulation'}
            </Badge>
          </div>
          <p className="text-sm text-[var(--dn-muted)]">{overviewQ.data.message_de}</p>
          <p className="text-xs text-[var(--dn-muted)]">{overviewQ.data.payment_note_de}</p>
        </Panel>
      )}

      {msg && <p className="text-sm text-[var(--dn-ok)]">{msg}</p>}
      {err && <p className="text-sm text-[var(--dn-danger)]">{err}</p>}

      <section>
        <SectionTitle>Billing-Konten</SectionTitle>
        <div className="mt-3 space-y-3">
          {(accountsQ.data?.accounts || []).map((a) => (
            <Panel key={String(a.id)} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <p className="font-medium">
                  {String(a.customer_type).toUpperCase()} · {String(a.contact_name)}
                </p>
                <p className="text-sm text-[var(--dn-muted)]">
                  {String(a.billing_email)}
                  {a.company_name ? ` · ${String(a.company_name)}` : ''} · {String(a.country)}
                  {a.preferred_plan_code ? ` · Plan ${String(a.preferred_plan_code)}` : ''}
                </p>
              </div>
              {isAdmin && (
                <Button
                  variant="ghost"
                  disabled={cancelMut.isPending || !a.preferred_plan_code}
                  onClick={() => cancelMut.mutate(String(a.id))}
                >
                  Kündigen (Periodenende)
                </Button>
              )}
            </Panel>
          ))}
          {!accountsQ.data?.count && (
            <p className="mb-3 text-sm text-[var(--dn-muted)]">Noch keine Billing-Konten.</p>
          )}
          {isAdmin && (
            <Panel className="mt-4 max-w-xl space-y-3 p-4">
              <SectionTitle>Neues B2B/B2C-Konto</SectionTitle>
              <p className="text-xs text-[var(--dn-muted)]">
                Platzhalter AGB/Widerruf – Rechtsfreigabe offen. Keine Live-Zahlung.
              </p>
              <form
                className="space-y-3"
                onSubmit={(e: FormEvent) => {
                  e.preventDefault()
                  createMut.mutate()
                }}
              >
                <div className="flex gap-3 text-sm">
                  <label className="flex items-center gap-1">
                    <input
                      type="radio"
                      checked={customerType === 'b2b'}
                      onChange={() => setCustomerType('b2b')}
                    />
                    B2B
                  </label>
                  <label className="flex items-center gap-1">
                    <input
                      type="radio"
                      checked={customerType === 'b2c'}
                      onChange={() => setCustomerType('b2c')}
                    />
                    B2C
                  </label>
                </div>
                <Field label="Kontaktname">
                  <Input value={contactName} onChange={(e) => setContactName(e.target.value)} required />
                </Field>
                <Field label="Rechnungs-E-Mail">
                  <Input
                    type="email"
                    value={billingEmail}
                    onChange={(e) => setBillingEmail(e.target.value)}
                    required
                  />
                </Field>
                {customerType === 'b2b' && (
                  <>
                    <Field label="Firma">
                      <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
                    </Field>
                    <Field label="USt-ID">
                      <Input value={vatId} onChange={(e) => setVatId(e.target.value)} />
                    </Field>
                  </>
                )}
                <label className="flex items-start gap-2 text-xs text-[var(--dn-muted)]">
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={ackTerms}
                    onChange={(e) => setAckTerms(e.target.checked)}
                    required
                  />
                  Platzhalter AGB/Datenschutz/Widerruf zur Kenntnis genommen (keine Rechtsfreigabe).
                </label>
                <Button type="submit" disabled={createMut.isPending || !ackTerms}>
                  {createMut.isPending ? '…' : 'Konto anlegen'}
                </Button>
              </form>
            </Panel>
          )}
        </div>
      </section>

      <section>
        <SectionTitle>Rechnungen</SectionTitle>
        <div className="mt-3 space-y-3">
          {(invoicesQ.data?.invoices || []).map((inv) => (
            <Panel key={String(inv.id)} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <p className="font-medium">
                  {String(inv.number)}{' '}
                  <span className="text-xs uppercase text-[var(--dn-muted)]">{String(inv.doc_type)}</span>
                </p>
                <p className="text-sm text-[var(--dn-muted)]">
                  {String(inv.tax_scenario)} · Netto {String(inv.net_cents)} / USt {String(inv.vat_cents)} / Brutto{' '}
                  {String(inv.gross_cents)} Cent
                </p>
              </div>
              <Button variant="ghost" onClick={() => void downloadInvoice(String(inv.id), String(inv.number))}>
                Download JSON
              </Button>
            </Panel>
          ))}
          {!invoicesQ.data?.count && (
            <p className="text-sm text-[var(--dn-muted)]">Keine Rechnungen.</p>
          )}
        </div>
      </section>
    </div>
  )
}
