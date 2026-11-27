import { useParams } from 'react-router-dom'

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
    <div className="dn-panel mx-auto max-w-2xl p-8 text-center">
      <span className="rounded bg-slate-700 px-2 py-1 text-xs uppercase tracking-wide text-slate-300">
        Geplant
      </span>
      <h1 className="mt-4 text-2xl font-semibold text-blue-100">{label}</h1>
      <p className="mt-3 text-sm text-slate-400">
        Dieses Modul ist für eine spätere Phase vorgesehen und im MVP nicht verfügbar. Es handelt sich um keine
        fertige Funktion und um keine echte Fahrzeugdiagnose.
      </p>
    </div>
  )
}
