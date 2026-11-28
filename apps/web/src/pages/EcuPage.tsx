import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function EcuPage() {
  const overview = useQuery({
    queryKey: ['ecu-overview'],
    queryFn: () => api.ecuOverview(),
  })
  const simulated = useQuery({
    queryKey: ['ecu-simulated'],
    queryFn: () => api.ecuSimulated(),
  })
  const matrix = useQuery({
    queryKey: ['capability-matrix'],
    queryFn: () => api.capabilityMatrix(),
  })

  const loading = overview.isLoading || simulated.isLoading
  const err = overview.error || simulated.error

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-[var(--dn-muted)]">Phase 05 · simuliert</p>
        <h1 className="text-2xl font-semibold text-[var(--dn-text)]">Steuergeräteübersicht</h1>
        <p className="max-w-2xl text-sm text-[var(--dn-muted)]">
          Nur ISO-15765-4-OBD-Standardadressen aus beobachteten Antworten. Kein Blindscan. ABS, Airbag und
          Komfort ohne verifizierte Definition sind nicht verfügbar.
        </p>
      </header>

      {loading && <p className="text-sm text-[var(--dn-muted)]">Laden…</p>}
      {err && (
        <p className="text-sm text-[var(--dn-danger)]">
          Fehler: {err instanceof Error ? err.message : 'Unbekannt'}
        </p>
      )}

      {simulated.data && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-[var(--dn-text)]">Entdeckte OBD-Steuergeräte</h2>
          <p className="text-xs text-[var(--dn-muted)]">
            Quelle: {simulated.data.data_source} · Blindscan: {String(simulated.data.blind_scan_used)} ·{' '}
            {simulated.data.message_de}
          </p>
          <ul className="divide-y divide-[var(--dn-border)] border border-[var(--dn-border)]">
            {simulated.data.discovered_obd_ecus.map((ecu) => (
              <li key={ecu.ecu_id} className="flex flex-wrap items-baseline justify-between gap-2 px-4 py-3">
                <div>
                  <div className="font-medium text-[var(--dn-text)]">{ecu.role_hint_de}</div>
                  <div className="text-xs text-[var(--dn-muted)]">
                    Antwort {ecu.response_hex}
                    {ecu.request_hex ? ` · Request ${ecu.request_hex}` : ''} · {ecu.verified_source}
                  </div>
                </div>
                <span className="text-xs uppercase text-[var(--dn-muted)]">{ecu.status}</span>
              </li>
            ))}
          </ul>
          {simulated.data.identification_read_first && (
            <p className="text-sm text-[var(--dn-muted)]">
              Lesende Identifikation zuerst:{' '}
              {simulated.data.identification_read_first.vin
                ? `VIN ${simulated.data.identification_read_first.vin}`
                : simulated.data.identification_read_first.status}
            </p>
          )}
        </section>
      )}

      {overview.data && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-[var(--dn-text)]">Kategorien</h2>
          <ul className="space-y-2">
            {overview.data.categories.map((cat) => (
              <li key={cat.id} className="border-b border-[var(--dn-border)] py-2 text-sm">
                <span className="text-[var(--dn-text)]">{cat.label_de}</span>
                <span className="ml-2 text-xs text-[var(--dn-muted)]">{cat.availability}</span>
                {cat.notes_de && (
                  <p className="mt-1 text-xs text-[var(--dn-muted)]">{cat.notes_de}</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {matrix.data && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-[var(--dn-text)]">Adapter-Capability (Auszug)</h2>
          <p className="text-xs text-[var(--dn-muted)]">{matrix.data.disclaimer_de}</p>
          <ul className="space-y-2 text-sm">
            {matrix.data.adapters.slice(0, 4).map((a) => (
              <li key={a.adapter_id} className="text-[var(--dn-muted)]">
                <span className="text-[var(--dn-text)]">{a.adapter_id}</span>
                {a.protocols?.iso_13400_doip
                  ? ` · DoIP: ${a.protocols.iso_13400_doip}`
                  : null}
                {a.protocols?.can_fd ? ` · CAN-FD: ${a.protocols.can_fd}` : null}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
