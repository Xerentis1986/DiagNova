import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'

const SAMPLE_IMPORT = {
  schema_version: 'diagnova.diagnostic-import.v1',
  dataset_version_label: 'ui-demo-import',
  source_key: 'diagnova-structural',
  manufacturers: [{ slug: 'demo-mfr', name: 'Demo Hersteller', data_scope: 'generic' }],
  models: [],
  variants: [],
  ecus: [],
  dtcs: [{ code: 'P0500', description_status: 'unknown', data_scope: 'generic' }],
  pids: [],
  units: [],
  service_procedures: [],
}

export function DiagnosticDataPage() {
  const [dtcCode, setDtcCode] = useState('P0301')
  const [lookupCode, setLookupCode] = useState('P0301')
  const [batchId, setBatchId] = useState<string | null>(null)
  const [importMsg, setImportMsg] = useState<string | null>(null)

  const sources = useQuery({ queryKey: ['diag-sources'], queryFn: () => api.diagnosticSources() })
  const coverage = useQuery({ queryKey: ['diag-coverage'], queryFn: () => api.diagnosticCoverage() })
  const pids = useQuery({ queryKey: ['diag-pids'], queryFn: () => api.diagnosticPids() })
  const ecus = useQuery({ queryKey: ['diag-ecus'], queryFn: () => api.diagnosticEcus() })
  const dtc = useQuery({
    queryKey: ['diag-dtc', lookupCode],
    queryFn: () => api.lookupDtc(lookupCode),
    enabled: lookupCode.length >= 5,
  })

  const preview = useMutation({
    mutationFn: () => api.importPreview(SAMPLE_IMPORT),
    onSuccess: (data) => {
      setBatchId(data.batch_id)
      setImportMsg(data.message_de)
    },
    onError: (e: Error) => setImportMsg(e.message),
  })

  const apply = useMutation({
    mutationFn: () => api.importApply(batchId!),
    onSuccess: (data) => setImportMsg(`Apply: ${data.status} (${data.applied_count} Datensätze)`),
    onError: (e: Error) => setImportMsg(e.message),
  })

  const rollback = useMutation({
    mutationFn: () => api.importRollback(batchId!),
    onSuccess: (data) => setImportMsg(`Rollback: ${data.status}`),
    onError: (e: Error) => setImportMsg(e.message),
  })

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-[var(--dn-muted)]">Phase 06 · simuliert</p>
        <h1 className="text-2xl font-semibold text-[var(--dn-text)]">Diagnosedatenbank</h1>
        <p className="max-w-2xl text-sm text-[var(--dn-muted)]">
          Versionierte Definitionen mit Herkunft. Unbekannte DTCs erscheinen als „unbekannt“. Keine
          Bosch-/Gutmann-/Delphi-Kopien. ODX deaktiviert.
        </p>
      </header>

      {coverage.data && (
        <section className="space-y-2 border-b border-[var(--dn-border)] pb-6">
          <h2 className="text-lg font-medium">Abdeckung</h2>
          <p className="text-sm text-[var(--dn-muted)]">{coverage.data.disclaimer_de}</p>
          <p className="text-sm text-[var(--dn-text)]">
            PIDs: {coverage.data.generic_pids} · ECUs: {coverage.data.ecu_count} · Hersteller (Import):{' '}
            {coverage.data.manufacturer_count} · ODX: {coverage.data.odx_import}
          </p>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-medium">DTC-Lookup</h2>
        <form
          className="flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setLookupCode(dtcCode.trim().toUpperCase())
          }}
        >
          <input
            value={dtcCode}
            onChange={(e) => setDtcCode(e.target.value)}
            className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
            aria-label="DTC-Code"
            maxLength={5}
          />
          <button
            type="submit"
            className="rounded-md bg-[var(--dn-accent)] px-3 py-2 text-sm font-medium text-white"
          >
            Nachschlagen
          </button>
        </form>
        {dtc.data && (
          <div className="space-y-1 text-sm">
            <p>
              <span className="font-medium">{dtc.data.code}</span>: {dtc.data.description_de}
            </p>
            <p className="text-[var(--dn-muted)]">{dtc.data.message_de}</p>
            {dtc.data.provenance && (
              <p className="text-xs text-[var(--dn-muted)]">
                Quelle: {dtc.data.provenance.source_name} · Lizenz: {dtc.data.provenance.license_name} ·
                geprüft {dtc.data.provenance.checked_at}
              </p>
            )}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Import (Demo-JSON)</h2>
        <p className="text-sm text-[var(--dn-muted)]">
          Vorschau → Apply → Rollback. Sample nutzt nur strukturelle DiagNova-Quelle.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => preview.mutate()}
            className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)]"
          >
            Vorschau
          </button>
          <button
            type="button"
            disabled={!batchId}
            onClick={() => apply.mutate()}
            className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)] disabled:opacity-40"
          >
            Apply
          </button>
          <button
            type="button"
            disabled={!batchId}
            onClick={() => rollback.mutate()}
            className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)] disabled:opacity-40"
          >
            Rollback
          </button>
        </div>
        {importMsg && <p className="text-sm text-[var(--dn-muted)]">{importMsg}</p>}
        {batchId && <p className="text-xs text-[var(--dn-muted)]">Batch: {batchId}</p>}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Lizenzquellen</h2>
        <ul className="divide-y divide-[var(--dn-border)] border border-[var(--dn-border)]">
          {(sources.data || []).map((s) => (
            <li key={s.key} className="px-4 py-3 text-sm">
              <div className="font-medium text-[var(--dn-text)]">{s.name}</div>
              <div className="text-xs text-[var(--dn-muted)]">
                {s.key} · {s.license_name} · kommerziell: {s.commercial_use} · redistributable:{' '}
                {String(s.redistributable)} · geprüft {s.checked_at}
              </div>
              {s.notes_de && <p className="mt-1 text-xs text-[var(--dn-muted)]">{s.notes_de}</p>}
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Generische PIDs / ECUs</h2>
        <p className="text-xs text-[var(--dn-muted)]">
          {pids.data?.length ?? 0} PIDs · {ecus.data?.length ?? 0} ECUs – Herkunft je Eintrag in der API.
        </p>
        <ul className="grid gap-2 sm:grid-cols-2">
          {(ecus.data || []).map((e) => (
            <li key={e.id} className="border-b border-[var(--dn-border)] py-2 text-sm">
              {e.name_de} ({e.request_address}→{e.response_address})
              <span className="ml-2 text-xs text-[var(--dn-muted)]">{e.provenance.source_key}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
