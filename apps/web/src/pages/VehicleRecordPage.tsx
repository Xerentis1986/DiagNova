import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
  api,
  type SessionCompare,
  type TimelineItem,
  type VehicleRecord,
} from '../lib/api'
import { useAuth } from '../lib/auth'

function authenticityLabel(a: TimelineItem['authenticity']) {
  if (a === 'example_seed') return 'Beispieldaten'
  if (a === 'simulated') return 'Simuliert'
  return 'Erfasst'
}

function outcomeLabel(o: SessionCompare['items'][0]['outcome']) {
  if (o === 'neu') return 'Neu'
  if (o === 'weiterhin_vorhanden') return 'Weiterhin vorhanden'
  return 'Nicht erneut beobachtet'
}

export function VehicleRecordPage() {
  const { vehicleId: routeId } = useParams()
  const [params, setParams] = useSearchParams()
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'technician'
  const qc = useQueryClient()

  const [vinQ, setVinQ] = useState('')
  const [plateQ, setPlateQ] = useState('')
  const [lookupHits, setLookupHits] = useState<VehicleRecord[] | null>(null)
  const [noteBody, setNoteBody] = useState('')
  const [noteType, setNoteType] = useState<'note' | 'service' | 'repair'>('note')
  const [msg, setMsg] = useState<string | null>(null)
  const [compareBefore, setCompareBefore] = useState('')
  const [compareAfter, setCompareAfter] = useState('')
  const [compareResult, setCompareResult] = useState<SessionCompare | null>(null)
  const [selectedSession, setSelectedSession] = useState<string | null>(null)

  const activeId = routeId || params.get('vehicle') || localStorage.getItem('dn_active_vehicle') || ''

  const record = useQuery({
    queryKey: ['vehicle-record', activeId],
    queryFn: () => api.vehicleRecord(activeId),
    enabled: Boolean(activeId),
  })

  const measurements = useQuery({
    queryKey: ['vehicle-measurements', activeId],
    queryFn: () => api.vehicleMeasurements(activeId, { limit: 100 }),
    enabled: Boolean(activeId),
  })

  const sessionDetail = useQuery({
    queryKey: ['session-detail', selectedSession],
    queryFn: () => api.sessionDetail(selectedSession!),
    enabled: Boolean(selectedSession),
  })

  const sessionIds = useMemo(() => {
    const ids =
      record.data?.timeline
        .filter((t) => t.kind === 'session' && t.session_id)
        .map((t) => t.session_id!) ?? []
    return [...new Set(ids)]
  }, [record.data])

  const addNote = useMutation({
    mutationFn: () =>
      api.addVehicleNote(activeId, { body: noteBody, note_type: noteType }),
    onSuccess: () => {
      setNoteBody('')
      setMsg('Notiz gespeichert (als erfasst gekennzeichnet).')
      void qc.invalidateQueries({ queryKey: ['vehicle-record', activeId] })
    },
    onError: (e: Error) => setMsg(e.message),
  })

  async function doLookup() {
    setMsg(null)
    setLookupHits(null)
    if (!vinQ && !plateQ) {
      setMsg('VIN oder Kennzeichen eingeben.')
      return
    }
    try {
      const res = await api.lookupVehicleRecord({
        vin: vinQ || undefined,
        license_plate: plateQ || undefined,
      })
      setLookupHits(res.matches)
      if (res.matches.length === 1) {
        const id = res.matches[0].vehicle_id
        localStorage.setItem('dn_active_vehicle', id)
        setParams({ vehicle: id })
      }
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Lookup fehlgeschlagen')
    }
  }

  async function doCompare() {
    setCompareResult(null)
    if (!compareBefore || !compareAfter) {
      setMsg('Zwei Sitzungen für den Vergleich wählen.')
      return
    }
    try {
      const res = await api.compareSessions(compareBefore, compareAfter)
      setCompareResult(res)
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Vergleich fehlgeschlagen')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Digitale Fahrzeugakte</h1>
        <p className="text-sm text-[var(--dn-muted)]">
          Chronologische Historie – Beispieldaten und Simulation sind gekennzeichnet, keine erfundenen
          Einträge als echt.
        </p>
      </div>

      <section className="dn-panel space-y-3 p-4">
        <h2 className="text-lg font-medium">Wiederaufruf per VIN / Kennzeichen</h2>
        <div className="flex flex-wrap gap-2">
          <input
            className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
            placeholder="VIN"
            value={vinQ}
            onChange={(e) => setVinQ(e.target.value.toUpperCase())}
            maxLength={17}
          />
          <input
            className="rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
            placeholder="Kennzeichen"
            value={plateQ}
            onChange={(e) => setPlateQ(e.target.value.toUpperCase())}
          />
          <button
            type="button"
            onClick={() => void doLookup()}
            className="rounded-md bg-[var(--dn-accent)] px-3 py-2 text-sm text-white"
          >
            Suchen
          </button>
        </div>
        {lookupHits && (
          <ul className="space-y-2 text-sm">
            {lookupHits.length === 0 && (
              <li className="text-[var(--dn-muted)]">Keine Treffer im eigenen Mandanten.</li>
            )}
            {lookupHits.map((m) => (
              <li key={m.vehicle_id}>
                <button
                  type="button"
                  className="text-left underline"
                  onClick={() => {
                    localStorage.setItem('dn_active_vehicle', m.vehicle_id)
                    setParams({ vehicle: m.vehicle_id })
                  }}
                >
                  {m.make} {m.model} · {m.vin} · {m.license_plate || '–'}
                  {m.is_example_data ? ' (Beispieldaten)' : ''}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {msg && <p className="text-sm text-[var(--dn-warn)]">{msg}</p>}

      {!activeId && (
        <p className="text-[var(--dn-muted)]">
          Kein Fahrzeug gewählt.{' '}
          <Link to="/vehicles" className="underline">
            Zur Fahrzeugliste
          </Link>
        </p>
      )}

      {record.isLoading && <p className="text-[var(--dn-muted)]">Akte wird geladen…</p>}
      {record.error && (
        <p className="text-[var(--dn-danger)]">Akte konnte nicht geladen werden (Mandantenschutz).</p>
      )}

      {record.data && (
        <>
          <section className="dn-panel space-y-2 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-wide text-[var(--dn-accent)]">
                  {record.data.make}
                </div>
                <h2 className="text-xl font-semibold">
                  {record.data.model} · {record.data.year}
                </h2>
                <p className="font-mono text-xs text-[var(--dn-muted)]">{record.data.vin}</p>
                <p className="text-sm">
                  {record.data.license_plate || '–'}
                  {record.data.odometer_km != null
                    ? ` · ${record.data.odometer_km.toLocaleString('de-AT')} km`
                    : ''}
                  {' · '}
                  {record.data.session_count} Sitzung(en)
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {record.data.is_example_data && (
                  <span className="rounded bg-[var(--dn-hover)] px-2 py-1 text-xs text-[var(--dn-warn)]">
                    Beispieldaten
                  </span>
                )}
                <Link
                  to={`/diagnostics?vehicle=${record.data.vehicle_id}`}
                  className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 text-sm"
                >
                  Diagnose
                </Link>
              </div>
            </div>
            <p className="text-xs text-[var(--dn-muted)]">{record.data.disclaimer_de}</p>
          </section>

          <section className="dn-panel space-y-3 p-4">
            <h2 className="text-lg font-medium">Zeitstrahl</h2>
            {record.data.timeline.length === 0 ? (
              <p className="text-sm text-[var(--dn-muted)]">Noch keine Historie-Einträge.</p>
            ) : (
              <ol className="relative space-y-4 border-l border-[var(--dn-border)] pl-4">
                {record.data.timeline.map((item) => (
                  <li key={item.id} className="relative">
                    <span className="absolute -left-[1.35rem] top-1 h-2.5 w-2.5 rounded-full bg-[var(--dn-accent)]" />
                    <div className="flex flex-wrap items-baseline gap-2">
                      <time className="text-xs text-[var(--dn-muted)]">
                        {new Date(item.at).toLocaleString('de-AT')}
                      </time>
                      <span className="text-xs rounded bg-[var(--dn-hover)] px-1.5 py-0.5">
                        {authenticityLabel(item.authenticity)}
                      </span>
                      {item.data_source === 'simulated' && (
                        <span className="text-xs text-[var(--dn-warn)]">data_source=simulated</span>
                      )}
                    </div>
                    <div className="font-medium">{item.title_de}</div>
                    <p className="text-sm text-[var(--dn-muted)]">{item.summary_de}</p>
                    {item.session_id && (
                      <button
                        type="button"
                        className="mt-1 text-xs underline"
                        onClick={() => setSelectedSession(item.session_id!)}
                      >
                        Sitzungsdetail
                      </button>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>

          {canWrite && (
            <section className="dn-panel space-y-3 p-4">
              <h2 className="text-lg font-medium">Notiz / Service / Reparatur</h2>
              <div className="flex flex-wrap gap-2">
                <select
                  className="rounded-md border border-[var(--dn-border)] bg-transparent px-2 py-2 text-sm"
                  value={noteType}
                  onChange={(e) => setNoteType(e.target.value as typeof noteType)}
                >
                  <option value="note">Notiz</option>
                  <option value="service">Service</option>
                  <option value="repair">Reparatur</option>
                </select>
                <input
                  className="min-w-[16rem] flex-1 rounded-md border border-[var(--dn-border)] bg-transparent px-3 py-2 text-sm"
                  placeholder="Eintrag (keine erfundenen Fakten als echt)"
                  value={noteBody}
                  onChange={(e) => setNoteBody(e.target.value)}
                />
                <button
                  type="button"
                  disabled={!noteBody.trim() || addNote.isPending}
                  onClick={() => addNote.mutate()}
                  className="rounded-md bg-[var(--dn-accent)] px-3 py-2 text-sm text-white disabled:opacity-50"
                >
                  Speichern
                </button>
              </div>
            </section>
          )}

          <section className="dn-panel space-y-3 p-4">
            <h2 className="text-lg font-medium">Vorher/Nachher DTC-Vergleich</h2>
            <p className="text-xs text-[var(--dn-muted)]">
              „Nicht erneut beobachtet“ ohne ECU-Prüfung wird nicht als behoben dargestellt.
            </p>
            <div className="flex flex-wrap gap-2">
              <select
                className="rounded-md border border-[var(--dn-border)] bg-transparent px-2 py-2 text-sm"
                value={compareBefore}
                onChange={(e) => setCompareBefore(e.target.value)}
              >
                <option value="">Frühere Sitzung…</option>
                {sessionIds.map((id) => (
                  <option key={`b-${id}`} value={id}>
                    {id.slice(0, 8)}…
                  </option>
                ))}
              </select>
              <select
                className="rounded-md border border-[var(--dn-border)] bg-transparent px-2 py-2 text-sm"
                value={compareAfter}
                onChange={(e) => setCompareAfter(e.target.value)}
              >
                <option value="">Spätere Sitzung…</option>
                {sessionIds.map((id) => (
                  <option key={`a-${id}`} value={id}>
                    {id.slice(0, 8)}…
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void doCompare()}
                className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm"
              >
                Vergleichen
              </button>
            </div>
            {compareResult && (
              <div className="space-y-2 text-sm">
                {compareResult.incomplete_scan && (
                  <p className="text-[var(--dn-warn)]">
                    Unvollständiger Scan – nicht geprüft:{' '}
                    {compareResult.unchecked_ecus_in_after.join(', ') || '–'}
                  </p>
                )}
                <p className="text-xs text-[var(--dn-muted)]">{compareResult.disclaimer_de}</p>
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--dn-border)] text-xs text-[var(--dn-muted)]">
                      <th className="py-1">ECU</th>
                      <th>Code</th>
                      <th>Ergebnis</th>
                      <th>Hinweis</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareResult.items.map((it, i) => (
                      <tr key={`${it.code}-${i}`} className="border-b border-[var(--dn-border)]/50">
                        <td className="py-1">{it.ecu_code}</td>
                        <td className="font-mono">{it.code}</td>
                        <td>
                          {outcomeLabel(it.outcome)}
                          {!it.may_interpret_as_resolved &&
                            it.outcome === 'nicht_erneut_beobachtet' && (
                              <span className="ml-1 text-xs text-[var(--dn-warn)]">≠ behoben</span>
                            )}
                        </td>
                        <td className="text-xs text-[var(--dn-muted)]">{it.note_de}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="dn-panel space-y-3 p-4">
            <h2 className="text-lg font-medium">Messwertverlauf (begrenzt)</h2>
            {measurements.data ? (
              <>
                <p className="text-xs text-[var(--dn-muted)]">{measurements.data.disclaimer_de}</p>
                <p className="text-sm">
                  {measurements.data.count} Sample(s)
                  {measurements.data.truncated ? ' · gekürzt' : ''}
                  {measurements.data.unit ? ` · Einheit ${measurements.data.unit}` : ''}
                </p>
                <div className="max-h-48 overflow-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="text-[var(--dn-muted)]">
                        <th className="py-1">Zeit</th>
                        <th>Name</th>
                        <th>Wert</th>
                        <th>Quelle</th>
                      </tr>
                    </thead>
                    <tbody>
                      {measurements.data.samples.slice(-40).map((s) => (
                        <tr key={s.id}>
                          <td>{new Date(s.recorded_at).toLocaleTimeString('de-AT')}</td>
                          <td>{s.name}</td>
                          <td>
                            {s.value} {s.unit}
                          </td>
                          <td>{s.data_source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <p className="text-sm text-[var(--dn-muted)]">Keine Messwerte gespeichert.</p>
            )}
          </section>

          {sessionDetail.data && (
            <section className="dn-panel space-y-2 p-4">
              <h2 className="text-lg font-medium">Sitzungsdetail</h2>
              <p className="text-sm">
                {sessionDetail.data.vehicle_label} · Status{' '}
                <strong>{sessionDetail.data.status}</strong> ·{' '}
                {sessionDetail.data.data_source} · {sessionDetail.data.adapter_name} ·{' '}
                {sessionDetail.data.protocol_name}
              </p>
              {sessionDetail.data.abort_reason && (
                <p className="text-sm text-[var(--dn-warn)]">
                  Abbruch: {sessionDetail.data.abort_reason}
                </p>
              )}
              <p className="text-sm">
                Benutzer: {sessionDetail.data.user_name || sessionDetail.data.user_id} · km:{' '}
                {sessionDetail.data.odometer_km ?? '–'} · DTCs: {sessionDetail.data.dtc_count} ·
                Messwerte: {sessionDetail.data.measurement_sample_count}
              </p>
              <ul className="text-sm">
                {sessionDetail.data.ecus.map((e) => (
                  <li key={e.ecu_code}>
                    ECU {e.ecu_code} ({e.ecu_label_de}) – geprüft: {e.checked ? 'ja' : 'nein'}
                  </li>
                ))}
              </ul>
              <ul className="font-mono text-xs">
                {sessionDetail.data.dtcs.map((d) => (
                  <li key={`${d.code}-${d.dtc_status}`}>
                    {d.code} [{d.dtc_status}] {d.description_de}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  )
}
