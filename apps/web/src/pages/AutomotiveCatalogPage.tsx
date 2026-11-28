import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Badge, Button, Field, Input, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function AutomotiveCatalogPage() {
  const { user } = useAuth()
  const [q, setQ] = useState('')
  const [probeMsg, setProbeMsg] = useState('')
  const summaryQ = useQuery({
    queryKey: ['auto-catalog-summary'],
    queryFn: () => api.automotiveCatalogSummary(),
  })
  const sourcesQ = useQuery({
    queryKey: ['auto-catalog-sources', q],
    queryFn: () => api.automotiveCatalogSources({ q: q || undefined, limit: 40 }),
  })
  const probe = useMutation({
    mutationFn: () => api.automotiveCatalogProbe(true),
    onSuccess: (r) => setProbeMsg(String(r.message_de ?? JSON.stringify(r).slice(0, 300))),
    onError: (e: Error) => setProbeMsg(e.message),
  })
  const preview = useMutation({
    mutationFn: () => api.automotiveCatalogImportPreview(),
    onSuccess: (r) =>
      setProbeMsg(
        `Import-Preview: ${String(r.status)} · can_apply=${String(r.can_apply)} · ${String(r.message_de ?? '')}`,
      ),
    onError: (e: Error) => setProbeMsg(e.message),
  })

  const s = summaryQ.data

  return (
    <div className="space-y-6">
      <PageHeader
        title="Automotive-Quellenkatalog"
        description="447 Einstiegspunkte. Open-Data-Pfade (OBDex Sample, SAE-PIDs). OEM/Flash/Schreiben gesperrt."
      />

      <Panel>
        <div className="mb-3 flex flex-wrap gap-2">
          <Badge>{String(s?.source_count ?? '…')} Quellen</Badge>
          <Badge>{String(s?.categories ?? '…')} Kategorien</Badge>
          <Badge tone="warn">Schreibdiagnose/Flash gesperrt</Badge>
          <Badge tone="warn">Kein kommerzielles Voll-GO</Badge>
        </div>
        <p className="text-sm text-[var(--dn-muted)]">{String(s?.note ?? '')}</p>
        <p className="mt-2 text-sm text-[var(--dn-muted)]">{String(s?.go_note_de ?? '')}</p>
        {(s?.coverage as { message_de?: string; blocked?: string[] } | undefined)?.message_de ? (
          <p className="mt-2 text-xs text-[var(--dn-muted)]">
            {String((s?.coverage as { message_de?: string }).message_de)}
          </p>
        ) : null}
      </Panel>

      <Panel>
        <SectionTitle>Prioritätsprobe / Import (Admin)</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {user?.is_platform_admin && (
            <Button
              variant="secondary"
              disabled={probe.isPending}
              onClick={() => probe.mutate()}
            >
              {probe.isPending ? 'Probe…' : 'Quellen-Probe'}
            </Button>
          )}
          {(user?.role === 'admin' || user?.is_platform_admin) && (
            <Button
              variant="secondary"
              disabled={preview.isPending}
              onClick={() => preview.mutate()}
            >
              {preview.isPending ? '…' : 'OBDex-Sample Import-Preview'}
            </Button>
          )}
        </div>
        {probeMsg ? <p className="mt-3 text-sm text-[var(--dn-muted)]">{probeMsg}</p> : null}
      </Panel>

      <Panel>
        <SectionTitle>Quellen durchsuchen</SectionTitle>
        <form
          className="mb-3 flex max-w-md gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            void sourcesQ.refetch()
          }}
        >
          <Field label="Suche">
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="OBDex, DTC, EV…" />
          </Field>
        </form>
        <p className="mb-2 text-xs text-[var(--dn-muted)]">
          Treffer: {sourcesQ.data?.total ?? '—'} (Anzeige max. {sourcesQ.data?.limit ?? 40})
        </p>
        <ul className="max-h-96 divide-y divide-[var(--dn-border)] overflow-y-auto text-sm">
          {(sourcesQ.data?.items ?? []).map((it) => (
            <li key={String(it.catalog_id ?? it.url)} className="py-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{String(it.catalog_id ?? '—')}</Badge>
                <Badge>{String(it.category ?? '')}</Badge>
                <span className="font-medium">{String(it.name)}</span>
              </div>
              <div className="text-xs text-[var(--dn-muted)]">
                {String(it.type ?? '')} · {String(it.scope ?? '')} · {String(it.url ?? '')}
              </div>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
