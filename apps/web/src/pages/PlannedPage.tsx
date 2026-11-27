import { useParams } from 'react-router-dom'
import { Badge, Panel } from '../components/ui'

const LABELS: Record<string, string> = {
  ecu: 'Steuergeräte',
  service: 'Servicefunktionen',
  coding: 'Codierung',
  actuator: 'Stellglieddiagnose',
  flash: 'Programmierung',
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
    </Panel>
  )
}
