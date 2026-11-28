import { useQuery } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { BrandMark } from './BrandMark'
import {
  IconCar,
  IconCustomers,
  IconDashboard,
  IconDatabase,
  IconDiagnose,
  IconFleet,
  IconReports,
  IconSettings,
  IconUpdates,
  IconWorkshop,
} from './icons'
import { SimBanner } from './SimBanner'
import { ThemeToggle } from './ThemeToggle'
import { Button } from './ui'

type NavItem = {
  to: string
  label: string
  end?: boolean
  icon: ReactNode
  planned?: boolean
}

const SIDEBAR_PRIMARY: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: <IconDashboard /> },
  { to: '/', label: 'Fahrzeugauswahl', end: true, icon: <IconCar /> },
  { to: '/diagnostics', label: 'Fahrzeugdiagnose', icon: <IconDiagnose /> },
  { to: '/vehicles', label: 'Fahrzeugverwaltung', icon: <IconFleet /> },
  { to: '/work-orders', label: 'Werkstatt & Aufträge', icon: <IconWorkshop /> },
  { to: '/diagnostic-data', label: 'Diagnosedatenbank', icon: <IconDatabase /> },
  { to: '/data-updates', label: 'Updates & Datenquellen', icon: <IconUpdates /> },
  { to: '/software-updates', label: 'Software-Updates', icon: <IconUpdates /> },
  { to: '/settings', label: 'Einstellungen', icon: <IconSettings /> },
]

const SIDEBAR_MORE: NavItem[] = [
  { to: '/customers', label: 'Kunden', icon: <IconCustomers /> },
  { to: '/workshop', label: 'Werkstattprofil', icon: <IconWorkshop /> },
  { to: '/vehicle-record', label: 'Fahrzeugakte', icon: <IconFleet /> },
  { to: '/reports', label: 'Berichte', icon: <IconReports /> },
  { to: '/ecu', label: 'Steuergeräte', icon: <IconDiagnose /> },
  { to: '/guided', label: 'Geführte Diagnose', icon: <IconDiagnose /> },
  { to: '/service', label: 'Service', icon: <IconWorkshop /> },
  { to: '/coding', label: 'Codierung', icon: <IconSettings /> },
  { to: '/tuning', label: 'Chiptuning', icon: <IconSettings />, planned: true },
  { to: '/subscriptions', label: 'Abos & Lizenzen', icon: <IconUpdates /> },
  { to: '/commerce', label: 'Konto & Abrechnung', icon: <IconUpdates /> },
  { to: '/lkw', label: 'LKW / Nutzfahrzeug', icon: <IconFleet />, planned: true },
  { to: '/security', label: 'Sicherheit', icon: <IconSettings /> },
]

const QUICK: { to: string; label: string; end?: boolean }[] = [
  { to: '/', label: 'Start', end: true },
  { to: '/vehicles', label: 'Fahrzeuge' },
  { to: '/diagnostics', label: 'Diagnose' },
  { to: '/workshop', label: 'Werkstatt' },
  { to: '/diagnostic-data', label: 'Datenbank' },
  { to: '/data-updates', label: 'Daten-Updates' },
  { to: '/software-updates', label: 'SW-Updates' },
]

function navClass(active: boolean) {
  return `dn-side-link ${active ? 'dn-side-link--active' : ''}`.trim()
}

function StatusFooter() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30_000,
    retry: 1,
  })
  const updates = useQuery({
    queryKey: ['data-updates-dash-shell'],
    queryFn: () => api.dataUpdatesDashboard(),
    refetchInterval: 60_000,
    retry: 0,
  })

  const serverOk = health.data?.status === 'ok'
  const lastUpdate = updates.data?.last_run_at ?? updates.data?.channels?.[0]?.last_run_at
  const lastLabel = lastUpdate
    ? new Date(lastUpdate).toLocaleString('de-AT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'

  return (
    <div className="dn-side-status" aria-label="Systemstatus">
      <div className="dn-side-status__row">
        <span className={`dn-status-dot ${serverOk ? 'dn-status-dot--ok' : 'dn-status-dot--danger'}`} />
        <span>Server: {serverOk ? 'Online' : health.isError ? 'Offline' : '…'}</span>
      </div>
      <div className="dn-side-status__row">
        <span className="dn-status-dot dn-status-dot--ok" />
        <span>Datenbank: {serverOk ? 'Erreichbar' : '—'}</span>
      </div>
      <div className="dn-side-status__row text-[11px] text-[var(--dn-muted)]">
        Letztes Update: {lastLabel}
      </div>
      <div className="dn-side-status__row text-[11px] text-[var(--dn-muted)]">Version: v0.15.0</div>
    </div>
  )
}

