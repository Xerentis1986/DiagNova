import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AuthProvider, useAuth } from './lib/auth'
import { ThemeProvider } from './lib/theme'
import { BrandsPage } from './pages/BrandsPage'
import { DashboardPage } from './pages/DashboardPage'
import { DiagnosticsPage } from './pages/DiagnosticsPage'
import { LoginPage } from './pages/LoginPage'
import { DiagnosticDataPage } from './pages/DiagnosticDataPage'
import { EcuPage } from './pages/EcuPage'
import { PlannedPage } from './pages/PlannedPage'
import { ReportsPage } from './pages/ReportsPage'
import { VehicleSelectPage } from './pages/VehicleSelectPage'
import { VehiclesPage } from './pages/VehiclesPage'
import type { ReactNode } from 'react'

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 5_000 } },
})

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8 text-[var(--dn-muted)]">Laden…</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AuthedShell({ children }: { children: ReactNode }) {
  return (
    <Protected>
      <ThemeProvider>{children}</ThemeProvider>
    </Protected>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <AuthedShell>
                  <Layout />
                </AuthedShell>
              }
            >
              <Route index element={<BrandsPage />} />
              <Route path="select/:brandSlug" element={<VehicleSelectPage />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="vehicles" element={<VehiclesPage />} />
              <Route path="diagnostics" element={<DiagnosticsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="ecu" element={<EcuPage />} />
              <Route path="diagnostic-data" element={<DiagnosticDataPage />} />
              <Route path="planned/:moduleId" element={<PlannedPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
