import { Link, useParams } from 'react-router-dom'
import { Badge, Panel } from '../components/ui'

const LABELS: Record<string, string> = {
  ecu: 'Steuergeräte',
  service: 'Servicefunktionen',
  coding: 'Codierung',
  actuator: 'Stellglieddiagnose',
  flash: 'Programmierung',
  chiptuning: 'Chiptuning',
  lkw: 'LKW / Nutzfahrzeug (J1939/RP1210)',
}

const EXTRA: Record<string, string> = {
  chiptuning:
    'Phase 18 liefert Architektur, Baselines und Gates. ' +
    'Keine Kennfeldänderungen, kein Flash, keine produktive Aktivierung.',
  lkw:
    'Phase 19 liefert nur Architektur, Capability-Flags und Markennavigation. ' +
    'Keine J1939-Diagnose, keine RP1210-Verbindung, keine simulierten LKW-Messwerte.',
}

export function PlannedPage() {
  const { moduleId = '' } = useParams()
  const label = LABELS[moduleId] || moduleId || 'Modul'

  return (
    <Panel className="mx-auto max-w-2xl p-8 text-center">
      <Badge>Geplant</Badge>
      <h1 className="dn-page-title mt-4">{label}</h1>
      <p className="mt-3 text-sm text-[var(--dn-muted)]">
        Dieses Modul ist für eine spätere Phase vorgesehen und im MVP nicht verfügbar. Es handelt sich um keine
        fertige Funktion und um keine echte Fahrzeugdiagnose.
      </p>
      {EXTRA[moduleId] && (
        <p className="mt-3 text-sm text-[var(--dn-muted)]">{EXTRA[moduleId]}</p>
      )}
      {moduleId === 'lkw' && (
        <p className="mt-4 text-sm">
          <Link className="text-[var(--dn-accent)] underline" to="/lkw">
            Zur Architekturübersicht
          </Link>
        </p>
      )}
      {moduleId === 'chiptuning' && (
        <p className="mt-4 text-sm">
          <Link className="text-[var(--dn-accent)] underline" to="/tuning">
            Zur Tuning-Architektur
          </Link>
        </p>
      )}
    </Panel>
  )
}
