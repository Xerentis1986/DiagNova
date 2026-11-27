import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AuthProvider, useAuth } from './lib/auth'
import { ThemeProvider } from './lib/theme'
import { BrandsPage } from './pages/BrandsPage'
import { DashboardPage } from './pages/DashboardPage'
import { DiagnosticsPage } from './pages/DiagnosticsPage'
import { LoginPage } from './pages/LoginPage'
import { CustomersPage } from './pages/CustomersPage'
import { DataUpdatesPage } from './pages/DataUpdatesPage'
import { DiagnosticDataPage } from './pages/DiagnosticDataPage'
import { EcuPage } from './pages/EcuPage'
import { PlannedPage } from './pages/PlannedPage'
import { ReportsPage } from './pages/ReportsPage'
import { VehicleSelectPage } from './pages/VehicleSelectPage'
import { VehicleRecordPage } from './pages/VehicleRecordPage'
import { VehiclesPage } from './pages/VehiclesPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'
import { WorkshopPage } from './pages/WorkshopPage'
import { SettingsPage } from './pages/SettingsPage'
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
  return <Protected>{children}</Protected>
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <ThemeProvider>
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
                <Route path="workshop" element={<WorkshopPage />} />
                <Route path="customers" element={<CustomersPage />} />
                <Route path="work-orders" element={<WorkOrdersPage />} />
                <Route path="vehicles" element={<VehiclesPage />} />
                <Route path="vehicle-record" element={<VehicleRecordPage />} />
                <Route path="vehicle-record/:vehicleId" element={<VehicleRecordPage />} />
                <Route path="diagnostics" element={<DiagnosticsPage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="ecu" element={<EcuPage />} />
                <Route path="diagnostic-data" element={<DiagnosticDataPage />} />
                <Route path="data-updates" element={<DataUpdatesPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="planned/:moduleId" element={<PlannedPage />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
