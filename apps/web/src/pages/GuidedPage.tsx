import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Badge, Button, PageHeader, Panel, SectionTitle } from '../components/ui'

export function GuidedPage() {
  const [dtcCode, setDtcCode] = useState('P0420')
  const [lookup, setLookup] = useState('P0420')
  const [groupId, setGroupId] = useState('engine_basic')

  const overviewQ = useQuery({ queryKey: ['guided-overview'], queryFn: () => api.guidedOverview() })
  const vehiclesQ = useQuery({ queryKey: ['vehicles'], queryFn: () => api.vehicles() })
  const vehicleId = vehiclesQ.data?.[0]?.id

  const dtcQ = useQuery({
    queryKey: ['dtc-help', lookup],
    queryFn: () => api.dtcHelp(lookup),
    enabled: !!lookup,
  })

  const groupQ = useQuery({
    queryKey: ['meas-group', groupId, vehicleId],
    queryFn: () => api.measurementGroup(groupId, vehicleId!),
    enabled: !!vehicleId && !!groupId,
    refetchInterval: 3000,
  })

  const categories = useMemo(() => {
    const raw = overviewQ.data?.ecu_summary?.categories
    return Array.isArray(raw) ? (raw as { id?: string; label_de?: string; availability?: string; notes_de?: string }[]) : []
  }, [overviewQ.data])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Geführte Diagnose"
        description="ECU-Überblick, Messwertgruppen und DTC-Hilfe. Keine automatische Reparaturdiagnose."
        actions={
          <Link className="dn-btn dn-btn--secondary" to="/service">
            Servicekatalog
          </Link>
        }
      />

      <Panel>
        <p className="text-sm text-[var(--dn-muted)]">{overviewQ.data?.disclaimer_de}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge>data_source: {overviewQ.data?.data_source ?? '…'}</Badge>
          <Badge tone="warn">Blindscan: aus</Badge>
        </div>
      </Panel>

      <Panel>
        <SectionTitle>ECU-Übersicht</SectionTitle>
        <p className="mt-2 text-xs text-[var(--dn-muted)]">
          {(overviewQ.data?.ecu_summary?.read_policy_de as string) ||
            'Lesende Identifikation zuerst. Schreiben gesperrt.'}
        </p>
        <ul className="mt-3 space-y-2">
          {categories.map((c) => (
            <li key={c.id || c.label_de} className="border-b border-[var(--dn-border)] py-2 text-sm">
              <span className="text-[var(--dn-text)]">{c.label_de}</span>
              <span className="ml-2 text-xs text-[var(--dn-muted)]">{c.availability}</span>
              {c.notes_de && <p className="mt-1 text-xs text-[var(--dn-muted)]">{c.notes_de}</p>}
            </li>
          ))}
          {!categories.length && !overviewQ.isLoading && (
            <li className="text-sm text-[var(--dn-muted)]">
              Keine Kategorien – siehe auch{' '}
              <Link className="text-[var(--dn-accent)] underline" to="/ecu">
                Steuergeräte
              </Link>
              .
            </li>
          )}
        </ul>
      </Panel>

      <Panel>
        <SectionTitle>Messwertgruppen</SectionTitle>
        <div className="mt-3 flex flex-wrap gap-2">
          {(overviewQ.data?.measurement_groups ?? []).map((g) => (
            <Button
              key={g.id}
              variant={groupId === g.id ? 'primary' : 'secondary'}
              onClick={() => setGroupId(g.id)}
            >
              {g.label_de}
            </Button>
          ))}
        </div>
        {groupQ.data && (
          <div className="mt-4">
            <p className="text-xs text-[var(--dn-muted)]">{groupQ.data.message_de}</p>
            <ul className="mt-2 grid gap-2 sm:grid-cols-2">
              {groupQ.data.readings.map((r) => (
                <li
                  key={r.name}
                  className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm"
                >
                  <div className="text-[var(--dn-muted)]">{r.name}</div>
                  <div className="text-lg font-medium text-[var(--dn-text)]">
                    {typeof r.value === 'number' ? r.value.toFixed(1) : r.value}
                    {r.unit ? ` ${r.unit}` : ''}
                  </div>
                </li>
              ))}
              {!groupQ.data.readings.length && (
                <li className="text-sm text-[var(--dn-muted)]">Keine belegten PIDs in dieser Gruppe.</li>
              )}
            </ul>
          </div>
        )}
        {!vehicleId && (
          <p className="mt-3 text-sm text-[var(--dn-muted)]">
            Kein Fahrzeug – bitte unter{' '}
            <Link className="underline" to="/">
              Fahrzeugauswahl
            </Link>{' '}
            bestätigen.
          </p>
        )}
      </Panel>

      <Panel>
        <SectionTitle>DTC-Hilfe</SectionTitle>
        <form
          className="mt-3 flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setLookup(dtcCode.trim().toUpperCase())
          }}
        >
          <input
            className="dn-input"
            value={dtcCode}
            onChange={(e) => setDtcCode(e.target.value)}
            placeholder="z. B. P0301"
            aria-label="DTC-Code"
          />
          <Button type="submit">Nachschlagen</Button>
        </form>
        {dtcQ.data && (
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge tone="accent">{dtcQ.data.code}</Badge>
              <Badge tone={dtcQ.data.description_status === 'unknown' ? 'warn' : 'ok'}>
                {dtcQ.data.description_status}
              </Badge>
              <Badge>{dtcQ.data.data_source}</Badge>
              {dtcQ.data.repair_auto_generated === false && <Badge>keine Auto-Reparatur</Badge>}
            </div>
            <p className="text-[var(--dn-text)]">
              {dtcQ.data.description_de || 'Unbekannt – keine Beschreibung erfunden.'}
            </p>
            <p className="text-xs text-[var(--dn-muted)]">{dtcQ.data.help_de}</p>
          </div>
        )}
      </Panel>
    </div>
  )
}
