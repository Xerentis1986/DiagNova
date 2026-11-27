import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Report, type ReportSummary } from '../lib/api'

export function ReportsPage() {
  const qc = useQueryClient()
  const [q, setQ] = useState('')
  const [vin, setVin] = useState('')
  const [includeArchived, setIncludeArchived] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)

  const listQuery = useQuery({
    queryKey: ['reports', q, vin, includeArchived],
    queryFn: () =>
      api.listReports({
        q: q || undefined,
        vin: vin || undefined,
        include_archived: includeArchived,
      }),
  })

  const previewQuery = useQuery({
    queryKey: ['report', selectedId],
    queryFn: () => api.getReport(selectedId!),
    enabled: !!selectedId,
  })

  const archiveMut = useMutation({
    mutationFn: (id: string) => api.archiveReport(id),
    onSuccess: () => {
      setMsg('Bericht archiviert')
      void qc.invalidateQueries({ queryKey: ['reports'] })
    },
  })

  const selected: Report | undefined = previewQuery.data
  const content = selected?.content as Record<string, unknown> | undefined
  const disclaimer = typeof content?.disclaimer_de === 'string' ? content.disclaimer_de : null
  const demo = Boolean(content?.demo_watermark)

  const rows: ReportSummary[] = listQuery.data ?? []
  const emptyHint = useMemo(() => {
    if (listQuery.isLoading) return null
    if (rows.length) return null
    return (
      <p className="text-sm text-[var(--dn-muted)]">
        Keine Berichte.{' '}
        <Link className="text-[var(--dn-accent)] underline" to="/diagnostics">
          Zur Diagnose
        </Link>
      </p>
    )
  }, [listQuery.isLoading, rows.length])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--dn-text)]">Berichte &amp; Archiv</h1>
        <p className="text-sm text-[var(--dn-muted)]">
          Unveränderliche Snapshots mit Datenquellenkennzeichnung. Demo/Simulation wird markiert.
          Keine automatisch erfundene Reparaturdiagnose.
        </p>
      </div>

      <section className="dn-panel space-y-3 p-4">
        <div className="flex flex-wrap gap-2">
          <input
            className="dn-input min-w-[12rem] flex-1"
            placeholder="Suche Titel / Berichtsnummer"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <input
            className="dn-input w-44"
            placeholder="VIN"
            value={vin}
            onChange={(e) => setVin(e.target.value.toUpperCase())}
          />
          <label className="flex items-center gap-2 text-sm text-[var(--dn-text)]">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(e) => setIncludeArchived(e.target.checked)}
            />
            Archiv anzeigen
          </label>
        </div>
        {msg && <p className="text-sm text-[var(--dn-ok)]">{msg}</p>}
        {listQuery.isLoading && <p className="text-sm text-[var(--dn-muted)]">Laden…</p>}
        {emptyHint}
        <ul className="divide-y divide-[var(--dn-border)]">
          {rows.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
              <button
                type="button"
                className="text-left"
                onClick={() => setSelectedId(r.id)}
              >
                <div className="font-medium text-[var(--dn-text)]">
                  {r.report_number ?? r.id.slice(0, 8)} · {r.title}
                </div>
                <div className="text-xs text-[var(--dn-muted)]">
                  {r.vehicle_label} · VIN {r.vin ?? '–'} · {r.dtc_count} DTCs · Quelle:{' '}
                  {r.data_source}
                  {r.demo_watermark ? ' · DEMO' : ''}
                  {r.archived_at ? ' · archiviert' : ''}
                </div>
              </button>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="dn-btn-secondary text-xs"
                  onClick={() => setSelectedId(r.id)}
                >
                  Vorschau
                </button>
                <button
                  type="button"
                  className="dn-btn-secondary text-xs"
                  onClick={() => void api.downloadExport(r.id, 'pdf')}
                >
                  PDF
                </button>
                <button
                  type="button"
                  className="dn-btn-secondary text-xs"
                  onClick={() => void api.downloadExport(r.id, 'csv')}
                >
                  CSV
                </button>
                {!r.archived_at && (
                  <button
                    type="button"
                    className="dn-btn-secondary text-xs"
                    onClick={() => archiveMut.mutate(r.id)}
                  >
                    Archivieren
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>

      {selected && (
        <section className="dn-panel space-y-3 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="text-lg font-medium text-[var(--dn-text)]">
                Vorschau {selected.report_number ?? selected.id.slice(0, 8)}
              </h2>
              <p className="text-xs text-[var(--dn-muted)]">
                Hash {selected.content_sha256?.slice(0, 16)}… · Version {selected.data_version} ·
                eingefroren {selected.frozen_at ? new Date(selected.frozen_at).toLocaleString('de-AT') : '–'}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                className="dn-btn-secondary text-xs"
                onClick={() => void api.downloadExport(selected.id, 'pdf')}
              >
                Download PDF
              </button>
              <button
                type="button"
                className="dn-btn-secondary text-xs"
                onClick={() => window.print()}
              >
                Drucken
              </button>
            </div>
          </div>
          {demo && (
            <p className="rounded border border-[color-mix(in_srgb,var(--dn-warn)_45%,var(--dn-border))] bg-[color-mix(in_srgb,var(--dn-warn)_12%,transparent)] px-3 py-2 text-sm text-[var(--dn-warn)]">
              DEMO / SIMULIERT – keine echte Fahrzeugdiagnose
            </p>
          )}
          {disclaimer && <p className="text-sm text-[var(--dn-text)]">{disclaimer}</p>}
          <pre className="max-h-[28rem] overflow-auto rounded bg-black/30 p-3 text-xs text-[var(--dn-text)]">
            {JSON.stringify(content, null, 2)}
          </pre>
        </section>
      )}
    </div>
  )
}
