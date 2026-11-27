import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { SimBanner } from './SimBanner'
import { ThemeToggle } from './ThemeToggle'

const NAV = [
  { to: '/', label: 'Marken', planned: false },
  { to: '/dashboard', label: 'Dashboard', planned: false },
  { to: '/vehicles', label: 'Fahrzeuge', planned: false },
  { to: '/diagnostics', label: 'Diagnose', planned: false },
  { to: '/reports', label: 'Berichte', planned: false },
  { to: '/ecu', label: 'Steuergeräte', planned: false },
  { to: '/planned/service', label: 'Service', planned: true },
  { to: '/planned/coding', label: 'Codierung', planned: true },
]

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-[var(--dn-border)] bg-[var(--dn-header)] backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--dn-accent)] font-bold text-white">
              DN
            </div>
            <div>
              <div className="text-lg font-semibold tracking-wide">DiagNova</div>
              <div className="text-xs text-[var(--dn-muted)]">Werkstatt-Diagnose · Markenauswahl</div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--dn-muted)]">
            <ThemeToggle />
            <span>
              {user?.full_name} · {user?.role}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-md border border-[var(--dn-border)] px-3 py-1.5 hover:bg-[var(--dn-hover)]"
            >
              Abmelden
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-3" aria-label="Hauptnavigation">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-md px-3 py-1.5 text-sm ${
                  isActive
                    ? 'bg-[var(--dn-logo-bg)] text-[var(--dn-text)]'
                    : 'text-[var(--dn-muted)] hover:bg-[var(--dn-hover)] hover:text-[var(--dn-text)]'
                }`
              }
            >
              {item.label}
              {item.planned && (
                <span className="ml-1 rounded bg-[var(--dn-hover)] px-1.5 py-0.5 text-[10px] uppercase text-[var(--dn-muted)]">
                  Geplant
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <SimBanner />
        <Outlet />
      </main>
    </div>
  )
}