export function AppShell() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenu, setUserMenu] = useState(false)
  const moreItems = SIDEBAR_MORE
  const operatorItem: NavItem | null = user?.is_platform_admin
    ? { to: '/operator', label: 'Betreiberkonsole', icon: <IconSettings /> }
    : null

  return (
    <div className="dn-shell">
      {mobileOpen && (
        <button
          type="button"
          className="dn-shell-backdrop"
          aria-label="Menü schließen"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        id="dn-sidebar"
        className={`dn-sidebar ${mobileOpen ? 'dn-sidebar--open' : ''}`.trim()}
        aria-label="Hauptmenü"
      >
        <div className="dn-sidebar__brand">
          <BrandMark variant="lockup" height="2rem" />
          <p className="mt-2 text-xs text-[var(--dn-muted)]">Mehrmarken-Diagnose</p>
        </div>

        <nav className="dn-sidebar__nav" onClick={() => setMobileOpen(false)}>
          {SIDEBAR_PRIMARY.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => navClass(isActive)}>
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}

          <p className="dn-sidebar__group">Weitere</p>
          {moreItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => navClass(isActive)}>
              {item.icon}
              <span>{item.label}</span>
              {item.planned && <span className="dn-badge ml-auto">Geplant</span>}
            </NavLink>
          ))}
          {operatorItem && (
            <>
              <p className="dn-sidebar__group">Betreiber</p>
              <NavLink
                to={operatorItem.to}
                className={({ isActive }) => navClass(isActive)}
              >
                {operatorItem.icon}
                <span>{operatorItem.label}</span>
              </NavLink>
            </>
          )}
        </nav>

        <StatusFooter />
      </aside>

      <div className="dn-shell__main">
        <header className="dn-topbar">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="dn-btn dn-btn--secondary dn-btn--sm lg:hidden"
              aria-expanded={mobileOpen}
              aria-controls="dn-sidebar"
              onClick={() => setMobileOpen((v) => !v)}
            >
              Menü
            </button>
            <nav className="dn-quicklinks" aria-label="Schnellzugriff">
              {QUICK.map((q) => (
                <NavLink
                  key={q.to}
                  to={q.to}
                  end={q.end}
                  className={({ isActive }) =>
                    `dn-quicklink ${isActive ? 'dn-quicklink--active' : ''}`.trim()
                  }
                >
                  {q.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <ThemeToggle />
            <div className="relative">
              <Button
                variant="secondary"
                size="sm"
                aria-expanded={userMenu}
                aria-haspopup="menu"
                onClick={() => setUserMenu((v) => !v)}
              >
                {user?.full_name ?? 'Benutzer'}
              </Button>
              {userMenu && (
                <div className="dn-user-menu" role="menu">
                  <div className="px-3 py-2 text-xs text-[var(--dn-muted)]">
                    {user?.email} · {user?.role}
                  </div>
                  <NavLink
                    to="/settings"
                    className="dn-user-menu__item"
                    role="menuitem"
                    onClick={() => setUserMenu(false)}
                  >
                    Einstellungen
                  </NavLink>
                  <button
                    type="button"
                    className="dn-user-menu__item w-full text-left"
                    role="menuitem"
                    onClick={() => {
                      setUserMenu(false)
                      logout()
                    }}
                  >
                    Abmelden
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="dn-content">
          <SimBanner />
          <Outlet />
        </main>
      </div>
    </div>
  )
}

/** @deprecated Alias – Layout nutzt AppShell */
export { AppShell as Layout }
