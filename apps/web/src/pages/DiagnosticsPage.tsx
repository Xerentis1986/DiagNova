import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../lib/api'

export function DiagnosticsPage() {
  const [params] = useSearchParams()
  const qc = useQueryClient()
  const [diagMode, setDiagMode] = useState<'demo' | 'live'>(() =>
    (localStorage.getItem('dn_diag_mode') as 'demo' | 'live') || 'demo',
  )
  const [history, setHistory] = useState<{ t: string; rpm: number; speed: number; coolant: number }[]>([])
  const [lastReportId, setLastReportId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [showClear, setShowClear] = useState(false)
  const [clearPhrase, setClearPhrase] = useState('')
  const [ackFf, setAckFf] = useState(false)
  const [ackRdy, setAckRdy] = useState(false)
  const [ackPerm, setAckPerm] = useState(false)
  const [ackReport, setAckReport] = useState(false)
  const [clearMsg, setClearMsg] = useState<string | null>(null)

  const vehiclesQ = useQuery({ queryKey: ['vehicles'], queryFn: () => api.vehicles() })
  const vehicleId =
    params.get('vehicle') || localStorage.getItem('dn_active_vehicle') || vehiclesQ.data?.[0]?.id || null

  const bridgeQ = useQuery({
    queryKey: ['bridge-status'],
    queryFn: () => api.bridgeStatus(),
    refetchInterval: 10000,
  })
  const connectionQ = useQuery({
    queryKey: ['connection', diagMode],
    queryFn: () => api.connection(diagMode),
    refetchInterval: 5000,
  })

  const dtcsQ = useQuery({
    queryKey: ['dtcs', vehicleId, diagMode],
    queryFn: () => api.dtcs(vehicleId!, diagMode),
    enabled: !!vehicleId,
    retry: diagMode === 'live' ? false : 1,
  })

  const liveQ = useQuery({
    queryKey: ['live', vehicleId, diagMode],
    queryFn: async () => {
      const live = await api.live(vehicleId!, diagMode)
      const rpm = live.readings.find((r) => r.name === 'rpm')?.value ?? 0
      const speed = live.readings.find((r) => r.name === 'speed')?.value ?? 0
      const coolant = live.readings.find((r) => r.name === 'coolant_temp')?.value ?? 0
      setHistory((prev) =>
        [...prev, { t: new Date().toLocaleTimeString('de-AT'), rpm, speed, coolant }].slice(-30),
      )
      return live
    },
    enabled: !!vehicleId,
    refetchInterval: diagMode === 'demo' ? 2000 : 3000,
    retry: diagMode === 'live' ? false : 1,
  })

  const startSession = useMutation({
    mutationFn: () => api.startSession(vehicleId!),
    onSuccess: (s) => {
      setSessionId(s.id)
      void qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const createReport = useMutation({
    mutationFn: async () => {
      let sid = sessionId
      if (!sid) {
        const s = await api.startSession(vehicleId!)
        sid = s.id
        setSessionId(sid)
      }
      const vehicle = vehiclesQ.data?.find((v) => v.id === vehicleId)
      return api.createReport(sid, `Simulierter Bericht – ${vehicle?.make ?? ''} ${vehicle?.model ?? ''}`)
    },
    onSuccess: (r) => setLastReportId(r.id),
  })

  const clearWarningsQ = useQuery({
    queryKey: ['clear-warnings'],
    queryFn: () => api.clearDtcWarnings(),
    enabled: showClear,
  })

  const clearDtcs = useMutation({
    mutationFn: () =>
      api.clearDtcs(vehicleId!, {
        confirmation_phrase: clearPhrase,
        acknowledge_freeze_frame_loss: ackFf,
        acknowledge_readiness_reset: ackRdy,
        acknowledge_permanent_remain: ackPerm,
        pre_report_saved: ackReport,
        operator_note: 'UI simulated clear',
      }),
    onSuccess: (r) => {
      setClearMsg(r.message_de)
      setShowClear(false)
      void qc.invalidateQueries({ queryKey: ['dtcs', vehicleId] })
    },
    onError: (e: Error) => setClearMsg(e.message),
  })

  const vehicleLabel = useMemo(() => {
    const v = vehiclesQ.data?.find((x) => x.id === vehicleId)
    return v ? `${v.make} ${v.model}` : '–'
  }, [vehiclesQ.data, vehicleId])

  const dataSource = liveQ.data?.data_source ?? 'simulated'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--dn-text)]">OBD-Diagnose</h1>
          <p className="text-sm text-[var(--dn-muted)]">Fahrzeug: {vehicleLabel}</p>
          <p
            className={`mt-1 text-xs font-medium ${
              dataSource === 'live' ? 'text-[var(--dn-ok)]' : 'text-[var(--dn-warn)]'
            }`}
          >
            Datenquelle: {dataSource === 'live' ? 'LIVE' : 'DEMO / simuliert'} – strikt getrennt
          </p>
          <p className="mt-1 text-xs text-[var(--dn-muted)]">
            Connector:{' '}
            {bridgeQ.data?.connector?.reachable
              ? `erreichbar (${bridgeQ.data.connector.base_url ?? 'loopback'})`
              : `nicht erreichbar${bridgeQ.data?.connector?.error_de ? ` – ${bridgeQ.data.connector.error_de}` : ''}`}
            {connectionQ.data ? ` · Modus-API: ${connectionQ.data.mode}` : ''}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            className="rounded-md border border-[var(--dn-border)] bg-transparent px-2 py-2 text-sm"
            value={diagMode}
            onChange={(e) => {
              const m = e.target.value === 'live' ? 'live' : 'demo'
              setDiagMode(m)
              localStorage.setItem('dn_diag_mode', m)
              setHistory([])
              void qc.invalidateQueries({ queryKey: ['live'] })
              void qc.invalidateQueries({ queryKey: ['dtcs'] })
            }}
          >
            <option value="demo">DEMO</option>
            <option value="live">LIVE (Connector)</option>
          </select>
          <button
            type="button"
            disabled={!vehicleId || startSession.isPending}
            onClick={() => startSession.mutate()}
            className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)] disabled:opacity-50"
          >
            Sitzung starten
          </button>
          <button
            type="button"
            disabled={!vehicleId || createReport.isPending}
            onClick={() => createReport.mutate()}
            className="dn-btn-primary px-3 py-2 text-sm disabled:opacity-50"
          >
            Vorher-Bericht speichern
          </button>
          <button
            type="button"
            disabled={!vehicleId}
            onClick={() => {
              setShowClear(true)
              setClearMsg(null)
            }}
            className="rounded-md border border-[color-mix(in_srgb,var(--dn-danger)_55%,var(--dn-border))] px-3 py-2 text-sm text-[var(--dn-danger)] hover:bg-[color-mix(in_srgb,var(--dn-danger)_10%,transparent)] disabled:opacity-50"
          >
            Fehler löschen…
          </button>
          {lastReportId && (
            <>
              <button
                type="button"
                className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm"
                onClick={() => void api.downloadExport(lastReportId, 'csv')}
              >
                CSV
              </button>
              <button
                type="button"
                className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm"
                onClick={() => void api.downloadExport(lastReportId, 'pdf')}
              >
                PDF
              </button>
            </>
          )}
        </div>
      </div>

      {sessionId && (
        <p className="text-xs text-[var(--dn-ok)]">
          Aktive Sitzung: {sessionId} ({dataSource})
        </p>
      )}
      {clearMsg && <p className="text-sm text-[var(--dn-warn)]">{clearMsg}</p>}

      {showClear && (
        <section className="dn-panel space-y-3 border border-[color-mix(in_srgb,var(--dn-danger)_45%,var(--dn-border))] p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-[var(--dn-danger)]">
            Fehlerlöschung (freigabegeschützt)
          </h2>
          <p className="text-xs text-[var(--dn-muted)]">
            Quelle: {clearWarningsQ.data?.data_source ?? '…'} · Hardware-Live:{' '}
            {clearWarningsQ.data?.hardware_live ? 'ja' : 'nein (Simulator)'}
          </p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--dn-text)]">
            {(clearWarningsQ.data?.warnings_de ?? []).map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={ackFf} onChange={(e) => setAckFf(e.target.checked)} />
            Freeze-Frame-Verlust verstanden
          </label>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={ackRdy} onChange={(e) => setAckRdy(e.target.checked)} />
            Readiness-Reset verstanden
          </label>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={ackPerm} onChange={(e) => setAckPerm(e.target.checked)} />
            Permanente DTCs bleiben bestehen
          </label>
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={ackReport}
              onChange={(e) => setAckReport(e.target.checked)}
            />
            Vorher-Bericht wurde gespeichert
          </label>
          <label className="block text-sm">
            Bestätigungsphrase ({clearWarningsQ.data?.requires_confirmation_phrase ?? '…'})
            <input
              className="mt-1 w-full rounded border border-[var(--dn-border)] bg-[var(--dn-surface-inset)] px-2 py-1 font-mono text-sm"
              value={clearPhrase}
              onChange={(e) => setClearPhrase(e.target.value)}
              autoComplete="off"
            />
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              className="rounded-md bg-[var(--dn-danger)] px-3 py-2 text-sm disabled:opacity-50"
              disabled={clearDtcs.isPending || !vehicleId}
              onClick={() => clearDtcs.mutate()}
            >
              Löschung ausführen (simuliert)
            </button>
            <button
              type="button"
              className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm"
              onClick={() => setShowClear(false)}
            >
              Abbrechen
            </button>
          </div>
        </section>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">
            Fehlercodes (DTCs)
          </h2>
          {!dtcsQ.data?.length ? (
            <p className="text-sm text-[var(--dn-muted)]">Keine DTCs oder noch nicht geladen.</p>
          ) : (
            <ul className="space-y-2">
              {dtcsQ.data.map((d) => (
                <li
                  key={`${d.code}-${d.status}`}
                  className="flex items-start justify-between gap-2 rounded-md border border-[var(--dn-border)] px-3 py-2"
                >
                  <div>
                    <div className="font-mono font-semibold text-[var(--dn-accent)]">{d.code}</div>
                    <div className="text-sm text-[var(--dn-text)]">{d.description_de}</div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="uppercase text-[var(--dn-muted)]">{d.status}</div>
                    {d.status === 'permanent' && (
                      <div className="text-[var(--dn-danger)]">nicht löschbar</div>
                    )}
                    <div
                      className={
                        d.severity === 'critical'
                          ? 'text-[var(--dn-danger)]'
                          : d.severity === 'warning'
                            ? 'text-[var(--dn-warn)]'
                            : 'text-[var(--dn-muted)]'
                      }
                    >
                      {d.severity}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">
            Live-PIDs
          </h2>
          {liveQ.data ? (
            <>
              <p className="mb-2 text-xs text-[var(--dn-warn)]">
                Quelle: {liveQ.data.data_source} · VIN: {liveQ.data.vin}
              </p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {liveQ.data.readings.map((r) => (
                  <div key={r.pid} className="rounded-md dn-surface-inset px-3 py-2">
                    <div className="text-[11px] text-[var(--dn-muted)]">{r.description_de}</div>
                    <div className="text-lg font-semibold tabular-nums">
                      {r.value} <span className="text-xs font-normal text-[var(--dn-muted)]">{r.unit}</span>
                    </div>
                    <div className="font-mono text-[10px] text-[var(--dn-muted)]">{r.pid_hex}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-[var(--dn-muted)]">Live-Daten werden geladen…</p>
          )}
        </section>
      </div>

      <section className="dn-panel p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">
          Live-Verlauf (simuliert)
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid stroke="var(--dn-chart-grid)" strokeDasharray="3 3" />
              <XAxis dataKey="t" stroke="var(--dn-chart-axis)" tick={{ fontSize: 10 }} />
              <YAxis stroke="var(--dn-chart-axis)" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  background: 'var(--dn-chart-tooltip-bg)',
                  border: '1px solid var(--dn-border)',
                  color: 'var(--dn-text)',
                }}
                labelStyle={{ color: 'var(--dn-muted)' }}
              />
              <Line type="monotone" dataKey="rpm" stroke="var(--dn-accent)" dot={false} name="RPM" />
              <Line type="monotone" dataKey="speed" stroke="var(--dn-ok)" dot={false} name="km/h" />
              <Line type="monotone" dataKey="coolant" stroke="var(--dn-warn)" dot={false} name="°C" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">Readiness</h2>
          <ul className="grid grid-cols-2 gap-2 text-sm">
            {liveQ.data &&
              Object.entries(liveQ.data.readiness).map(([k, v]) => (
                <li key={k} className="flex justify-between rounded dn-surface-inset px-2 py-1">
                  <span className="text-[var(--dn-muted)]">{k}</span>
                  <span className={v ? 'text-[var(--dn-ok)]' : 'text-[var(--dn-warn)]'}>{v ? 'OK' : 'offen'}</span>
                </li>
              ))}
          </ul>
        </section>
        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">Freeze-Frame</h2>
          {liveQ.data?.freeze_frame ? (
            <dl className="space-y-1 text-sm">
              {Object.entries(liveQ.data.freeze_frame).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <dt className="text-[var(--dn-muted)]">{k}</dt>
                  <dd className="font-mono text-[var(--dn-text)]">{String(v)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-sm text-[var(--dn-muted)]">Kein Freeze-Frame.</p>
          )}
        </section>
      </div>
    </div>
  )
}
