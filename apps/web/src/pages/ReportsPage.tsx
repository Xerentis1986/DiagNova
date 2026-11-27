import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => api.sessions(),
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-blue-100">Berichte</h1>
        <p className="text-sm text-slate-400">
          Berichte entstehen aus Diagnosesitzungen. Export als CSV/PDF auf der Diagnose-Seite nach dem Speichern.
        </p>
      </div>
      <section className="dn-panel p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">Sitzungen</h2>
        {isLoading && <p className="text-sm text-slate-400">Laden…</p>}
        {!isLoading && !data?.length && (
          <p className="text-sm text-slate-400">
            Noch keine Sitzungen.{' '}
            <Link className="text-blue-300 underline" to="/diagnostics">
              Zur Diagnose
            </Link>
          </p>
        )}
        <ul className="divide-y divide-[var(--dn-border)]">
          {data?.map((s) => (
            <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
              <div>
                <div className="font-medium">{s.vehicle_label}</div>
                <div className="text-xs text-slate-500">
                  {new Date(s.started_at).toLocaleString('de-AT')} · {s.dtc_count} DTCs · Quelle:{' '}
                  {s.data_source}
                </div>
              </div>
              <Link to="/diagnostics" className="text-blue-300 hover:underline">
                Diagnose öffnen
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
