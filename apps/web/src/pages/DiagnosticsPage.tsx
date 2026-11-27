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
  const [history, setHistory] = useState<{ t: string; rpm: number; speed: number; coolant: number }[]>([])
  const [lastReportId, setLastReportId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  const vehiclesQ = useQuery({ queryKey: ['vehicles'], queryFn: () => api.vehicles() })
  const vehicleId =
    params.get('vehicle') || localStorage.getItem('dn_active_vehicle') || vehiclesQ.data?.[0]?.id || null

  const dtcsQ = useQuery({
    queryKey: ['dtcs', vehicleId],
    queryFn: () => api.dtcs(vehicleId!),
    enabled: !!vehicleId,
  })

  const liveQ = useQuery({
    queryKey: ['live', vehicleId],
    queryFn: async () => {
      const live = await api.live(vehicleId!)
      const rpm = live.readings.find((r) => r.name === 'rpm')?.value ?? 0
      const speed = live.readings.find((r) => r.name === 'speed')?.value ?? 0
      const coolant = live.readings.find((r) => r.name === 'coolant_temp')?.value ?? 0
      setHistory((prev) =>
        [...prev, { t: new Date().toLocaleTimeString('de-AT'), rpm, speed, coolant }].slice(-30),
      )
      return live
    },
    enabled: !!vehicleId,
    refetchInterval: 2000,
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

  const vehicleLabel = useMemo(() => {
    const v = vehiclesQ.data?.find((x) => x.id === vehicleId)
    return v ? `${v.make} ${v.model}` : '–'
  }, [vehiclesQ.data, vehicleId])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-blue-100">OBD-Diagnose (Simulator)</h1>
          <p className="text-sm text-slate-400">Fahrzeug: {vehicleLabel}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={!vehicleId || startSession.isPending}
            onClick={() => startSession.mutate()}
            className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-slate-800 disabled:opacity-50"
          >
            Sitzung starten
          </button>
          <button
            type="button"
            disabled={!vehicleId || createReport.isPending}
            onClick={() => createReport.mutate()}
            className="rounded-md bg-blue-600 px-3 py-2 text-sm hover:bg-blue-500 disabled:opacity-50"
          >
            Bericht speichern
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
        <p className="text-xs text-emerald-300">Aktive Sitzung: {sessionId} (simuliert)</p>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
            Fehlercodes (DTCs)
          </h2>
          {!dtcsQ.data?.length ? (
            <p className="text-sm text-slate-400">Keine DTCs oder noch nicht geladen.</p>
          ) : (
            <ul className="space-y-2">
              {dtcsQ.data.map((d) => (
                <li
                  key={`${d.code}-${d.status}`}
                  className="flex items-start justify-between gap-2 rounded-md border border-[var(--dn-border)] px-3 py-2"
                >
                  <div>
                    <div className="font-mono font-semibold text-blue-200">{d.code}</div>
                    <div className="text-sm text-slate-300">{d.description_de}</div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="uppercase text-slate-400">{d.status}</div>
                    <div
                      className={
                        d.severity === 'critical'
                          ? 'text-red-400'
                          : d.severity === 'warning'
                            ? 'text-amber-300'
                            : 'text-slate-400'
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
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
            Live-PIDs
          </h2>
          {liveQ.data ? (
            <>
              <p className="mb-2 text-xs text-amber-300">
                Quelle: {liveQ.data.data_source} · VIN: {liveQ.data.vin}
              </p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {liveQ.data.readings.map((r) => (
                  <div key={r.pid} className="rounded-md bg-slate-950/60 px-3 py-2">
                    <div className="text-[11px] text-slate-500">{r.description_de}</div>
                    <div className="text-lg font-semibold tabular-nums">
                      {r.value} <span className="text-xs font-normal text-slate-400">{r.unit}</span>
                    </div>
                    <div className="font-mono text-[10px] text-slate-500">{r.pid_hex}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-400">Live-Daten werden geladen…</p>
          )}
        </section>
      </div>

      <section className="dn-panel p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
          Live-Verlauf (simuliert)
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid stroke="#1e3a5f" strokeDasharray="3 3" />
              <XAxis dataKey="t" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1e3a5f' }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Line type="monotone" dataKey="rpm" stroke="#60a5fa" dot={false} name="RPM" />
              <Line type="monotone" dataKey="speed" stroke="#34d399" dot={false} name="km/h" />
              <Line type="monotone" dataKey="coolant" stroke="#fbbf24" dot={false} name="°C" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Readiness</h2>
          <ul className="grid grid-cols-2 gap-2 text-sm">
            {liveQ.data &&
              Object.entries(liveQ.data.readiness).map(([k, v]) => (
                <li key={k} className="flex justify-between rounded bg-slate-950/50 px-2 py-1">
                  <span className="text-slate-400">{k}</span>
                  <span className={v ? 'text-emerald-400' : 'text-amber-300'}>{v ? 'OK' : 'offen'}</span>
                </li>
              ))}
          </ul>
        </section>
        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Freeze-Frame</h2>
          {liveQ.data?.freeze_frame ? (
            <dl className="space-y-1 text-sm">
              {Object.entries(liveQ.data.freeze_frame).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <dt className="text-slate-500">{k}</dt>
                  <dd className="font-mono text-slate-200">{String(v)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-sm text-slate-400">Kein Freeze-Frame.</p>
          )}
        </section>
      </div>
    </div>
  )
}
