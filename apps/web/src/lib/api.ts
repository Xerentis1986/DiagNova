const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || ''

export type UserRole = 'admin' | 'technician' | 'viewer'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface Vehicle {
  id: string
  make: string
  model: string
  year: number
  vin: string
  license_plate: string | null
  engine: string | null
  fuel_type: string | null
  is_example_data: boolean
  notes: string | null
}

export interface DtcEntry {
  code: string
  status: 'stored' | 'pending' | 'permanent'
  description_de: string
  severity: 'info' | 'warning' | 'critical'
}

export interface PidReading {
  pid: number
  pid_hex: string
  name: string
  description_de: string
  value: number
  unit: string
  timestamp: string
}

export interface LiveData {
  data_source: 'simulated' | 'live'
  vehicle_id: string
  vin: string
  readings: PidReading[]
  readiness: Record<string, boolean>
  freeze_frame: Record<string, number | string> | null
}

export interface ConnectionStatus {
  connected: boolean
  mode: 'simulator' | 'connector' | 'none'
  adapter_name: string
  data_source: 'simulated' | 'live'
  message_de: string
  last_heartbeat: string | null
}

export interface SessionSummary {
  id: string
  vehicle_id: string
  vehicle_label: string
  started_at: string
  ended_at: string | null
  data_source: 'simulated' | 'live'
  dtc_count: number
  status: 'open' | 'closed'
}

export interface DashboardData {
  active_vehicle: Vehicle | null
  connection: ConnectionStatus
  recent_sessions: SessionSummary[]
  demo_mode: boolean
  planned_modules: { id: string; label: string; status: string }[]
}

export interface Report {
  id: string
  session_id: string
  title: string
  created_at: string
  content: Record<string, unknown>
}

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function authHeader(): HeadersInit {
  const token = localStorage.getItem('dn_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
      ...(init.headers || {}),
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  login(email: string, password: string) {
    return request<{ access_token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },
  me() {
    return request<User>('/api/auth/me')
  },
  dashboard(activeVehicleId?: string | null) {
    const q = activeVehicleId ? `?active_vehicle_id=${encodeURIComponent(activeVehicleId)}` : ''
    return request<DashboardData>(`/api/dashboard${q}`)
  },
  vehicles() {
    return request<Vehicle[]>('/api/vehicles')
  },
  vehicle(id: string) {
    return request<Vehicle>(`/api/vehicles/${id}`)
  },
  connection() {
    return request<ConnectionStatus>('/api/connection')
  },
  dtcs(vehicleId: string) {
    return request<DtcEntry[]>(`/api/diagnostics/${vehicleId}/dtcs`)
  },
  live(vehicleId: string) {
    return request<LiveData>(`/api/diagnostics/${vehicleId}/live`)
  },
  startSession(vehicleId: string) {
    return request<SessionSummary>(`/api/sessions?vehicle_id=${encodeURIComponent(vehicleId)}`, {
      method: 'POST',
    })
  },
  sessions() {
    return request<SessionSummary[]>('/api/sessions')
  },
  createReport(sessionId: string, title: string) {
    return request<Report>('/api/reports', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, title }),
    })
  },
  exportUrl(reportId: string, kind: 'csv' | 'pdf') {
    const token = localStorage.getItem('dn_token')
    return `${API_BASE}/api/reports/${reportId}/export.${kind}?token_hint=use_header&_=${token ? 'auth' : 'none'}`
  },
  async downloadExport(reportId: string, kind: 'csv' | 'pdf') {
    const res = await fetch(`${API_BASE}/api/reports/${reportId}/export.${kind}`, {
      headers: { ...authHeader() },
    })
    if (!res.ok) throw new ApiError(res.status, 'Export fehlgeschlagen')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `diagnova-report-${reportId}.${kind}`
    a.click()
    URL.revokeObjectURL(url)
  },
}

export { ApiError }
