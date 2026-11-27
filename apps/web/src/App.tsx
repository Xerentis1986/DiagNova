import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AuthProvider, useAuth } from './lib/auth'
import { DashboardPage } from './pages/DashboardPage'
import { DiagnosticsPage } from './pages/DiagnosticsPage'
import { LoginPage } from './pages/LoginPage'
import { PlannedPage } from './pages/PlannedPage'
import { ReportsPage } from './pages/ReportsPage'
import { VehiclesPage } from './pages/VehiclesPage'
import type { ReactNode } from 'react'

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 5_000 } },
})

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8 text-slate-400">Laden…</div>
  if (!user) return <Navigate to="/login" replace />
  return children
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
                <Protected>
                  <Layout />
                </Protected>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="vehicles" element={<VehiclesPage />} />
              <Route path="diagnostics" element={<DiagnosticsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="planned/:moduleId" element={<PlannedPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
