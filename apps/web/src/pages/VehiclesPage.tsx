import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export function VehiclesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => api.vehicles(),
  })

  function selectVehicle(id: string) {
    localStorage.setItem('dn_active_vehicle', id)
  }

  if (isLoading) return <p className="text-slate-400">Fahrzeuge werden geladen…</p>
  if (error || !data) return <p className="text-red-400">Fahrzeuge konnten nicht geladen werden.</p>

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-blue-100">Fahrzeugauswahl</h1>
        <p className="text-sm text-slate-400">
          Seed-Beispieldaten (VW, Audi, BMW, Mercedes-Benz, Škoda, Seat, Opel, Ford, Toyota) – keine volle Abdeckung.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((v) => (
          <article key={v.id} className="dn-panel flex flex-col p-4">
            <div className="mb-1 text-xs uppercase tracking-wide text-blue-300/80">{v.make}</div>
            <h2 className="text-lg font-semibold">
              {v.model} <span className="text-sm font-normal text-slate-400">{v.year}</span>
            </h2>
            <p className="mt-1 font-mono text-xs text-slate-400">{v.vin}</p>
            <p className="mt-2 text-sm text-slate-300">
              {v.engine} · {v.fuel_type} · {v.license_plate}
            </p>
            {v.is_example_data && (
              <p className="mt-2 text-xs text-amber-300/90">Beispieldaten</p>
            )}
            <div className="mt-auto flex gap-2 pt-4">
              <button
                type="button"
                onClick={() => selectVehicle(v.id)}
                className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-slate-800"
              >
                Aktiv setzen
              </button>
              <Link
                to={`/diagnostics?vehicle=${v.id}`}
                onClick={() => selectVehicle(v.id)}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm hover:bg-blue-500"
              >
                Diagnose
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
