import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button, Badge, Panel, PageHeader, SectionTitle } from '../components/ui'
import { api } from '../lib/api'

export function DashboardPage() {
  const activeId = localStorage.getItem('dn_active_vehicle')
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', activeId],
    queryFn: () => api.dashboard(activeId),
    refetchInterval: 10000,
  })

  if (isLoading) return <p className="text-[var(--dn-muted)]">Dashboard wird geladen…</p>
  if (error || !data) return <p className="text-[var(--dn-danger)]">Dashboard konnte nicht geladen werden.</p>

  const vehicle = data.active_vehicle

  return (
    <div className="space-y-6">
      <PageHeader
        title="Werkstatt-Dashboard"
        description={`Überblick · Demo-Modus ${data.demo_mode ? 'aktiv' : 'aus'}`}
        actions={
          <>
            <Link to="/">
              <Button variant="secondary">Marke wählen</Button>
            </Link>
            <Link to="/diagnostics">
              <Button variant="primary">Diagnose starten</Button>
            </Link>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Panel className="md:col-span-2">
          <SectionTitle>Aktives Fahrzeug</SectionTitle>
          {vehicle ? (
            <div>
              <div className="text-xl font-semibold">
                {vehicle.make} {vehicle.model}{' '}
                <span className="text-base font-normal text-[var(--dn-muted)]">({vehicle.year})</span>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <dt className="text-[var(--dn-muted)]">VIN</dt>
                  <dd className="font-mono">{vehicle.vin}</dd>
                </div>
                <div>
                  <dt className="text-[var(--dn-muted)]">Kennzeichen</dt>
                  <dd>{vehicle.license_plate || '–'}</dd>
                </div>
                <div>
                  <dt className="text-[var(--dn-muted)]">Motor</dt>
                  <dd>{vehicle.engine || '–'}</dd>
                </div>
                <div>
                  <dt className="text-[var(--dn-muted)]">Kraftstoff</dt>
                  <dd>{vehicle.fuel_type || '–'}</dd>
                </div>
              </dl>
              {vehicle.is_example_data && (
                <p className="mt-3 text-xs text-[var(--dn-warn)]">
                  Beispieldaten – keine volle Markenabdeckung.
                </p>
              )}
            </div>
          ) : (
            <p className="text-[var(--dn-muted)]">Kein Fahrzeug gewählt.</p>
          )}
        </Panel>

        <Panel>
          <SectionTitle>Verbindung</SectionTitle>
          <div className="flex items-center gap-2">
            <span
              className={`dn-status-dot ${
                data.connection.connected ? 'dn-status-dot--ok' : 'dn-status-dot--danger'
              }`}
            />
            <span className="font-medium">{data.connection.adapter_name}</span>
          </div>
          <p className="mt-2 text-sm text-[var(--dn-muted)]">{data.connection.message_de}</p>
          <p className="mt-2 text-xs text-[var(--dn-warn)]">
            Modus: {data.connection.mode} · Quelle: {data.connection.data_source}
          </p>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Letzte Sitzungen</SectionTitle>
        {data.recent_sessions.length === 0 ? (
          <p className="text-sm text-[var(--dn-muted)]">
            Noch keine Sitzungen. Starte eine Diagnose im Simulator.
          </p>
        ) : (
          <ul className="divide-y divide-[var(--dn-border)]">
            {data.recent_sessions.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <div className="font-medium">{s.vehicle_label}</div>
                  <div className="text-xs text-[var(--dn-muted)]">
                    {new Date(s.started_at).toLocaleString('de-AT')} · {s.dtc_count} DTCs · {s.data_source}
                  </div>
                </div>
                <Badge>{s.status}</Badge>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel>
        <SectionTitle>Schnellzugriff / Geplant</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {data.planned_modules.map((m) => {
            const simRoutes: Record<string, string> = {
              ecu: '/ecu',
              service: '/service',
              guided: '/guided',
            }
            const isSim = m.status === 'simulated' && simRoutes[m.id]
            return (
              <Link
                key={m.id}
                to={isSim ? simRoutes[m.id] : `/planned/${m.id}`}
                className="rounded-md border border-dashed border-[var(--dn-border)] px-3 py-2 text-sm text-[var(--dn-muted)] hover:border-[var(--dn-accent)] hover:text-[var(--dn-text)]"
              >
                {m.label}{' '}
                <span className="text-[10px] uppercase">{isSim ? 'Simuliert' : 'Geplant'}</span>
              </Link>
            )
          })}
        </div>
      </Panel>
    </div>
  )
}
