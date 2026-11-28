import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Badge, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'

export function LkwPage() {
  const archQ = useQuery({
    queryKey: ['lkw-architecture'],
    queryFn: () => api.lkwArchitecture(),
  })
  const brandsQ = useQuery({
    queryKey: ['lkw-brands'],
    queryFn: () => api.lkwBrands(),
  })
  const capsQ = useQuery({
    queryKey: ['lkw-capabilities'],
    queryFn: () => api.lkwCapabilities(),
  })

  const arch = archQ.data
  const brands = brandsQ.data?.brands ?? []
  const flags = capsQ.data?.flags ?? []

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="LKW / Nutzfahrzeug"
        description="Architekturvorbereitung Phase 19 – keine freigegebene Diagnose."
      />

      <Panel className="space-y-3 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="warn">Geplant</Badge>
          <Badge>Architektur only</Badge>
          <Badge>J1939 / RP1210 Prep</Badge>
        </div>
        <p className="text-sm text-[var(--dn-muted)]">
          {arch?.summary_de ??
            'LKW-Diagnose ist nicht freigegeben. PKW-OBD-Adapter ersetzen J1939/RP1210 nicht.'}
        </p>
        <p className="text-sm text-[var(--dn-muted)]">
          Keine vorgetäuschten LKW-Messwerte, kein Parser, keine RP1210-DLL-Bindung. Diagnose-Endpunkte
          antworten mit 403.
        </p>
        {arch && (
          <ul className="mt-2 list-inside list-disc text-sm text-[var(--dn-muted)]">
            <li>Scope: {arch.scope}</li>
            <li>Status: {arch.status}</li>
            <li>Entitlement vehicle.lkw: {arch.entitlement_granted ? 'ja' : 'nicht freigegeben'}</li>
            <li>Blocker: {(arch.blockers ?? []).join(', ') || '—'}</li>
          </ul>
        )}
      </Panel>

      <Panel className="p-6">
        <SectionTitle>Markenkatalog (Navigation)</SectionTitle>
        <p className="mb-4 text-sm text-[var(--dn-muted)]">
          {brandsQ.data?.disclaimer_de ??
            'Katalogeintrag bedeutet keine Diagnoseabdeckung.'}
        </p>
        {brandsQ.isLoading && <p className="text-sm text-[var(--dn-muted)]">Laden…</p>}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {brands.map((b) => (
            <div
              key={b.slug}
              className="rounded-md border border-dashed border-[var(--dn-border)] p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-lg font-semibold tracking-tight">{b.name}</div>
                  <div className="text-xs text-[var(--dn-muted)]">{b.group}</div>
                </div>
                <Badge tone="warn">Geplant</Badge>
              </div>
              <p className="mt-2 text-xs text-[var(--dn-muted)]">{b.voltage_note_de}</p>
              {b.example_models_nav_only.length > 0 && (
                <p className="mt-2 text-xs text-[var(--dn-muted)]">
                  Beispiele (nur Nav): {b.example_models_nav_only.join(', ')}
                </p>
              )}
              <p className="mt-2 text-[11px] uppercase tracking-wide text-[var(--dn-muted)]">
                Diagnose: nicht verfügbar
              </p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel className="p-6">
        <SectionTitle>Capability-Flags</SectionTitle>
        <p className="mb-4 text-sm text-[var(--dn-muted)]">
          {capsQ.data?.disclaimer_de ?? 'Alle Flags deaktiviert.'}
        </p>
        <ul className="divide-y divide-[var(--dn-border)]">
          {flags.map((f) => (
            <li key={f.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
              <div>
                <div className="font-medium">{f.label_de}</div>
                {f.notes_de && (
                  <div className="text-xs text-[var(--dn-muted)]">{f.notes_de}</div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="warn">{f.status}</Badge>
                <Badge tone="danger">aus</Badge>
              </div>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel className="p-6 text-sm text-[var(--dn-muted)]">
        <SectionTitle>Weiter</SectionTitle>
        <p className="mt-2">
          Tarife <code>lkw_planned</code> / <code>kombi_planned</code> sind nicht buchbar.{' '}
          <Link className="text-[var(--dn-accent)] underline" to="/subscriptions">
            Abos &amp; Lizenzen
          </Link>
          {' · '}
          <Link className="text-[var(--dn-accent)] underline" to="/planned/lkw">
            Platzhalter „Geplant“
          </Link>
        </p>
      </Panel>
    </div>
  )
}
