import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  api,
  type CodingOperation,
  type CodingRun,
  type CompatibilityCheck,
} from '../lib/api'
import { Badge, Button, Dialog, PageHeader, Panel, SectionTitle } from '../components/ui'

type Scenario =
  | 'normal'
  | 'missing_prereq'
  | 'abort'
  | 'comm_loss'
  | 'voltage_drop'
  | 'wrong_vehicle'

function statusTone(status: string): 'ok' | 'warn' | 'danger' | 'default' | 'accent' {
  if (status === 'completed') return 'ok'
  if (status === 'blocked' || status === 'running') return 'warn'
  if (status === 'failed' || status === 'aborted') return 'danger'
  return 'default'
}

export function CodingPage() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<CodingOperation | null>(null)
  const [scenario, setScenario] = useState<Scenario>('normal')
  const [phrase, setPhrase] = useState('')
  const [ackDisabled, setAckDisabled] = useState(false)
  const [ackNoWrite, setAckNoWrite] = useState(false)
  const [ackNoFlash, setAckNoFlash] = useState(false)
  const [operatorOk, setOperatorOk] = useState(false)
  const [oemOk, setOemOk] = useState(false)
  const [authOk, setAuthOk] = useState(false)
  const [recoveryOk, setRecoveryOk] = useState(false)
  const [lastRun, setLastRun] = useState<CodingRun | null>(null)
  const [compat, setCompat] = useState<CompatibilityCheck | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const catalogQ = useQuery({ queryKey: ['coding-catalog'], queryFn: () => api.codingCatalog() })
  const runsQ = useQuery({ queryKey: ['coding-runs'], queryFn: () => api.codingRuns() })
  const vehiclesQ = useQuery({ queryKey: ['vehicles'], queryFn: () => api.vehicles() })
  const interfacesQ = useQuery({ queryKey: ['coding-interfaces'], queryFn: () => api.codingInterfaces() })
  const vehicleId = vehiclesQ.data?.[0]?.id

  const identifyQ = useQuery({
    queryKey: ['coding-identify', vehicleId],
    queryFn: () => api.codingIdentify(vehicleId),
    enabled: !!vehicleId || vehicleId === undefined,
  })

  const startMut = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error('Keine Operation gewählt')
      return api.startCodingRun(selected.code, {
        vehicle_id: vehicleId,
        confirmation_phrase: phrase || selected.confirmation_phrase,
        scenario,
        acknowledge_disabled: ackDisabled,
        acknowledge_no_oem_write: ackNoWrite,
        acknowledge_no_flash: ackNoFlash,
        vehicle_state: {
          ignition_on: true,
          adapter_connected: scenario !== 'missing_prereq',
          battery_voltage_ok: scenario !== 'voltage_drop',
          battery_voltage_v: scenario === 'voltage_drop' ? 9.5 : 12.6,
          stable_connection: true,
          vin_ecu_match: scenario !== 'wrong_vehicle',
          operator_confirm: operatorOk,
          oem_spec_present: oemOk,
          authorization_present: authOk,
          recovery_plan: recoveryOk,
        },
      })
    },
    onSuccess: (run) => {
      setLastRun(run)
      setMsg(run.message_de)
      setErr(null)
      void qc.invalidateQueries({ queryKey: ['coding-runs'] })
    },
    onError: (e: Error) => {
      setErr(e.message)
      setMsg(null)
    },
  })

  const abortMut = useMutation({
    mutationFn: (id: string) => api.abortCodingRun(id, 'UI-Abbruch'),
    onSuccess: (run) => {
      setLastRun(run)
      setMsg(run.message_de)
      void qc.invalidateQueries({ queryKey: ['coding-runs'] })
    },
    onError: (e: Error) => setErr(e.message),
  })

  const liveMut = useMutation({
    mutationFn: (code: string) => api.executeCodingLive(code),
    onError: (e: Error) => setErr(e.message),
    onSuccess: () => setMsg('Unerwartet: Live freigegeben – bitte prüfen'),
  })

  const flashMut = useMutation({
    mutationFn: (code: string) => api.executeCodingFlash(code),
    onError: (e: Error) => setErr(e.message),
    onSuccess: () => setMsg('Unerwartet: Flash freigegeben – bitte prüfen'),
  })

  const compatMut = useMutation({
    mutationFn: () =>
      api.codingCompatibilityCheck({
        ignition_on: true,
        adapter_connected: true,
        battery_voltage_ok: true,
        battery_voltage_v: 12.6,
        stable_connection: true,
        vin_ecu_match: true,
        oem_spec_present: oemOk,
        authorization_present: authOk,
        recovery_plan: recoveryOk,
        operator_confirm: operatorOk,
      }),
    onSuccess: (c) => {
      setCompat(c)
      setMsg(c.message_de)
      setErr(null)
    },
    onError: (e: Error) => setErr(e.message),
  })

  const operations = catalogQ.data?.operations ?? []
  const excluded = catalogQ.data?.excluded ?? []
  const byCategory = useMemo(() => {
    const map = new Map<string, CodingOperation[]>()
    for (const o of operations) {
      const list = map.get(o.category) || []
      list.push(o)
      map.set(o.category, list)
    }
    return [...map.entries()]
  }, [operations])

  const ident = identifyQ.data

  return (
    <div className="space-y-6">
      <PageHeader
        title="Codierung & Programmierung"
        description="Identifikation, Spannungs-/Kompatibilitäts-Gates und J2534/D-PDU-Prep. Codierung/Flash ohne Spec und Berechtigung DEAKTIVIERT. Keine echten Flash-Routinen."
        actions={
          <Link className="dn-btn dn-btn--secondary" to="/service">
            Servicefunktionen
          </Link>
        }
      />

      <Panel>
        <p className="text-sm text-[var(--dn-muted)]">{catalogQ.data?.disclaimer_de}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge tone="warn">Schreiben: aus</Badge>
          <Badge tone="danger">Flash: aus</Badge>
          <Badge>Auto-Retry: verboten</Badge>
          <Badge>J2534: {catalogQ.data?.j2534_status || 'prep'}</Badge>
          <Badge>Hardware: nicht freigegeben</Badge>
        </div>
      </Panel>

      <Panel>
        <SectionTitle>ECU-Identifikation (lesend)</SectionTitle>
        {identifyQ.isLoading && <p className="mt-2 text-sm text-[var(--dn-muted)]">Laden…</p>}
        {ident && (
          <div className="mt-3 space-y-2 text-sm">
            <p className="text-xs text-[var(--dn-muted)]">{ident.disclaimer_de}</p>
            <div className="flex flex-wrap gap-2">
              <Badge>Quelle: {ident.data_source}</Badge>
              <Badge tone={ident.oem_fields_available ? 'ok' : 'warn'}>
                OEM-Felder: {ident.oem_fields_available ? 'ja' : 'nein'}
              </Badge>
              <Badge tone="warn">Profil: {ident.coding_profile_status}</Badge>
            </div>
            <ul className="mt-2 space-y-1 text-[var(--dn-muted)]">
              <li>VIN: {ident.vin || '—'}</li>
              <li>ECU: {ident.ecu_id || '—'}</li>
              <li>SW: {ident.software_version || '—'}</li>
              <li>Teilenummer: {ident.part_number || 'nicht belegt'}</li>
              <li>Codierprofil: {ident.coding_profile || 'nicht verfügbar'}</li>
            </ul>
            <p className="text-xs text-[var(--dn-muted)]">{ident.message_de}</p>
          </div>
        )}
      </Panel>

      <Panel>
        <SectionTitle>Spannung & Kompatibilität (Framework)</SectionTitle>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={oemOk} onChange={(e) => setOemOk(e.target.checked)} />
            OEM-Spec
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={authOk} onChange={(e) => setAuthOk(e.target.checked)} />
            Berechtigung
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={recoveryOk} onChange={(e) => setRecoveryOk(e.target.checked)} />
            Wiederherstellungsplan
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={operatorOk} onChange={(e) => setOperatorOk(e.target.checked)} />
            Fachkraft
          </label>
          <Button variant="secondary" onClick={() => compatMut.mutate()} disabled={compatMut.isPending}>
            Prüfung simulieren
          </Button>
        </div>
        {compat && (
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge tone={compat.overall_ok ? 'ok' : 'warn'}>
                overall: {String(compat.overall_ok)}
              </Badge>
              <Badge tone={compat.voltage_ok ? 'ok' : 'danger'}>
                U={compat.voltage_v ?? '—'}V
              </Badge>
              <Badge tone={compat.flash_blocked ? 'danger' : 'ok'}>Flash blocked</Badge>
            </div>
            {compat.blockers.length > 0 && (
              <p className="text-xs text-[var(--dn-muted)]">Blocker: {compat.blockers.join(', ')}</p>
            )}
            <p className="text-xs text-[var(--dn-muted)]">{compat.message_de}</p>
          </div>
        )}
      </Panel>

      <Panel>
        <SectionTitle>Schnittstellen J2534 / D-PDU</SectionTitle>
        {interfacesQ.data && (
          <div className="mt-2 space-y-2 text-sm text-[var(--dn-muted)]">
            <div className="flex flex-wrap gap-2">
              <Badge>J2534: {interfacesQ.data.j2534_status}</Badge>
              <Badge>D-PDU: {interfacesQ.data.dpdu_status}</Badge>
              <Badge tone={interfacesQ.data.vendor_dll_present ? 'ok' : 'warn'}>
                Vendor-DLL: {String(interfacesQ.data.vendor_dll_present)}
              </Badge>
            </div>
            <p className="text-xs">{interfacesQ.data.notes_de}</p>
          </div>
        )}
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
            {items.map((o) => (
              <li key={o.code} className="flex flex-wrap items-start justify-between gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-[var(--dn-text)]">{o.name_de}</div>
                  <div className="mt-1 flex flex-wrap gap-2">
                    <Badge
                      tone={
                        o.safety_class === 'flash_critical' || o.safety_class === 'write_critical'
                          ? 'danger'
                          : 'warn'
                      }
                    >
                      {o.safety_class}
                    </Badge>
                    <Badge>{o.release_status}</Badge>
                    {!o.enabled && <Badge tone="warn">deaktiviert</Badge>}
                    {o.requires_j2534 && <Badge>J2534</Badge>}
                  </div>
                  <p className="mt-2 text-xs text-[var(--dn-muted)]">{o.notes_de}</p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSelected(o)
                    setPhrase(o.confirmation_phrase || '')
                    setAckDisabled(o.release_status === 'disabled')
                    setAckNoWrite(true)
                    setAckNoFlash(true)
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
            <span className="text-sm text-[var(--dn-muted)]">{lastRun.operation_code}</span>
            <Badge>writes: {String(lastRun.write_commands_sent)}</Badge>
            <Badge>flash: {String(lastRun.flash_commands_sent)}</Badge>
            <Badge>retry: {String(lastRun.auto_retry_attempted)}</Badge>
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
                {r.operation_code} · {r.scenario || '—'}
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
        title={selected?.name_de || 'Operation'}
        onClose={() => setSelected(null)}
        danger={
          selected?.safety_class === 'flash_critical' || selected?.safety_class === 'write_critical'
        }
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
              Live versuchen (403)
            </Button>
            <Button
              variant="secondary"
              onClick={() => selected && flashMut.mutate(selected.code)}
              disabled={flashMut.isPending}
            >
              Flash versuchen (403)
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
              <strong>Timeout:</strong> {selected.timeout_seconds}s · Auto-Retry verboten
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
                <option value="wrong_vehicle">falsches Fahrzeug</option>
                <option value="voltage_drop">Spannungsabfall</option>
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
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={ackNoFlash}
                    onChange={(e) => setAckNoFlash(e.target.checked)}
                  />
                  Kein Flash
                </label>
              </>
            )}
          </div>
        )}
      </Dialog>
    </div>
  )
}
