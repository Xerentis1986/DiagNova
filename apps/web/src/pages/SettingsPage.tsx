import { Link } from 'react-router-dom'
import { ThemeToggle } from '../components/ThemeToggle'
import { Panel, PageHeader, SectionTitle, Badge } from '../components/ui'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'

export function SettingsPage() {
  const { user } = useAuth()
  const { preference, resolved } = useTheme()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Einstellungen"
        description="Darstellung, Profil und Verweise auf Werkstattmodule. Keine Diagnose- oder Sicherheitslogik."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Darstellung</SectionTitle>
          <p className="mb-3 text-sm text-[var(--dn-muted)]">
            Hell / Dunkel / System. Preference: <Badge tone="accent">{preference}</Badge> · aktiv:{' '}
            <Badge>{resolved}</Badge>
          </p>
          <ThemeToggle />
        </Panel>

        <Panel>
          <SectionTitle>Profil</SectionTitle>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--dn-muted)]">Name</dt>
              <dd>{user?.full_name}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--dn-muted)]">E-Mail</dt>
              <dd>{user?.email}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--dn-muted)]">Rolle</dt>
              <dd>
                <Badge>{user?.role}</Badge>
              </dd>
            </div>
          </dl>
        </Panel>

        <Panel className="lg:col-span-2">
          <SectionTitle>Werkstatt & Module</SectionTitle>
          <ul className="flex flex-wrap gap-2">
            <li>
              <Link className="dn-btn dn-btn--secondary" to="/workshop">
                Werkstattprofil
              </Link>
            </li>
            <li>
              <Link className="dn-btn dn-btn--secondary" to="/customers">
                Kunden
              </Link>
            </li>
            <li>
              <Link className="dn-btn dn-btn--secondary" to="/reports">
                Berichte
              </Link>
            </li>
            <li>
              <Link className="dn-btn dn-btn--secondary" to="/service">
                Servicefunktionen
              </Link>
            </li>
            <li>
              <Link className="dn-btn dn-btn--secondary" to="/guided">
                Geführte Diagnose
              </Link>
            </li>
            <li>
              <Link className="dn-btn dn-btn--secondary" to="/planned/coding">
                Codierung (geplant)
              </Link>
            </li>
          </ul>
        </Panel>
      </div>
    </div>
  )
}
