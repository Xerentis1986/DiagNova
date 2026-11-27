import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Badge, Button, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function CommercePage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const isAdmin = user?.role === 'admin'

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
            <p className="text-sm text-[var(--dn-muted)]">
              Noch keine Konten. Admin kann B2B/B2C-Konten über die Commerce-API anlegen.
            </p>
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
