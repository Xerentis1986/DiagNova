import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export function DashboardPage() {
  const activeId = localStorage.getItem('dn_active_vehicle')
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', activeId],
    queryFn: () => api.dashboard(activeId),
    refetchInterval: 10000,
  })

  if (isLoading) return <p className="text-slate-400">Dashboard wird geladen…</p>
  if (error || !data) return <p className="text-red-400">Dashboard konnte nicht geladen werden.</p>

  const vehicle = data.active_vehicle

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-blue-100">Werkstatt-Dashboard</h1>
          <p className="text-sm text-slate-400">Überblick · Demo-Modus {data.demo_mode ? 'aktiv' : 'aus'}</p>
        </div>
        <div className="flex gap-2">
          <Link to="/vehicles" className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-slate-800">
            Fahrzeug wählen
          </Link>
          <Link to="/diagnostics" className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium hover:bg-blue-500">
            Diagnose starten
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <section className="dn-panel p-4 md:col-span-2">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Aktives Fahrzeug</h2>
          {vehicle ? (
            <div>
              <div className="text-xl font-semibold">
                {vehicle.make} {vehicle.model}{' '}
                <span className="text-base font-normal text-slate-400">({vehicle.year})</span>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm text-slate-300">
                <div>
                  <dt className="text-slate-500">VIN</dt>
                  <dd className="font-mono">{vehicle.vin}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Kennzeichen</dt>
                  <dd>{vehicle.license_plate || '–'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Motor</dt>
                  <dd>{vehicle.engine || '–'}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Kraftstoff</dt>
                  <dd>{vehicle.fuel_type || '–'}</dd>
                </div>
              </dl>
              {vehicle.is_example_data && (
                <p className="mt-3 text-xs text-amber-300/90">Beispieldaten – keine volle Markenabdeckung.</p>
              )}
            </div>
          ) : (
            <p className="text-slate-400">Kein Fahrzeug gewählt.</p>
          )}
        </section>

        <section className="dn-panel p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Verbindung</h2>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                data.connection.connected ? 'bg-emerald-400' : 'bg-red-400'
              }`}
            />
            <span className="font-medium">{data.connection.adapter_name}</span>
          </div>
          <p className="mt-2 text-sm text-slate-400">{data.connection.message_de}</p>
          <p className="mt-2 text-xs text-amber-300">Modus: {data.connection.mode} · Quelle: {data.connection.data_source}</p>
        </section>
      </div>

      <section className="dn-panel p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Letzte Sitzungen</h2>
        {data.recent_sessions.length === 0 ? (
          <p className="text-sm text-slate-400">Noch keine Sitzungen. Starte eine Diagnose im Simulator.</p>
        ) : (
          <ul className="divide-y divide-[var(--dn-border)]">
            {data.recent_sessions.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <div className="font-medium">{s.vehicle_label}</div>
                  <div className="text-xs text-slate-500">
                    {new Date(s.started_at).toLocaleString('de-AT')} · {s.dtc_count} DTCs · {s.data_source}
                  </div>
                </div>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-xs uppercase text-slate-300">{s.status}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="dn-panel p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Schnellzugriff / Geplant</h2>
        <div className="flex flex-wrap gap-2">
          {data.planned_modules.map((m) => (
            <Link
              key={m.id}
              to={`/planned/${m.id}`}
              className="rounded-md border border-dashed border-slate-600 px-3 py-2 text-sm text-slate-400 hover:border-blue-500 hover:text-blue-200"
            >
              {m.label} <span className="text-[10px] uppercase">Geplant</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
