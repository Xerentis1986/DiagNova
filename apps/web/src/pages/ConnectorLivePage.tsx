import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, PageHeader, Panel, SectionTitle } from '../components/ui'
import { api } from '../lib/api'

const CHECK_LS_KEY = 'dn_live_assistant_checks'

type ManualChecks = Record<string, boolean>

function loadManual(): ManualChecks {
  try {
    const raw = localStorage.getItem(CHECK_LS_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as ManualChecks
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

export function ConnectorLivePage() {
  const qc = useQueryClient()
  const [diagMode, setDiagMode] = useState<'demo' | 'live'>(() =>
    (localStorage.getItem('dn_diag_mode') as 'demo' | 'live') || 'live',
  )
  const [manual, setManual] = useState<ManualChecks>(loadManual)

  useEffect(() => {
    localStorage.setItem(CHECK_LS_KEY, JSON.stringify(manual))
  }, [manual])

  const guideQ = useQuery({
    queryKey: ['connector-setup-guide'],
    queryFn: () => api.connectorSetupGuide(),
  })
  const assistantQ = useQuery({
    queryKey: ['connector-live-assistant', diagMode],
    queryFn: () => api.connectorLiveAssistant(diagMode),
    refetchInterval: 8000,
  })

  const setLive = useMutation({
    mutationFn: async () => {
      localStorage.setItem('dn_diag_mode', 'live')
      setDiagMode('live')
      return 'live' as const
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['connector-live-assistant'] })
      void qc.invalidateQueries({ queryKey: ['bridge-status'] })
      void qc.invalidateQueries({ queryKey: ['connection'] })
    },
  })

  const guide = guideQ.data
  const assistant = assistantQ.data
  const installer = guide?.installer ?? assistant?.installer

  const doneCount = useMemo(() => {
    const steps = assistant?.steps ?? []
    return steps.filter((s) => {
      if (s.auto_ok === true) return true
      if (s.auto_ok === false) return false
      return !!manual[s.id]
    }).length
  }, [assistant?.steps, manual])

  const total = assistant?.steps?.length ?? 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="Connector & LIVE-Assistent"
        description="Legaler Sofort-Pfad: UNSIGNED Windows-Connector, Pairing, Adapter, LIVE ohne DEMO-Fallback."
        actions={
          <>
            <Link to="/diagnostics">
              <Button variant="secondary">Zur Diagnose</Button>
            </Link>
            <Button
              variant="primary"
              disabled={diagMode === 'live' || setLive.isPending}
              onClick={() => setLive.mutate()}
            >
              LIVE aktivieren
            </Button>
          </>
        }
      />

      <Panel className="border border-[color-mix(in_srgb,var(--dn-accent)_35%,var(--dn-border))]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <SectionTitle>Windows-Connector herunterladen</SectionTitle>
            <p className="mt-2 text-sm text-[var(--dn-muted)]">
              Offizielles UNSIGNED Setup (Inno). Kein Code-Signing – SmartScreen-Warnung ist erwartet.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="warn">UNSIGNED</Badge>
              <Badge>v{installer?.version ?? '…'}</Badge>
              <Badge tone={installer?.available ? 'ok' : 'danger'}>
                {installer?.available ? 'Datei bereit' : 'Datei auf Server ausstehend'}
              </Badge>
            </div>
            {installer?.filename && (
              <dl className="mt-3 grid gap-1 text-xs text-[var(--dn-muted)] sm:grid-cols-2">
                <div>
                  <dt className="inline text-[var(--dn-muted)]">Datei: </dt>
                  <dd className="inline font-mono text-[var(--dn-text)]">{installer.filename}</dd>
                </div>
                <div>
                  <dt className="inline text-[var(--dn-muted)]">SHA-256: </dt>
                  <dd className="inline break-all font-mono text-[var(--dn-text)]">
                    {installer.sha256}
                  </dd>
                </div>
              </dl>
            )}
            {installer?.operator_de && !installer.available && (
              <p className="mt-3 text-xs text-[var(--dn-warn)]">{installer.operator_de}</p>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <a
              className="dn-btn dn-btn--primary text-center"
              href={installer?.download_path ?? '/downloads/'}
              download={installer?.filename}
            >
              Installer herunterladen
            </a>
            <a
              className="dn-btn dn-btn--secondary text-center text-sm"
              href="/downloads/INSTALLER_SHA256SUMS.txt"
              target="_blank"
              rel="noreferrer"
            >
              SHA-Summen-Datei
            </a>
          </div>
        </div>
      </Panel>

      <Panel>
        <SectionTitle>Rechtlicher Rahmen</SectionTitle>
        <p className="mt-2 text-sm text-[var(--dn-text)]">
          {guide?.legal_notice_de ?? assistant?.legal_notice_de ?? '…'}
        </p>
        <p className="mt-2 text-xs text-[var(--dn-muted)]">{guide?.ui_separation_de}</p>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Installation (Windows)</SectionTitle>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-[var(--dn-text)]">
            {(guide?.install_steps_de ?? []).map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </Panel>
        <Panel>
          <SectionTitle>Pairing & Adapter</SectionTitle>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-[var(--dn-text)]">
            {(guide?.pairing_steps_de ?? []).map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <ul className="mt-4 space-y-2 border-t border-[var(--dn-border)] pt-3 text-sm">
            {(guide?.adapters ?? []).map((a) => (
              <li key={a.id}>
                <span className="font-medium text-[var(--dn-text)]">{a.label_de}</span>
                <p className="text-xs text-[var(--dn-muted)]">{a.notes_de}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <SectionTitle>LIVE-Assistent – Checkliste</SectionTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={diagMode === 'live' ? 'ok' : 'warn'}>
              Modus: {diagMode === 'live' ? 'LIVE' : 'DEMO'}
            </Badge>
            <Badge>
              {doneCount}/{total || '…'} erledigt
            </Badge>
            <select
              className="rounded-md border border-[var(--dn-border)] bg-transparent px-2 py-1 text-sm"
              value={diagMode}
              aria-label="Diagnose-Modus"
              onChange={(e) => {
                const m = e.target.value === 'live' ? 'live' : 'demo'
                setDiagMode(m)
                localStorage.setItem('dn_diag_mode', m)
                void qc.invalidateQueries({ queryKey: ['connector-live-assistant'] })
              }}
            >
              <option value="live">LIVE</option>
              <option value="demo">DEMO</option>
            </select>
          </div>
        </div>
        <p className="mt-2 text-sm text-[var(--dn-muted)]">{assistant?.message_de}</p>
        <p className="mt-1 text-xs text-[var(--dn-muted)]">
          Connector:{' '}
          {assistant?.connector?.reachable
            ? `erreichbar (${assistant.connector.base_url ?? 'loopback'})`
            : `nicht erreichbar${
                assistant?.connector?.error_de ? ` – ${assistant.connector.error_de}` : ''
              }`}
        </p>

        <ul className="mt-4 space-y-3">
          {(assistant?.steps ?? []).map((step) => {
            const auto = step.auto_ok
            const checked = auto === true || (auto !== false && !!manual[step.id])
            const lockedFail = auto === false
            return (
              <li
                key={step.id}
                className="rounded-md border border-[var(--dn-border)] px-3 py-3"
              >
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={checked}
                    disabled={auto === true || lockedFail}
                    onChange={(e) =>
                      setManual((prev) => ({ ...prev, [step.id]: e.target.checked }))
                    }
                  />
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-[var(--dn-text)]">{step.title_de}</span>
                      {auto === true && <Badge tone="ok">auto OK</Badge>}
                      {auto === false && <Badge tone="danger">offen</Badge>}
                      {auto === null && <Badge>manuell</Badge>}
                    </span>
                    <p className="mt-1 text-xs text-[var(--dn-muted)]">{step.status_de}</p>
                  </span>
                </label>
              </li>
            )
          })}
          {!assistant && !assistantQ.isLoading && (
            <li className="text-sm text-[var(--dn-muted)]">Assistent wird geladen…</li>
          )}
        </ul>

        <div className="mt-4 border-t border-[var(--dn-border)] pt-3">
          <SectionTitle>OBD-II Basics (SAE J1979)</SectionTitle>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--dn-text)]">
            {(guide?.obd_basics_de ?? []).map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          <p className="mt-3 text-sm">
            Weiter zur Diagnose:{' '}
            <Link className="text-[var(--dn-accent)] underline" to="/diagnostics">
              /diagnostics
            </Link>
            {' · '}
            Betreiber (Admin):{' '}
            <Link className="text-[var(--dn-accent)] underline" to="/operator">
              /operator
            </Link>
          </p>
        </div>
      </Panel>
    </div>
  )
}
