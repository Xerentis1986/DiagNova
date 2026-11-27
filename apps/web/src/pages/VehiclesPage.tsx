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

  if (isLoading) return <p className="text-[var(--dn-muted)]">Fahrzeuge werden geladen…</p>
  if (error || !data) return <p className="text-[var(--dn-danger)]">Fahrzeuge konnten nicht geladen werden.</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Fahrzeugliste</h1>
          <p className="text-sm text-[var(--dn-muted)]">
            Demo-Fahrzeuge und bestätigte Auswahlen. Keine volle Marken-Diagnoseabdeckung.
          </p>
        </div>
        <Link
          to="/"
          className="rounded-md bg-[var(--dn-accent)] px-3 py-2 text-sm text-white hover:opacity-90"
        >
          Über Marke wählen
        </Link>
      </div>

      {data.length === 0 ? (
        <div className="dn-panel p-8 text-center" role="status">
          <p className="text-lg font-medium">Keine Fahrzeuge</p>
          <p className="mt-1 text-sm text-[var(--dn-muted)]">Starte mit der Markenübersicht.</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((v) => (
            <article key={v.id} className="dn-panel flex flex-col p-4">
              <div className="mb-1 text-xs uppercase tracking-wide text-[var(--dn-accent)]">{v.make}</div>
              <h2 className="text-lg font-semibold">
                {v.model}{' '}
                <span className="text-sm font-normal text-[var(--dn-muted)]">
                  {v.series ? `${v.series} · ` : ''}
                  {v.year}
                </span>
              </h2>
              <p className="mt-1 font-mono text-xs text-[var(--dn-muted)]">{v.vin}</p>
              <p className="mt-2 text-sm">
                {v.engine} · {v.fuel_type} · {v.license_plate || '–'}
                {v.odometer_km != null ? ` · ${v.odometer_km.toLocaleString('de-AT')} km` : ''}
              </p>
              {v.is_example_data && (
                <p className="mt-2 text-xs text-[var(--dn-warn)]">Beispieldaten</p>
              )}
              <div className="mt-auto flex gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => selectVehicle(v.id)}
                  className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 text-sm hover:bg-[var(--dn-hover)]"
                >
                  Aktiv setzen
                </button>
                <Link
                  to={`/diagnostics?vehicle=${v.id}`}
                  onClick={() => selectVehicle(v.id)}
                  className="rounded-md bg-[var(--dn-accent)] px-3 py-1.5 text-sm text-white hover:opacity-90"
                >
                  Diagnose
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
