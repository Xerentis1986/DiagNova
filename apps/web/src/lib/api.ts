const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || ''

export type UserRole = 'admin' | 'technician' | 'viewer'
export type ThemePreference = 'light' | 'dark' | 'system'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  theme_preference: ThemePreference
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
  series: string | null
  odometer_km: number | null
  catalog_brand_slug: string | null
  catalog_model_id: string | null
  catalog_variant_id: string | null
  is_example_data: boolean
  notes: string | null
}

export interface Brand {
  slug: string
  name: string
  group: string
  sort_order: number
  logo_mode: 'text_fallback' | 'image'
  logo_initials: string
  logo_rights_cleared: boolean
  coverage_disclaimer_de: string
  model_count: number
}

export interface CatalogModel {
  id: string
  name: string
  variant_count: number
}

export interface CatalogVariant {
  id: string
  series: string
  year_from: number
  year_to: number
  engine: string
  fuel_type: string
}

export interface CapabilityItem {
  id: string
  label_de: string
  status: 'simulated' | 'planned' | 'available' | 'unavailable'
  phase: number
}

export interface Capabilities {
  disclaimer_de: string
  available: CapabilityItem[]
  unavailable: CapabilityItem[]
  adapter_next_step_de: string
}

export interface EcuDiscovered {
  ecu_id: string
  response_hex: string
  request_hex: string | null
  slot_index: number | null
  role_hint_de: string
  verified_source: string
  discovery_method: string
  status: string
}

export interface EcuSimulated {
  data_source: string
  protocol_name?: string | null
  blind_scan_used: boolean
  blind_scan_allowed: boolean
  count: number
  discovered_obd_ecus: EcuDiscovered[]
  unavailable_categories: { id: string; label_de: string; reason_de: string }[]
  message_de: string
  categories?: {
    id: string
    label_de: string
    availability: string
    notes_de?: string
  }[]
  identification_read_first?: {
    status: string
    vin?: string
    note_de?: string
  }
  disclaimer_de?: string
}

export interface EcuOverview {
  data_source: string
  blind_scan_allowed: boolean
  disclaimer_de: string
  categories: {
    id: string
    label_de: string
    availability: string
    notes_de?: string
    source?: string | null
  }[]
}

export interface CapabilityMatrix {
  disclaimer_de: string
  adapters: {
    adapter_id: string
    hardware_tested?: boolean
    protocols?: Record<string, string>
    notes_de?: string
  }[]
}

export interface RecentSelection {
  id: string
  vehicle_id: string | null
  brand_slug: string
  brand_name: string
  model_name: string
  series: string | null
  year: number | null
  engine: string | null
  vin: string | null
  used_at: string
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

export interface VehicleConfirmPayload {
  brand_slug: string
  model_id: string
  variant_id: string
  year: number
  vin: string
  license_plate?: string | null
  odometer_km?: number | null
  notes?: string | null
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
  updatePreferences(theme_preference: ThemePreference) {
    return request<{ theme_preference: ThemePreference }>('/api/preferences', {
      method: 'PATCH',
      body: JSON.stringify({ theme_preference }),
    })
  },
  getFavorites() {
    return request<{ brand_slugs: string[] }>('/api/favorites/brands')
  },
  putFavorites(brand_slugs: string[]) {
    return request<{ brand_slugs: string[] }>('/api/favorites/brands', {
      method: 'PUT',
      body: JSON.stringify({ brand_slugs }),
    })
  },
  recentSelections() {
    return request<RecentSelection[]>('/api/recent/selections')
  },
  catalogBrands(q?: string) {
    const qs = q ? `?q=${encodeURIComponent(q)}` : ''
    return request<Brand[]>(`/api/catalog/brands${qs}`)
  },
  catalogModels(slug: string) {
    return request<CatalogModel[]>(`/api/catalog/brands/${slug}/models`)
  },
  catalogVariants(slug: string, modelId: string) {
    return request<CatalogVariant[]>(`/api/catalog/brands/${slug}/models/${modelId}/variants`)
  },
  catalogCapabilities(brandSlug?: string) {
    const qs = brandSlug ? `?brand_slug=${encodeURIComponent(brandSlug)}` : ''
    return request<Capabilities>(`/api/catalog/capabilities${qs}`)
  },
  protocolCatalog() {
    return request<Record<string, unknown>>('/api/protocols/catalog')
  },
  capabilityMatrix() {
    return request<CapabilityMatrix>('/api/protocols/capability-matrix')
  },
  ecuOverview() {
    return request<EcuOverview>('/api/protocols/ecu/overview')
  },
  ecuSimulated() {
    return request<EcuSimulated>('/api/protocols/ecu/simulated')
  },
  confirmVehicle(payload: VehicleConfirmPayload) {
    return request<Vehicle>('/api/vehicles/confirm', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  updateVehicle(
    id: string,
    payload: { vin?: string; license_plate?: string | null; odometer_km?: number | null; notes?: string | null },
  ) {
    return request<Vehicle>(`/api/vehicles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
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
  clearDtcWarnings() {
    return request<{
      data_source: string
      warnings_de: string[]
      permanent_dtcs_clearable: boolean
      requires_confirmation_phrase: string
      hardware_live: boolean
    }>('/api/diagnostics/clear/warnings')
  },
  clearDtcs(
    vehicleId: string,
    body: {
      confirmation_phrase: string
      acknowledge_freeze_frame_loss: boolean
      acknowledge_readiness_reset: boolean
      acknowledge_permanent_remain: boolean
      pre_report_saved: boolean
      operator_note?: string
    },
  ) {
    return request<{
      success: boolean
      data_source: string
      message_de: string
      before?: DtcEntry[]
      after?: DtcEntry[]
      permanent_remain?: DtcEntry[]
    }>(`/api/diagnostics/${vehicleId}/dtcs/clear`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
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
