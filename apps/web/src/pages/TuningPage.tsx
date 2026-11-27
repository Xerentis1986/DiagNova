import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  api,
  type LegalGateCheck,
  type TuningOperation,
  type TuningRun,
} from '../lib/api'
import { Badge, Button, Dialog, PageHeader, Panel, SectionTitle } from '../components/ui'

type Scenario = 'normal' | 'missing_prereq' | 'missing_legal' | 'abort' | 'comm_loss' | 'wrong_vehicle'

function statusTone(status: string): 'ok' | 'warn' | 'danger' | 'default' | 'accent' {
  if (status === 'completed') return 'ok'
  if (status === 'blocked' || status === 'running') return 'warn'
  if (status === 'failed' || status === 'aborted') return 'danger'
  return 'default'
}

export function TuningPage() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<TuningOperation | null>(null)
  const [scenario, setScenario] = useState<Scenario>('normal')
  const [phrase, setPhrase] = useState('')
  const [ackDisabled, setAckDisabled] = useState(false)
  const [ackNoMap, setAckNoMap] = useState(false)
  const [ackNoEmission, setAckNoEmission] = useState(false)
  const [ackLocked, setAckLocked] = useState(false)
  const [operatorOk, setOperatorOk] = useState(false)
  const [legalAck, setLegalAck] = useState(false)
  const [legalPresent, setLegalPresent] = useState(false)
  const [techOk, setTechOk] = useState(false)
  const [recoveryOk, setRecoveryOk] = useState(false)
  const [oemOk, setOemOk] = useState(false)
  const [hwOk, setHwOk] = useState(false)
  const [lastRun, setLastRun] = useState<TuningRun | null>(null)
  const [gates, setGates] = useState<LegalGateCheck | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [baselineCode, setBaselineCode] = useState('UI-BASELINE-1.0.0')
  const [approvalTitle, setApprovalTitle] = useState('Demo-Genehmigungsnachweis')

  const statusQ = useQuery({ queryKey: ['tuning-status'], queryFn: () => api.tuningStatus() })
  const catalogQ = useQuery({ queryKey: ['tuning-catalog'], queryFn: () => api.tuningCatalog() })
  const baselinesQ = useQuery({ queryKey: ['tuning-baselines'], queryFn: () => api.tuningBaselines() })
  const approvalsQ = useQuery({ queryKey: ['tuning-approvals'], queryFn: () => api.tuningApprovals() })
  const historyQ = useQuery({ queryKey: ['tuning-history'], queryFn: () => api.tuningHistory() })
  const runsQ = useQuery({ queryKey: ['tuning-runs'], queryFn: () => api.tuningRuns() })

  const startMut = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error('Keine Operation gewählt')
      return api.startTuningRun(selected.code, {
        confirmation_phrase: phrase || selected.confirmation_phrase,
        scenario,
        acknowledge_disabled: ackDisabled,
        acknowledge_no_map_change: ackNoMap,
        acknowledge_no_emission_defeat: ackNoEmission,
        acknowledge_activation_locked: ackLocked,
        gate_state: {
          operator_confirm: operatorOk,
          legal_gate_ack: legalAck,
          no_emission_defeat_ack: ackNoEmission,
          no_map_change_ack: ackNoMap,
          legal_approval_present: legalPresent,
          technical_review_present: techOk,
          recovery_plan: recoveryOk,
          oem_baseline_documented: oemOk,
          hardware_suitable: hwOk,
        },
      })
    },
    onSuccess: (run) => {
      setLastRun(run)
      setMsg(run.message_de)
      setErr(null)
      void qc.invalidateQueries({ queryKey: ['tuning-runs'] })
    },
    onError: (e: Error) => {
      setErr(e.message)
      setMsg(null)
    },
  })

  const abortMut = useMutation({
    mutationFn: (id: string) => api.abortTuningRun(id, 'UI-Abbruch'),
    onSuccess: (run) => {
      setLastRun(run)
      setMsg(run.message_de)
      void qc.invalidateQueries({ queryKey: ['tuning-runs'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  const gateMut = useMutation({
    mutationFn: () =>
      api.tuningLegalGates({
        operator_confirm: operatorOk,
        legal_gate_ack: legalAck,
        no_emission_defeat_ack: ackNoEmission,
        no_map_change_ack: ackNoMap,
        legal_approval_present: legalPresent,
        technical_review_present: techOk,
        recovery_plan: recoveryOk,
        oem_baseline_documented: oemOk,
        hardware_suitable: hwOk,
      }),
    onSuccess: (g) => {
      setGates(g)
      setMsg(g.message_de)
      setErr(null)
    },
    onError: (e: Error) => setErr(e.message),
  })

  const baselineMut = useMutation({
    mutationFn: () =>
      api.createTuningBaseline({
        code: baselineCode,
        software_version: '1.0.0',
        source_de: 'UI-Demo: nur Metadaten, keine Map/Binary',
        acknowledge_no_map_binary: true,
        acknowledge_demo_only: true,
      }),
    onSuccess: () => {
      setMsg('Baseline als draft registriert (kein Flash).')
      void qc.invalidateQueries({ queryKey: ['tuning-baselines'] })
      void qc.invalidateQueries({ queryKey: ['tuning-history'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  const approvalMut = useMutation({
    mutationFn: () =>
      api.createTuningApproval({
        baseline_id: baselinesQ.data?.[0]?.id,
        title_de: approvalTitle,
        doc_type: 'workshop_ack',
        acknowledge_not_legal_advice: true,
        acknowledge_no_activation: true,
      }),
    onSuccess: () => {
      setMsg('Genehmigungsnachweis dokumentiert (keine Aktivierung).')
      void qc.invalidateQueries({ queryKey: ['tuning-approvals'] })
      void qc.invalidateQueries({ queryKey: ['tuning-history'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  const catalog = catalogQ.data
  const status = statusQ.data

  return (
    <div className="space-y-6">
      <PageHeader
        title="Chiptuning"
        description="Optionales Modul – nur Architektur, Verwaltung und Gates. Keine Kennfeldänderungen."
      />

      <Panel className="space-y-3 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="warn">Geplant</Badge>
          <Badge tone="danger">Deaktiviert</Badge>
          <Badge>Aktivierung gesperrt</Badge>
          {status && <Badge tone="default">Phase {status.phase}</Badge>}
        </div>
        <p className="text-sm text-[var(--dn-muted)]">
          {status?.disclaimer_de || catalog?.disclaimer_de || 'Modulstatus wird geladen…'}
        </p>
        <ul className="list-inside list-disc text-sm text-[var(--dn-muted)]">
          <li>Keine aktiven Kennfeldänderungen</li>
          <li>Kein Tuning-Flash</li>
          <li>Keine Manipulation von Abgas- oder Sicherheitssystemen</li>
          <li>Produktive Aktivierung standardmäßig gesperrt</li>
        </ul>
      </Panel>

      {err && (
        <Panel className="border-[var(--dn-danger)] p-4 text-sm text-[var(--dn-danger)]">{err}</Panel>
      )}
      {msg && <Panel className="p-4 text-sm text-[var(--dn-muted)]">{msg}</Panel>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel className="space-y-4 p-5">
          <SectionTitle>Autorisierte Softwarestände</SectionTitle>
          <p className="text-xs text-[var(--dn-muted)]">Nur Metadaten – keine Binaries/Maps.</p>
          <div className="flex flex-wrap gap-2">
            <input
              className="dn-input min-w-[12rem] flex-1"
              value={baselineCode}
              onChange={(e) => setBaselineCode(e.target.value)}
              aria-label="Baseline-Code"
            />
            <Button
              type="button"
              onClick={() => baselineMut.mutate()}
              disabled={baselineMut.isPending}
            >
              Registrieren (Demo)
            </Button>
          </div>
          <ul className="max-h-48 space-y-2 overflow-auto text-sm">
            {(baselinesQ.data || []).map((b) => (
              <li key={b.id} className="rounded border border-[var(--dn-border)] px-3 py-2">
                <div className="font-medium">{b.code}</div>
                <div className="text-xs text-[var(--dn-muted)]">
                  {b.ecu_role} · {b.software_version} · {b.authorization_status}
                </div>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel className="space-y-4 p-5">
          <SectionTitle>Genehmigungsnachweise</SectionTitle>
          <p className="text-xs text-[var(--dn-muted)]">Keine Rechtsberatung; aktiviert kein Tuning.</p>
          <div className="flex flex-wrap gap-2">
            <input
              className="dn-input min-w-[12rem] flex-1"
              value={approvalTitle}
              onChange={(e) => setApprovalTitle(e.target.value)}
              aria-label="Genehmigungstitel"
            />
            <Button
              type="button"
              onClick={() => approvalMut.mutate()}
              disabled={approvalMut.isPending || !baselinesQ.data?.length}
            >
              Dokumentieren
            </Button>
          </div>
          <ul className="max-h-48 space-y-2 overflow-auto text-sm">
            {(approvalsQ.data || []).map((a) => (
              <li key={a.id} className="rounded border border-[var(--dn-border)] px-3 py-2">
                <div className="font-medium">{a.title_de}</div>
                <div className="text-xs text-[var(--dn-muted)]">
                  {a.doc_type} · {a.status}
                </div>
              </li>
            ))}
            {!approvalsQ.data?.length && (
              <li className="text-xs text-[var(--dn-muted)]">Noch keine Nachweise.</li>
            )}
          </ul>
        </Panel>
      </div>

      <Panel className="space-y-4 p-5">
        <SectionTitle>Versionshistorie</SectionTitle>
        <ul className="max-h-40 space-y-2 overflow-auto text-sm">
          {(historyQ.data || []).slice(0, 12).map((h) => (
            <li key={h.id} className="border-b border-[var(--dn-border)] pb-2">
              <span className="text-xs uppercase text-[var(--dn-muted)]">{h.event_type}</span>
              <div>
                {h.ecu_role} {h.software_version}
                {h.message_de ? ` – ${h.message_de}` : ''}
              </div>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel className="space-y-4 p-5">
        <SectionTitle>Rechtliche / technische Gates</SectionTitle>
        <div className="grid gap-2 sm:grid-cols-2 text-sm">
          {(
            [
              ['Fachkraft bestätigt', operatorOk, setOperatorOk],
              ['Rechtliche Hinweise bestätigt', legalAck, setLegalAck],
              ['Genehmigung vorhanden', legalPresent, setLegalPresent],
              ['Technische Review', techOk, setTechOk],
              ['Wiederherstellungsplan', recoveryOk, setRecoveryOk],
              ['OEM-Baseline dokumentiert', oemOk, setOemOk],
              ['Hardware geeignet', hwOk, setHwOk],
              ['Keine Kennfeldänderung', ackNoMap, setAckNoMap],
              ['Keine Abgasmanipulation', ackNoEmission, setAckNoEmission],
            ] as const
          ).map(([label, val, set]) => (
            <label key={label} className="flex items-center gap-2">
              <input type="checkbox" checked={val} onChange={(e) => set(e.target.checked)} />
              {label}
            </label>
          ))}
        </div>
        <Button type="button" onClick={() => gateMut.mutate()} disabled={gateMut.isPending}>
          Gates prüfen (Simulation)
        </Button>
        {gates && (
          <div className="rounded border border-[var(--dn-border)] p-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge tone={gates.overall_ok ? 'ok' : 'warn'}>
                {gates.overall_ok ? 'Gates ok (Framework)' : 'Gates unvollständig'}
              </Badge>
              <Badge tone="danger">Map gesperrt</Badge>
              <Badge tone="danger">Flash gesperrt</Badge>
              <Badge tone="danger">Aktivierung gesperrt</Badge>
            </div>
            <p className="mt-2 text-[var(--dn-muted)]">{gates.message_de}</p>
            {gates.blockers.length > 0 && (
              <p className="mt-1 text-xs text-[var(--dn-muted)]">
                Blocker: {gates.blockers.join(', ')}
              </p>
            )}
          </div>
        )}
      </Panel>

      <Panel className="space-y-4 p-5">
        <SectionTitle>Katalog & simulierte Workflows</SectionTitle>
        <div className="grid gap-2 sm:grid-cols-2">
          {(catalog?.operations || []).map((op) => (
            <button
              key={op.code}
              type="button"
              className="rounded border border-[var(--dn-border)] px-3 py-2 text-left text-sm hover:border-[var(--dn-accent)]"
              onClick={() => {
                setSelected(op)
                setPhrase(op.confirmation_phrase || '')
                setErr(null)
              }}
            >
              <div className="font-medium">{op.name_de}</div>
              <div className="text-xs text-[var(--dn-muted)]">
                {op.category} · {op.release_status} · deaktiviert
              </div>
            </button>
          ))}
        </div>
        {catalog?.excluded && catalog.excluded.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-medium">Ausgeschlossen</h3>
            <ul className="space-y-1 text-xs text-[var(--dn-muted)]">
              {catalog.excluded.map((ex) => (
                <li key={ex.code}>
                  <strong>{ex.name_de}</strong>: {ex.reason_de}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Panel>

      <Panel className="space-y-3 p-5">
        <SectionTitle>Letzte Läufe</SectionTitle>
        <ul className="space-y-2 text-sm">
          {(runsQ.data || []).slice(0, 8).map((r) => (
            <li key={r.id} className="flex flex-wrap items-center gap-2">
              <Badge tone={statusTone(r.status)}>{r.status}</Badge>
              <span>{r.operation_code}</span>
              <span className="text-xs text-[var(--dn-muted)]">
                map={String(r.map_commands_sent)} flash={String(r.flash_commands_sent)} aktiv=
                {String(r.tuning_activated)}
              </span>
            </li>
          ))}
          {!runsQ.data?.length && (
            <li className="text-xs text-[var(--dn-muted)]">Noch keine Simulationsläufe.</li>
          )}
        </ul>
        {lastRun?.status === 'running' && (
          <Button type="button" onClick={() => abortMut.mutate(lastRun.id)}>
            Lauf abbrechen
          </Button>
        )}
      </Panel>

      <Dialog
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.name_de || 'Operation'}
      >
        {selected && (
          <div className="space-y-3 text-sm">
            <p className="text-[var(--dn-muted)]">{selected.notes_de}</p>
            <Badge tone="warn">Geplant / deaktiviert</Badge>
            <label className="block">
              Szenario
              <select
                className="dn-input mt-1 w-full"
                value={scenario}
                onChange={(e) => setScenario(e.target.value as Scenario)}
              >
                <option value="normal">normal</option>
                <option value="missing_prereq">missing_prereq</option>
                <option value="missing_legal">missing_legal</option>
                <option value="abort">abort</option>
                <option value="comm_loss">comm_loss</option>
                <option value="wrong_vehicle">wrong_vehicle</option>
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
              <input
                type="checkbox"
                checked={ackDisabled}
                onChange={(e) => setAckDisabled(e.target.checked)}
              />
              Modul geplant/deaktiviert bestätigt
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={ackLocked}
                onChange={(e) => setAckLocked(e.target.checked)}
              />
              Produktive Aktivierung gesperrt bestätigt
            </label>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                onClick={() => startMut.mutate()}
                disabled={startMut.isPending}
              >
                Simulation starten
              </Button>
              <Button type="button" variant="secondary" onClick={() => setSelected(null)}>
                Schließen
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  )
}
