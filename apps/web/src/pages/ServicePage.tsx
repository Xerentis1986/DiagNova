import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ServiceProcedure, type ServiceRun } from '../lib/api'
import { Badge, Button, Dialog, PageHeader, Panel, SectionTitle } from '../components/ui'

type Scenario = 'normal' | 'missing_prereq' | 'abort' | 'comm_loss'

function statusTone(status: string): 'ok' | 'warn' | 'danger' | 'default' | 'accent' {
  if (status === 'completed') return 'ok'
  if (status === 'blocked' || status === 'running') return 'warn'
  if (status === 'failed' || status === 'aborted') return 'danger'
  return 'default'
}

export function ServicePage() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<ServiceProcedure | null>(null)
  const [scenario, setScenario] = useState<Scenario>('normal')
  const [phrase, setPhrase] = useState('')
  const [ackDisabled, setAckDisabled] = useState(false)
  const [ackNoWrite, setAckNoWrite] = useState(false)
  const [operatorOk, setOperatorOk] = useState(false)
  const [oemOk, setOemOk] = useState(false)
  const [lastRun, setLastRun] = useState<ServiceRun | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const catalogQ = useQuery({ queryKey: ['service-catalog'], queryFn: () => api.serviceCatalog() })
  const runsQ = useQuery({ queryKey: ['service-runs'], queryFn: () => api.serviceRuns() })
  const vehiclesQ = useQuery({ queryKey: ['vehicles'], queryFn: () => api.vehicles() })
  const vehicleId = vehiclesQ.data?.[0]?.id

  const startMut = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error('Keine Prozedur gewählt')
      return api.startServiceRun(selected.code, {
        vehicle_id: vehicleId,
        confirmation_phrase: phrase || selected.confirmation_phrase,
        scenario,
        acknowledge_disabled: ackDisabled,
        acknowledge_no_oem_write: ackNoWrite,
        vehicle_state: {
          ignition_on: true,
          adapter_connected: scenario !== 'missing_prereq',
          battery_voltage_ok: true,
          operator_confirm: operatorOk,
          oem_spec_present: oemOk,
          safe_work_area: true,
          exhaust_safe: true,
        },
      })
    },
    onSuccess: (run) => {
      setLastRun(run)
      setMsg(run.message_de)
      setErr(null)
      void qc.invalidateQueries({ queryKey: ['service-runs'] })
    },
    onError: (e: Error) => {
      setErr(e.message)
      setMsg(null)
    },
  })

  const abortMut = useMutation({
    mutationFn: (id: string) => api.abortServiceRun(id, 'UI-Abbruch'),
    onSuccess: (run) => {
      setLastRun(run)
      setMsg(run.message_de)
      void qc.invalidateQueries({ queryKey: ['service-runs'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  const liveMut = useMutation({
    mutationFn: (code: string) => api.executeServiceLive(code),
    onError: (e: Error) => setErr(e.message),
    onSuccess: () => setMsg('Unerwartet: Live freigegeben – bitte prüfen'),
  })

  const procedures = catalogQ.data?.procedures ?? []
  const excluded = catalogQ.data?.excluded ?? []
  const byCategory = useMemo(() => {
    const map = new Map<string, ServiceProcedure[]>()
    for (const p of procedures) {
      const list = map.get(p.category) || []
      list.push(p)
      map.set(p.category, list)
    }
    return [...map.entries()]
  }, [procedures])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Servicefunktionen"
        description="Katalog mit Specs, Voraussetzungen und Safety-Gates. Keine erfundenen OEM-Schreibprozeduren. DPF-Off ausgeschlossen."
        actions={
          <Link className="dn-btn dn-btn--secondary" to="/guided">
            Geführte Diagnose
          </Link>
        }
      />

      <Panel>
        <p className="text-sm text-[var(--dn-muted)]">{catalogQ.data?.disclaimer_de}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge tone="warn">Live-Schreiben: aus</Badge>
          <Badge>Hardware: nicht freigegeben</Badge>
          <Badge tone="danger">DPF-Off: ausgeschlossen</Badge>
        </div>
      </Panel>

      {catalogQ.isLoading && <p className="text-sm text-[var(--dn-muted)]">Katalog laden…</p>}
      {catalogQ.error && (
        <p className="text-sm text-[var(--dn-danger)]">
          {catalogQ.error instanceof Error ? catalogQ.error.message : 'Fehler'}
        </p>
      )}

      {byCategory.map(([cat, items]) => (
        <Panel key={cat}>
          <SectionTitle>{cat}</SectionTitle>
          <ul className="mt-3 divide-y divide-[var(--dn-border)]">
            {items.map((p) => (
              <li key={p.code} className="flex flex-wrap items-start justify-between gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-[var(--dn-text)]">{p.name_de}</div>
                  <div className="mt-1 flex flex-wrap gap-2">
                    <Badge tone={p.safety_class === 'safety_critical' ? 'danger' : 'warn'}>
                      {p.safety_class}
                    </Badge>
                    <Badge>{p.release_status}</Badge>
                    {!p.enabled && <Badge tone="warn">deaktiviert</Badge>}
                  </div>
                  <p className="mt-2 text-xs text-[var(--dn-muted)]">{p.notes_de}</p>
                  <p className="mt-1 text-xs text-[var(--dn-muted)]">{p.compatibility_de}</p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSelected(p)
                    setPhrase(p.confirmation_phrase || '')
                    setAckDisabled(p.release_status === 'disabled')
                    setAckNoWrite(true)
                    setScenario('normal')
                    setErr(null)
                    setMsg(null)
                  }}
                >
                  Details / Gate-Test
                </Button>
              </li>
            ))}
          </ul>
        </Panel>
      ))}

      {excluded.length > 0 && (
        <Panel>
          <SectionTitle>Ausgeschlossen</SectionTitle>
          <ul className="mt-2 space-y-2">
            {excluded.map((e) => (
              <li key={e.code} className="text-sm">
                <Badge tone="danger">{e.code}</Badge>{' '}
                <span className="text-[var(--dn-text)]">{e.name_de}</span>
                {e.reason_de && <p className="mt-1 text-xs text-[var(--dn-muted)]">{e.reason_de}</p>}
              </li>
            ))}
          </ul>
        </Panel>
      )}

      {lastRun && (
        <Panel>
          <SectionTitle>Letzter Lauf</SectionTitle>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge tone={statusTone(lastRun.status)}>{lastRun.status}</Badge>
            <span className="text-sm text-[var(--dn-muted)]">{lastRun.procedure_code}</span>
            <Badge>writes: {String(lastRun.write_commands_sent)}</Badge>
          </div>
          {lastRun.message_de && <p className="mt-2 text-sm text-[var(--dn-muted)]">{lastRun.message_de}</p>}
          <ul className="mt-3 space-y-1 text-xs text-[var(--dn-muted)]">
            {lastRun.prerequisites.map((p) => (
              <li key={p.id}>
                {p.met ? '✓' : '✗'} {p.label_de}
              </li>
            ))}
          </ul>
          {lastRun.status === 'running' && (
            <Button className="mt-3" variant="danger" onClick={() => abortMut.mutate(lastRun.id)}>
              Abbrechen
            </Button>
          )}
        </Panel>
      )}

      <Panel>
        <SectionTitle>Audit-Läufe</SectionTitle>
        <ul className="mt-2 divide-y divide-[var(--dn-border)] text-sm">
          {(runsQ.data ?? []).slice(0, 12).map((r) => (
            <li key={r.id} className="flex flex-wrap justify-between gap-2 py-2">
              <span>
                {r.procedure_code} · {r.scenario || '—'}
              </span>
              <Badge tone={statusTone(r.status)}>{r.status}</Badge>
            </li>
          ))}
          {!runsQ.data?.length && (
            <li className="py-2 text-[var(--dn-muted)]">Noch keine Gate-Läufe.</li>
          )}
        </ul>
      </Panel>

      {(msg || err) && (
        <p className={`text-sm ${err ? 'text-[var(--dn-danger)]' : 'text-[var(--dn-muted)]'}`}>{err || msg}</p>
      )}

      <Dialog
        open={!!selected}
        title={selected?.name_de || 'Prozedur'}
        onClose={() => setSelected(null)}
        danger={selected?.safety_class === 'safety_critical'}
        actions={
          <>
            <Button variant="secondary" onClick={() => setSelected(null)}>
              Schließen
            </Button>
            <Button
              variant="secondary"
              onClick={() => selected && liveMut.mutate(selected.code)}
              disabled={liveMut.isPending}
            >
              Live versuchen (erwartet 403)
            </Button>
            <Button onClick={() => startMut.mutate()} disabled={startMut.isPending || !selected}>
              Gate-Simulation starten
            </Button>
          </>
        }
      >
        {selected && (
          <div className="space-y-3 text-sm">
            <p className="text-[var(--dn-muted)]">{selected.source_license_de}</p>
            <p>
              <strong>Abbruch:</strong> {selected.abort_strategy_de}
            </p>
            <p>
              <strong>Timeout:</strong> {selected.timeout_seconds}s
            </p>
            <ul className="list-disc pl-5 text-[var(--dn-muted)]">
              {selected.prerequisites.map((p) => (
                <li key={p.id}>{p.label_de}</li>
              ))}
            </ul>
            <label className="block">
              Szenario
              <select
                className="dn-input mt-1 w-full"
                value={scenario}
                onChange={(e) => setScenario(e.target.value as Scenario)}
              >
                <option value="normal">normal (Gates OK)</option>
                <option value="missing_prereq">fehlende Voraussetzungen</option>
                <option value="abort">Abbruch vorbereiten</option>
                <option value="comm_loss">Kommunikationsverlust</option>
              </select>
            </label>
            {selected.confirmation_phrase && (
              <label className="block">
                Bestätigungsphrase
                <input
                  className="dn-input mt-1 w-full"
                  value={phrase}
                  onChange={(e) => setPhrase(e.target.value)}
                />
              </label>
            )}
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={operatorOk} onChange={(e) => setOperatorOk(e.target.checked)} />
              Fachkraft bestätigt Kompatibilität
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={oemOk} onChange={(e) => setOemOk(e.target.checked)} />
              OEM-Spezifikation vorhanden (simuliert)
            </label>
            {selected.release_status === 'disabled' && (
              <>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={ackDisabled}
                    onChange={(e) => setAckDisabled(e.target.checked)}
                  />
                  Ohne Freigabe deaktiviert – nur Gate-Test
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={ackNoWrite}
                    onChange={(e) => setAckNoWrite(e.target.checked)}
                  />
                  Keine OEM-Schreibbefehle
                </label>
              </>
            )}
          </div>
        )}
      </Dialog>
    </div>
  )
}
