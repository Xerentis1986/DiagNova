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
  workshop_id?: string | null
  is_platform_admin?: boolean
}

export interface SubscriptionPlan {
  code: string
  name_de: string
  vehicle_scope: 'pkw' | 'lkw' | 'kombi'
  billing_period: string
  price_cents_demo: number | null
  currency: string
  trial_days: number
  max_devices: number
  release_status: 'available' | 'planned'
  description_de: string
  entitlements: string[]
  payment_note_de: string
}

export interface SubscriptionInfo {
  id: string
  workshop_id: string
  plan_code: string
  plan_name_de?: string | null
  status: string
  payment_provider: string
  external_ref?: string | null
  trial_ends_at?: string | null
  current_period_start?: string | null
  current_period_end?: string | null
  cancel_at_period_end: boolean
  canceled_at?: string | null
  grace_until?: string | null
  entitlements: string[]
  is_example_data: boolean
  license_active: boolean
  allows_new_operations: boolean
  has_running_critical_ops: boolean
  message_de: string
  payment_note_de: string
}

export interface DeviceBinding {
  id: string
  workshop_id: string
  device_name: string
  device_fingerprint: string
  platform: string
  last_seen_at: string | null
  revoked_at: string | null
  is_example_data: boolean
}

export interface Invitation {
  id: string
  workshop_id: string
  email: string
  role: UserRole
  status: string
  expires_at: string
  accepted_at: string | null
  token?: string | null
}

export interface SoftwareComponentInfo {
  key: string
  label_de: string
  current_version: string
  previous_version: string | null
  channel_key: string
  health_status: string
  last_healthcheck_at: string | null
  last_error_de: string | null
}

export interface SoftwareChannel {
  id: string
  key: string
  name: string
  channel_type: string
  fetch_mode: string
  enabled: boolean
  auto_install_allowed: boolean
  require_signature: boolean
  require_signing_cert: boolean
  notes_de: string | null
}

export interface SoftwarePackage {
  id: string
  channel_id: string
  channel_key?: string | null
  component: string
  version: string
  package_filename: string
  content_sha256: string
  signature_ok: boolean | null
  release_notes_de: string
  migration_plan: unknown[]
  status: string
  error_de: string | null
  created_at: string | null
  approved_by: string | null
  approved_at: string | null
}

export interface SoftwareRun {
  id: string
  package_id: string
  component: string
  action: string
  status: string
  from_version: string | null
  to_version: string | null
  healthcheck_ok: boolean | null
  busy_reason_de: string | null
  error_de: string | null
  summary: Record<string, unknown>
  started_at: string | null
  finished_at: string | null
}

export interface SoftwareBusyGate {
  allowed: boolean
  reason_de: string | null
  blockers: { kind: string; ref: string; detail_de: string }[]
}

export interface SoftwareUpdatesDashboard {
  disclaimer_de: string
  signing_cert_configured: boolean
  auto_install_enabled: boolean
  productive_auto_updates_blocked: boolean
  components: SoftwareComponentInfo[]
  channels: SoftwareChannel[]
  pending_packages: SoftwarePackage[]
  recent_packages: SoftwarePackage[]
  recent_runs: SoftwareRun[]
  recent_events: {
    id: string
    package_id: string | null
    run_id: string | null
    component: string | null
    event: string
    detail_de: string
    created_at: string | null
  }[]
  compatibility_rules: {
    id: string
    component: string
    version: string
    requires: Record<string, string>
    notes_de: string | null
  }[]
  migration_plan: {
    revision: string
    from_revision: string
    backup_required: boolean
    backup_steps_de: string[]
    restore_steps_de: string[]
    notes_de: string | null
  }[]
  busy: SoftwareBusyGate
  data_updates_note_de: string
}

export interface AdminDashboard {
  payment_mode: string
  payment_note_de: string
  workshops_count: number
  users_count: number
  active_subscriptions: number
  past_due_subscriptions: number
  canceled_subscriptions: number
  invitations_pending: number
  devices_bound: number
  data_versions: { id: string; label: string; status: string; created_at: string | null }[]
  adapter_summary: Record<string, unknown>[]
  recent_audit: Record<string, unknown>[]
  recent_webhooks: Record<string, unknown>[]
  subscriptions: SubscriptionInfo[]
  legal_open_items_de: string[]
  stripe?: Record<string, unknown> | null
  mollie?: Record<string, unknown> | null
  customers_count?: number
  customers_b2b?: number
  customers_b2c?: number
  trial_subscriptions?: number
  mrr_cents?: number
  arr_cents?: number
  invoices_open?: number
  invoices_paid?: number
  invoices_overdue?: number
  active_licenses?: number
  metrics_note_de?: string | null
}

export interface SecurityThreatNode {
  id: string
  surface: string
  threat: string
  mitigation_de: string
  status: 'mitigated' | 'partial' | 'open' | 'accepted'
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
}

export interface SecurityFinding {
  id: string
  title_de: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'open' | 'mitigated' | 'accepted' | 'documented'
  detail_de: string
}

export interface SecurityDashboard {
  version: string
  demo_mode: boolean
  jwt_secret_insecure_default: boolean
  cors_origins: string[]
  rate_limits: Record<string, number>
  auth: Record<string, string | boolean | number>
  rbac_roles: string[]
  audit_redaction: boolean
  security_headers: boolean
  ssrf_protection_data_updates: boolean
  connector_loopback_only: boolean
  productive_auto_updates_blocked: boolean
  monitoring_enabled: boolean
  disclaimer_de: string
  threat_model: SecurityThreatNode[]
  findings: SecurityFinding[]
  open_risks_de: string[]
}

export interface SecurityPrivacy {
  disclaimer_de: string
  processes: {
    id: string
    title_de: string
    description_de: string
    api_hint: string | null
    legal_note_de: string
  }[]
  retention_note_de: string
  av_note_de: string
}

export interface SecurityBackup {
  disclaimer_de: string
  recommended_steps_de: string[]
  restore_steps_de: string[]
  monitoring_hints_de: string[]
  phase16_checklist_hint: string
}

export interface SecurityAuditList {
  items: {
    id: string
    action: string
    resource: string
    detail: string | null
    user_id: string | null
    workshop_id: string | null
    created_at: string | null
  }[]
  note_de: string
}

export interface Vehicle {
  id: string
  workshop_id?: string | null
  customer_id?: string | null
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
  archived_at?: string | null
}

export interface Workshop {
  id: string
  name: string
  legal_name: string | null
  email: string | null
  phone: string | null
  street: string | null
  postal_code: string | null
  city: string | null
  country: string
  vat_id: string | null
  has_logo: boolean
  retention_days: number
  notes: string | null
  is_example_data: boolean
  archived_at: string | null
}

export interface WorkshopMember {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface Customer {
  id: string
  workshop_id: string
  display_name: string
  email: string | null
  phone: string | null
  street: string | null
  postal_code: string | null
  city: string | null
  country: string | null
  notes: string | null
  is_example_data: boolean
  archived_at: string | null
  anonymized_at: string | null
  created_at?: string | null
}

export interface WorkOrder {
  id: string
  workshop_id: string
  customer_id: string | null
  vehicle_id: string | null
  created_by_user_id: string | null
  title: string
  status: 'open' | 'in_progress' | 'done' | 'cancelled'
  notes: string | null
  repair_summary: string | null
  odometer_km: number | null
  is_example_data: boolean
  archived_at: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface TimelineItem {
  id: string
  kind: 'session' | 'note' | 'work_order' | 'report'
  at: string
  title_de: string
  summary_de: string
  data_source?: string | null
  status?: string | null
  odometer_km?: number | null
  session_id?: string | null
  work_order_id?: string | null
  report_id?: string | null
  is_example_data: boolean
  authenticity: 'recorded' | 'example_seed' | 'simulated'
}

export interface VehicleRecord {
  vehicle_id: string
  make: string
  model: string
  year: number
  vin: string
  license_plate: string | null
  odometer_km: number | null
  is_example_data: boolean
  customer_id: string | null
  workshop_id: string | null
  session_count: number
  open_session_count: number
  timeline: TimelineItem[]
  disclaimer_de: string
}

export interface SessionDetail {
  id: string
  vehicle_id: string
  vehicle_label: string
  workshop_id: string | null
  user_id: string
  user_name: string | null
  work_order_id: string | null
  status: 'open' | 'closed' | 'aborted'
  data_source: 'simulated' | 'live'
  started_at: string
  ended_at: string | null
  auto_saved_at: string | null
  odometer_km: number | null
  adapter_name: string | null
  protocol_name: string | null
  abort_reason: string | null
  notes: string | null
  dtc_count: number
  ecus: {
    ecu_code: string
    ecu_label_de: string
    checked: boolean
    protocol_name: string | null
    address_hex: string | null
    status: string
  }[]
  dtcs: {
    ecu_code: string
    code: string
    dtc_status: string
    description_de: string
    severity: string
  }[]
  freeze_frame: Record<string, unknown> | null
  readiness: Record<string, unknown> | null
  report_ids: string[]
  measurement_sample_count: number
}

export interface SessionCompare {
  before_session_id: string
  after_session_id: string
  vehicle_id: string
  incomplete_scan: boolean
  unchecked_ecus_in_after: string[]
  items: {
    ecu_code: string
    code: string
    dtc_status: string
    description_de: string
    outcome: 'neu' | 'weiterhin_vorhanden' | 'nicht_erneut_beobachtet'
    ecu_checked_in_after: boolean
    may_interpret_as_resolved: boolean
    note_de: string
  }[]
  disclaimer_de: string
}

export interface MeasurementSeries {
  vehicle_id: string
  pid: number | null
  name: string | null
  unit: string | null
  from_at: string | null
  to_at: string | null
  count: number
  truncated: boolean
  max_samples: number
  samples: {
    id: string
    session_id: string
    pid: number
    pid_hex: string
    name: string
    value: number
    unit: string
    recorded_at: string
    data_source: 'simulated' | 'live'
  }[]
  disclaimer_de: string
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
  status: 'open' | 'closed' | 'aborted'
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
  report_number?: string | null
  workshop_id?: string | null
  vehicle_id?: string | null
  customer_id?: string | null
  data_source?: string | null
  data_version?: string | null
  content_sha256?: string | null
  auto_generated?: boolean
  frozen_at?: string | null
  archived_at?: string | null
  deleted_at?: string | null
  notes?: string | null
  recommendations?: string | null
}

export interface ReportSummary {
  id: string
  session_id: string
  workshop_id?: string | null
  vehicle_id?: string | null
  customer_id?: string | null
  report_number?: string | null
  title: string
  data_source?: string | null
  data_version?: string | null
  content_sha256?: string | null
  auto_generated: boolean
  demo_watermark: boolean
  created_at: string
  frozen_at?: string | null
  archived_at?: string | null
  deleted_at?: string | null
  vehicle_label: string
  vin?: string | null
  dtc_count: number
}

export interface DataLicenseSource {
  key: string
  name: string
  url: string | null
  version: string | null
  license_name: string
  commercial_use: string
  attribution: string | null
  scope: string
  notes_de: string | null
  checked_at: string
  redistributable: boolean
}

export interface Provenance {
  source_key: string
  source_name: string
  license_name: string
  commercial_use: string
  attribution: string | null
  checked_at: string
  redistributable: boolean
  url: string | null
  version: string | null
}

export interface DtcLookup {
  code: string
  known: boolean
  description_de: string
  description_status: 'known' | 'unknown' | 'withheld'
  data_scope: string | null
  provenance: Provenance | null
  message_de: string
}

export interface DiagPid {
  id: string
  pid_hex: string
  name: string
  description_de: string
  unit: string
  bytes_needed: number
  conversion_formula: string | null
  data_scope: string
  kind: string
  provenance: Provenance
}

export interface DiagEcu {
  id: string
  code: string
  name_de: string
  category: string
  protocol_id: string
  request_address: string | null
  response_address: string | null
  verified: boolean
  data_scope: string
  provenance: Provenance
}

export interface DiagnosticCoverage {
  disclaimer_de: string
  generic_pids: number
  ecu_count: number
  manufacturer_count: number
  odx_import: string
  blocked_vendors: string[]
  phase_07: string
}

export interface ImportPreview {
  batch_id: string
  status: string
  format: string
  summary: Record<string, unknown>
  conflicts: { entity_type: string; key: string; reason_de: string }[]
  quarantine: { entity_type: string; row_index: number; reason_de: string }[]
  can_apply: boolean
  message_de: string
}

export interface ImportBatch {
  id: string
  format: string
  status: string
  applied_count: number
  quarantine_count: number
}

export interface UpdateChannel {
  id: string
  key: string
  name: string
  fetch_mode: string
  url: string
  enabled: boolean
  rights_verified: boolean
  interval_hours: number
  expected_license: string
  source_key: string
  content_kind: string
  auto_activate_allowed: boolean
  max_bytes: number
  require_signature: boolean
  signature_key_id: string | null
  last_etag: string | null
  last_version: string | null
  last_content_hash: string | null
  last_run_at: string | null
  next_run_at: string | null
  notes_de: string | null
}

export interface UpdateRun {
  id: string
  channel_id: string
  channel_key: string | null
  trigger: string
  status: string
  etag: string | null
  version_label: string | null
  content_hash: string | null
  signature_ok: boolean | null
  license_changed: boolean
  detected_license: string | null
  http_status: number | null
  error_de: string | null
  summary: Record<string, unknown>
  import_batch_id: string | null
  dataset_version_id: string | null
  started_at: string
  finished_at: string | null
}

export interface UpdateChangelog {
  id: string
  run_id: string
  channel_key: string
  event: string
  detail_de: string
  created_at: string
}

export interface DataUpdatesDashboard {
  scheduler_enabled: boolean
  default_interval_hours: number
  lock_held: boolean
  lock_by: string | null
  channels: UpdateChannel[]
  recent_runs: UpdateRun[]
  pending_approvals: UpdateRun[]
  recent_changelog: UpdateChangelog[]
  next_scheduled_at: string | null
  last_run_at: string | null
  disclaimer_de: string
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

export interface ServiceProcedure {
  code: string
  name_de: string
  category: string
  safety_class: string
  release_status: string
  enabled: boolean
  write_allowed: boolean
  prerequisites: { id: string; label_de: string }[]
  confirmation_phrase: string | null
  timeout_seconds: number
  abort_strategy_de: string
  result_checks_de: string[]
  ecu_roles: string[]
  compatibility_de: string
  source_license_de: string
  notes_de: string
  blockers: string[]
  data_source: string
  oem_procedure_invented: boolean
}

export interface ServiceCatalog {
  data_source: string
  disclaimer_de: string
  procedures: ServiceProcedure[]
  excluded: { code: string; name_de: string; reason_de?: string; safety_class?: string }[]
  live_execution_available: boolean
  hardware_live: boolean
}

export interface ServiceVehicleState {
  ignition_on?: boolean
  adapter_connected?: boolean
  battery_voltage_ok?: boolean
  operator_confirm?: boolean
  oem_spec_present?: boolean
  safe_work_area?: boolean
  exhaust_safe?: boolean
}

export interface ServiceRun {
  id: string
  procedure_code: string
  status: string
  scenario: string | null
  data_source: string
  prerequisites: { id: string; label_de: string; met: boolean; detail_de?: string | null }[]
  result: Record<string, unknown>
  message_de: string | null
  abort_reason_de: string | null
  write_commands_sent: boolean
  started_at: string
  ended_at: string | null
}

export interface MeasurementGroup {
  id: string
  label_de: string
  pid_names: string[]
  notes_de: string
  data_source: string
}

export interface DtcHelp {
  code: string
  description_de: string | null
  description_status: string
  severity: string | null
  help_de: string
  source: string
  data_source: string
  repair_auto_generated: boolean
}

export interface GuidedOverview {
  data_source: string
  disclaimer_de: string
  ecu_summary: Record<string, unknown>
  measurement_groups: MeasurementGroup[]
  dtc_help_hint_de: string
}

export interface CodingOperation {
  code: string
  name_de: string
  category: string
  operation_type: string
  safety_class: string
  release_status: string
  enabled: boolean
  write_allowed: boolean
  flash_allowed: boolean
  prerequisites: { id: string; label_de: string }[]
  confirmation_phrase: string | null
  timeout_seconds: number
  abort_strategy_de: string
  result_checks_de: string[]
  ecu_roles: string[]
  compatibility_de: string
  source_license_de: string
  notes_de: string
  blockers: string[]
  requires_j2534: boolean
  requires_authorization: boolean
  backup_supported: boolean
  auto_retry_forbidden: boolean
  data_source: string
  oem_procedure_invented: boolean
}

export interface CodingCatalog {
  data_source: string
  disclaimer_de: string
  operations: CodingOperation[]
  excluded: { code: string; name_de: string; reason_de?: string; safety_class?: string }[]
  live_execution_available: boolean
  flash_available: boolean
  hardware_live: boolean
  auto_retry_forbidden: boolean
  j2534_status: string
  dpdu_status: string
}

export interface CodingVehicleState {
  ignition_on?: boolean
  adapter_connected?: boolean
  battery_voltage_ok?: boolean
  battery_voltage_v?: number | null
  stable_connection?: boolean
  vin_ecu_match?: boolean
  oem_spec_present?: boolean
  authorization_present?: boolean
  recovery_plan?: boolean
  operator_confirm?: boolean
  expected_vin?: string | null
  actual_vin?: string | null
  expected_ecu_sw?: string | null
  actual_ecu_sw?: string | null
}

export interface CodingRun {
  id: string
  operation_code: string
  status: string
  scenario: string | null
  data_source: string
  prerequisites: { id: string; label_de: string; met: boolean; detail_de?: string | null }[]
  checks: Record<string, unknown>
  result: Record<string, unknown>
  message_de: string | null
  abort_reason_de: string | null
  write_commands_sent: boolean
  flash_commands_sent: boolean
  auto_retry_attempted: boolean
  started_at: string
  ended_at: string | null
}

export interface EcuIdentification {
  data_source: string
  disclaimer_de: string
  vin: string | null
  ecu_id: string | null
  part_number: string | null
  software_version: string | null
  hardware_version: string | null
  coding_profile: string | null
  coding_profile_status: string
  oem_fields_available: boolean
  message_de: string
}

export interface CompatibilityCheck {
  data_source: string
  vin_match: boolean
  ecu_match: boolean
  software_compatible: boolean | null
  signature_verified: boolean | null
  voltage_ok: boolean
  voltage_v: number | null
  stable_connection: boolean
  authorization_ok: boolean
  oem_spec_ok: boolean
  recovery_plan_ok: boolean
  overall_ok: boolean
  blockers: string[]
  message_de: string
  flash_blocked: boolean
  write_blocked: boolean
}

export interface CodingInterfaces {
  j2534_status: string
  dpdu_status: string
  vendor_dll_present: boolean
  notes_de: string
  docs: string[]
}

export interface TuningModuleStatus {
  module: string
  phase: number
  status: string
  productive_activation_locked: boolean
  map_change_available: boolean
  flash_available: boolean
  emission_defeat_excluded: boolean
  disclaimer_de: string
}

export interface TuningOperation {
  code: string
  name_de: string
  category: string
  operation_type: string
  safety_class: string
  release_status: string
  enabled: boolean
  write_allowed: boolean
  map_change_allowed: boolean
  flash_allowed: boolean
  tuning_activation_allowed: boolean
  prerequisites: { id: string; label_de: string }[]
  confirmation_phrase: string | null
  timeout_seconds: number
  abort_strategy_de: string
  result_checks_de: string[]
  notes_de: string
  blockers: string[]
  requires_legal_approval: boolean
  requires_technical_review: boolean
  auto_retry_forbidden: boolean
  productive_activation_locked: boolean
  data_source: string
  oem_maps_invented: boolean
}

export interface TuningCatalog {
  data_source: string
  module_status: string
  disclaimer_de: string
  operations: TuningOperation[]
  excluded: { code: string; name_de: string; reason_de?: string; safety_class?: string }[]
  live_execution_available: boolean
  map_change_available: boolean
  flash_available: boolean
  tuning_activation_available: boolean
  hardware_live: boolean
  auto_retry_forbidden: boolean
  productive_activation_locked: boolean
  legal_gates_required: boolean
}

export interface TuningGateState {
  operator_confirm?: boolean
  legal_gate_ack?: boolean
  no_emission_defeat_ack?: boolean
  no_map_change_ack?: boolean
  legal_approval_present?: boolean
  technical_review_present?: boolean
  recovery_plan?: boolean
  oem_baseline_documented?: boolean
  hardware_suitable?: boolean
  expected_vin?: string | null
  actual_vin?: string | null
  expected_ecu_sw?: string | null
  actual_ecu_sw?: string | null
}

export interface TuningBaseline {
  id: string
  code: string
  ecu_role: string
  software_version: string
  part_number: string | null
  checksum_ref: string | null
  source_de: string
  authorization_status: string
  compatible_notes_de: string | null
  data_source: string
  created_at: string
}

export interface TuningApproval {
  id: string
  baseline_id: string | null
  vehicle_id: string | null
  doc_type: string
  title_de: string
  reference_code: string | null
  issuer_de: string | null
  status: string
  notes_de: string | null
  data_source: string
  created_at: string
}

export interface TuningHistoryEntry {
  id: string
  vehicle_id: string | null
  baseline_id: string | null
  ecu_role: string
  software_version: string
  event_type: string
  message_de: string | null
  data_source: string
  created_at: string
}

export interface TuningRun {
  id: string
  operation_code: string
  status: string
  scenario: string | null
  data_source: string
  prerequisites: { id: string; label_de: string; met: boolean; detail_de?: string | null }[]
  gates: Record<string, unknown>
  result: Record<string, unknown>
  message_de: string | null
  abort_reason_de: string | null
  map_commands_sent: boolean
  flash_commands_sent: boolean
  tuning_activated: boolean
  auto_retry_attempted: boolean
  started_at: string
  ended_at: string | null
}

export interface LegalGateCheck {
  data_source: string
  legal_approval_ok: boolean
  technical_review_ok: boolean
  recovery_plan_ok: boolean
  emission_policy_ok: boolean
  map_change_blocked: boolean
  flash_blocked: boolean
  tuning_activation_blocked: boolean
  vin_match: boolean | null
  software_compatible: boolean | null
  overall_ok: boolean
  blockers: string[]
  message_de: string
  productive_activation_locked: boolean
}

export interface LkwArchitecture {
  phase: number
  scope: string
  status: string
  title_de: string
  summary_de: string
  entitlement_granted: boolean
  entitlement_key?: string
  brand_count?: number
  blockers?: string[]
  explicitly_disabled?: string[]
  tariff_codes_planned?: string[]
  layers?: Record<string, unknown>[]
  docs?: string[]
}

export interface LkwBrand {
  slug: string
  name: string
  group: string
  release_status: string
  diagnosis_available: boolean
  voltage_note_de: string
  coverage_disclaimer_de: string
  example_models_nav_only: string[]
  protocols_planned: string[]
}

export interface LkwBrandsResponse {
  disclaimer_de: string
  count: number
  brands: LkwBrand[]
}

export interface LkwCapabilityFlag {
  id: string
  label_de: string
  status: string
  enabled: boolean
  phase: number
  blocker?: string
  notes_de?: string
}

export interface LkwCapabilities {
  disclaimer_de: string
  release_status: string
  diagnosis_enabled: boolean
  flags: LkwCapabilityFlag[]
  available: LkwCapabilityFlag[]
  unavailable: LkwCapabilityFlag[]
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
  health() {
    return request<{
      status: string
      demo_mode?: boolean
      data_source_default?: string
      message_de?: string
      version?: string
      components?: Record<string, string>
    }>('/health')
  },
  login(email: string, password: string, mfa_code?: string) {
    return request<{ access_token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        ...(mfa_code ? { mfa_code } : {}),
      }),
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
  connection(mode: 'demo' | 'live' = 'demo') {
    return request<ConnectionStatus>(`/api/connection?mode=${mode}`)
  },
  bridgeStatus() {
    return request<{
      default_mode: string
      connector: { reachable: boolean; error_de?: string; base_url?: string }
      message_de: string
    }>('/api/connector/bridge-status')
  },
  dtcs(vehicleId: string, mode: 'demo' | 'live' = 'demo') {
    return request<DtcEntry[]>(`/api/diagnostics/${vehicleId}/dtcs?mode=${mode}`)
  },
  live(vehicleId: string, mode: 'demo' | 'live' = 'demo') {
    return request<LiveData>(`/api/diagnostics/${vehicleId}/live?mode=${mode}`)
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
  createReport(
    sessionId: string,
    title: string,
    opts?: { notes?: string; recommendations?: string; auto_generate?: boolean },
  ) {
    return request<Report>('/api/reports', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        title,
        notes: opts?.notes,
        recommendations: opts?.recommendations,
        auto_generate: opts?.auto_generate ?? false,
      }),
    })
  },
  listReports(params?: { q?: string; vin?: string; include_archived?: boolean }) {
    const sp = new URLSearchParams()
    if (params?.q) sp.set('q', params.q)
    if (params?.vin) sp.set('vin', params.vin)
    if (params?.include_archived) sp.set('include_archived', 'true')
    const qs = sp.toString()
    return request<ReportSummary[]>(`/api/reports${qs ? `?${qs}` : ''}`)
  },
  getReport(reportId: string) {
    return request<Report>(`/api/reports/${reportId}`)
  },
  archiveReport(reportId: string) {
    return request<Report>(`/api/reports/${reportId}/archive`, { method: 'POST' })
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
  diagnosticSources() {
    return request<DataLicenseSource[]>('/api/diagnostic-data/sources')
  },
  diagnosticCoverage() {
    return request<DiagnosticCoverage>('/api/diagnostic-data/coverage')
  },
  diagnosticEcus() {
    return request<DiagEcu[]>('/api/diagnostic-data/ecus')
  },
  diagnosticPids() {
    return request<DiagPid[]>('/api/diagnostic-data/pids')
  },
  lookupDtc(code: string) {
    return request<DtcLookup>(`/api/diagnostic-data/dtcs/${encodeURIComponent(code)}`)
  },
  importPreview(payload: Record<string, unknown>) {
    return request<ImportPreview>('/api/diagnostic-data/import/preview', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  importApply(batchId: string) {
    return request<ImportBatch>(`/api/diagnostic-data/import/${batchId}/apply`, { method: 'POST' })
  },
  importRollback(batchId: string) {
    return request<ImportBatch>(`/api/diagnostic-data/import/${batchId}/rollback`, { method: 'POST' })
  },
  dataUpdatesDashboard() {
    return request<DataUpdatesDashboard>('/api/data-updates/dashboard')
  },
  dataUpdateChannels() {
    return request<UpdateChannel[]>('/api/data-updates/channels')
  },
  patchUpdateChannel(key: string, body: Partial<Pick<UpdateChannel, 'enabled' | 'rights_verified' | 'interval_hours' | 'auto_activate_allowed' | 'notes_de'>>) {
    return request<UpdateChannel>(`/api/data-updates/channels/${encodeURIComponent(key)}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  },
  runUpdateChannel(key: string, force = false) {
    return request<UpdateRun>(`/api/data-updates/channels/${encodeURIComponent(key)}/run`, {
      method: 'POST',
      body: JSON.stringify({ force }),
    })
  },
  approveUpdateRun(runId: string) {
    return request<UpdateRun>(`/api/data-updates/runs/${runId}/approve`, { method: 'POST' })
  },
  rejectUpdateRun(runId: string, reason_de?: string) {
    return request<UpdateRun>(`/api/data-updates/runs/${runId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason_de }),
    })
  },
  rollbackUpdateRun(runId: string) {
    return request<UpdateRun>(`/api/data-updates/runs/${runId}/rollback`, { method: 'POST' })
  },
  workshopMe() {
    return request<Workshop>('/api/workshop/me')
  },
  workshopMembers() {
    return request<WorkshopMember[]>('/api/workshop/me/members')
  },
  updateWorkshop(body: Partial<Workshop> & { logo_data_url?: string | null; clear_logo?: boolean }) {
    return request<Workshop>('/api/workshop/me', {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  },
  customers(params?: { q?: string; city?: string; include_archived?: boolean }) {
    const sp = new URLSearchParams()
    if (params?.q) sp.set('q', params.q)
    if (params?.city) sp.set('city', params.city)
    if (params?.include_archived) sp.set('include_archived', 'true')
    const qs = sp.toString()
    return request<Customer[]>(`/api/customers${qs ? `?${qs}` : ''}`)
  },
  createCustomer(body: {
    display_name: string
    email?: string | null
    phone?: string | null
    city?: string | null
    postal_code?: string | null
    country?: string | null
    notes?: string | null
    force?: boolean
  }) {
    return request<Customer>('/api/customers', { method: 'POST', body: JSON.stringify(body) })
  },
  updateCustomer(id: string, body: Partial<Customer>) {
    return request<Customer>(`/api/customers/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
  },
  mergeCustomer(targetId: string, source_customer_id: string) {
    return request<Customer>(`/api/customers/${targetId}/merge`, {
      method: 'POST',
      body: JSON.stringify({ source_customer_id }),
    })
  },
  async exportCustomer(id: string) {
    const res = await fetch(`${API_BASE}/api/customers/${id}/export`, { headers: { ...authHeader() } })
    if (!res.ok) throw new ApiError(res.status, 'Export fehlgeschlagen')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `customer-${id}.json`
    a.click()
    URL.revokeObjectURL(url)
  },
  deleteCustomer(id: string, mode: 'archive' | 'anonymize' | 'delete', force = false) {
    return request<{ status: string; customer_id: string }>(`/api/customers/${id}/delete`, {
      method: 'POST',
      body: JSON.stringify({ mode, force }),
    })
  },
  workOrders(params?: { status?: string; q?: string; customer_id?: string }) {
    const sp = new URLSearchParams()
    if (params?.status) sp.set('status', params.status)
    if (params?.q) sp.set('q', params.q)
    if (params?.customer_id) sp.set('customer_id', params.customer_id)
    const qs = sp.toString()
    return request<WorkOrder[]>(`/api/work-orders${qs ? `?${qs}` : ''}`)
  },
  createWorkOrder(body: {
    title: string
    customer_id?: string | null
    vehicle_id?: string | null
    notes?: string | null
    repair_summary?: string | null
    odometer_km?: number | null
    status?: WorkOrder['status']
  }) {
    return request<WorkOrder>('/api/work-orders', { method: 'POST', body: JSON.stringify(body) })
  },
  updateWorkOrder(id: string, body: Partial<WorkOrder>) {
    return request<WorkOrder>(`/api/work-orders/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
  },
  archiveWorkOrder(id: string) {
    return request<WorkOrder>(`/api/work-orders/${id}/archive`, { method: 'POST' })
  },
  lookupVehicleRecord(params: { vin?: string; license_plate?: string }) {
    const sp = new URLSearchParams()
    if (params.vin) sp.set('vin', params.vin)
    if (params.license_plate) sp.set('license_plate', params.license_plate)
    return request<{ query: string; matches: VehicleRecord[]; disclaimer_de: string }>(
      `/api/vehicle-records/lookup?${sp.toString()}`,
    )
  },
  vehicleRecord(vehicleId: string) {
    return request<VehicleRecord>(`/api/vehicle-records/${vehicleId}`)
  },
  vehicleMeasurements(vehicleId: string, params?: { pid?: number; limit?: number }) {
    const sp = new URLSearchParams()
    if (params?.pid != null) sp.set('pid', String(params.pid))
    if (params?.limit != null) sp.set('limit', String(params.limit))
    const qs = sp.toString()
    return request<MeasurementSeries>(
      `/api/vehicle-records/${vehicleId}/measurements${qs ? `?${qs}` : ''}`,
    )
  },
  addVehicleNote(
    vehicleId: string,
    body: {
      body: string
      note_type?: 'note' | 'service' | 'repair'
      odometer_km?: number | null
      work_order_id?: string | null
      session_id?: string | null
    },
  ) {
    return request<{ id: string; authenticity: string }>(`/api/vehicle-records/${vehicleId}/notes`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  sessionDetail(sessionId: string) {
    return request<SessionDetail>(`/api/sessions/${sessionId}`)
  },
  compareSessions(before: string, after: string) {
    return request<SessionCompare>(
      `/api/sessions/compare?before=${encodeURIComponent(before)}&after=${encodeURIComponent(after)}`,
    )
  },
  abortSession(sessionId: string, reason: string) {
    return request<SessionDetail>(`/api/sessions/${sessionId}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  },
  closeSession(sessionId: string) {
    return request<SessionSummary>(`/api/sessions/${sessionId}/close`, { method: 'POST' })
  },
  startSessionV2(body: {
    vehicle_id: string
    odometer_km?: number | null
    work_order_id?: string | null
    notes?: string | null
    idempotency_key?: string | null
    ecu_codes?: string[] | null
  }) {
    return request<SessionDetail>('/api/sessions/v2', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  serviceCatalog() {
    return request<ServiceCatalog>('/api/service/catalog')
  },
  serviceProcedure(code: string) {
    return request<ServiceProcedure>(`/api/service/procedures/${encodeURIComponent(code)}`)
  },
  startServiceRun(
    code: string,
    body: {
      vehicle_id?: string | null
      confirmation_phrase?: string | null
      vehicle_state?: ServiceVehicleState
      scenario?: 'normal' | 'missing_prereq' | 'abort' | 'comm_loss'
      acknowledge_disabled?: boolean
      acknowledge_no_oem_write?: boolean
    },
  ) {
    return request<ServiceRun>(`/api/service/procedures/${encodeURIComponent(code)}/start`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  abortServiceRun(runId: string, reason_de?: string) {
    return request<ServiceRun>(`/api/service/runs/${runId}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason_de: reason_de || 'Bedienerabbruch' }),
    })
  },
  serviceRuns() {
    return request<ServiceRun[]>('/api/service/runs')
  },
  serviceRun(id: string) {
    return request<ServiceRun>(`/api/service/runs/${id}`)
  },
  executeServiceLive(code: string) {
    return request<unknown>(`/api/service/procedures/${encodeURIComponent(code)}/execute-live`, {
      method: 'POST',
    })
  },
  guidedOverview() {
    return request<GuidedOverview>('/api/guided/overview')
  },
  measurementGroups() {
    return request<MeasurementGroup[]>('/api/guided/measurement-groups')
  },
  measurementGroup(groupId: string, vehicleId: string) {
    return request<{
      data_source: string
      group: MeasurementGroup
      readings: { name: string; value: number; unit?: string }[]
      message_de: string
    }>(`/api/guided/measurement-groups/${encodeURIComponent(groupId)}?vehicle_id=${encodeURIComponent(vehicleId)}`)
  },
  dtcHelp(code: string) {
    return request<DtcHelp>(`/api/guided/dtc/${encodeURIComponent(code)}`)
  },
  codingCatalog() {
    return request<CodingCatalog>('/api/coding/catalog')
  },
  codingOperation(code: string) {
    return request<CodingOperation>(`/api/coding/operations/${encodeURIComponent(code)}`)
  },
  codingIdentify(vehicleId?: string) {
    const qs = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : ''
    return request<EcuIdentification>(`/api/coding/identify${qs}`)
  },
  codingCompatibilityCheck(body: CodingVehicleState) {
    return request<CompatibilityCheck>('/api/coding/compatibility-check', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  codingInterfaces() {
    return request<CodingInterfaces>('/api/coding/interfaces')
  },
  startCodingRun(
    code: string,
    body: {
      vehicle_id?: string | null
      confirmation_phrase?: string | null
      vehicle_state?: CodingVehicleState
      scenario?:
        | 'normal'
        | 'missing_prereq'
        | 'abort'
        | 'comm_loss'
        | 'voltage_drop'
        | 'wrong_vehicle'
      acknowledge_disabled?: boolean
      acknowledge_no_oem_write?: boolean
      acknowledge_no_flash?: boolean
    },
  ) {
    return request<CodingRun>(`/api/coding/operations/${encodeURIComponent(code)}/start`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  abortCodingRun(runId: string, reason_de?: string) {
    return request<CodingRun>(`/api/coding/runs/${runId}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason_de: reason_de || 'Bedienerabbruch' }),
    })
  },
  codingRuns() {
    return request<CodingRun[]>('/api/coding/runs')
  },
  codingRun(id: string) {
    return request<CodingRun>(`/api/coding/runs/${id}`)
  },
  executeCodingLive(code: string) {
    return request<unknown>(`/api/coding/operations/${encodeURIComponent(code)}/execute-live`, {
      method: 'POST',
    })
  },
  executeCodingFlash(code: string) {
    return request<unknown>(`/api/coding/operations/${encodeURIComponent(code)}/flash`, {
      method: 'POST',
    })
  },
  tuningStatus() {
    return request<TuningModuleStatus>('/api/tuning/status')
  },
  tuningCatalog() {
    return request<TuningCatalog>('/api/tuning/catalog')
  },
  tuningBaselines() {
    return request<TuningBaseline[]>('/api/tuning/baselines')
  },
  createTuningBaseline(body: {
    code: string
    ecu_role?: string
    software_version: string
    part_number?: string | null
    checksum_ref?: string | null
    source_de: string
    compatible_notes_de?: string | null
    acknowledge_no_map_binary: boolean
    acknowledge_demo_only: boolean
  }) {
    return request<TuningBaseline>('/api/tuning/baselines', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  tuningApprovals() {
    return request<TuningApproval[]>('/api/tuning/approvals')
  },
  createTuningApproval(body: {
    baseline_id?: string | null
    vehicle_id?: string | null
    doc_type?: 'type_approval' | 'workshop_ack' | 'technical_review' | 'other'
    title_de: string
    reference_code?: string | null
    issuer_de?: string | null
    notes_de?: string | null
    acknowledge_not_legal_advice: boolean
    acknowledge_no_activation: boolean
  }) {
    return request<TuningApproval>('/api/tuning/approvals', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  tuningHistory(vehicleId?: string) {
    const qs = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : ''
    return request<TuningHistoryEntry[]>(`/api/tuning/history${qs}`)
  },
  tuningLegalGates(body: TuningGateState) {
    return request<LegalGateCheck>('/api/tuning/legal-gates', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  startTuningRun(
    code: string,
    body: {
      vehicle_id?: string | null
      baseline_id?: string | null
      confirmation_phrase?: string | null
      gate_state?: TuningGateState
      scenario?: 'normal' | 'missing_prereq' | 'missing_legal' | 'abort' | 'comm_loss' | 'wrong_vehicle'
      acknowledge_disabled?: boolean
      acknowledge_no_map_change?: boolean
      acknowledge_no_emission_defeat?: boolean
      acknowledge_activation_locked?: boolean
    },
  ) {
    return request<TuningRun>(`/api/tuning/operations/${encodeURIComponent(code)}/start`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  abortTuningRun(runId: string, reason_de?: string) {
    return request<TuningRun>(`/api/tuning/runs/${runId}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason_de: reason_de || 'Bedienerabbruch' }),
    })
  },
  tuningRuns() {
    return request<TuningRun[]>('/api/tuning/runs')
  },
  subscriptionPlans() {
    return request<SubscriptionPlan[]>('/api/subscriptions/plans')
  },
  mySubscription() {
    return request<SubscriptionInfo>('/api/subscriptions/me')
  },
  startTrial(plan_code = 'pkw_trial') {
    return request<SubscriptionInfo>('/api/subscriptions/me/trial', {
      method: 'POST',
      body: JSON.stringify({ plan_code }),
    })
  },
  activateStubPlan(plan_code: string, acknowledge_stub_payment: boolean) {
    return request<SubscriptionInfo>('/api/subscriptions/me/activate-stub', {
      method: 'POST',
      body: JSON.stringify({ plan_code, acknowledge_stub_payment }),
    })
  },
  cancelSubscription(at_period_end = true, reason_de?: string) {
    return request<SubscriptionInfo>('/api/subscriptions/me/cancel', {
      method: 'POST',
      body: JSON.stringify({ at_period_end, reason_de }),
    })
  },
  checkEntitlement(feature: string, for_new_operation = true) {
    const qs = `?for_new_operation=${for_new_operation ? 'true' : 'false'}`
    return request<{
      feature: string
      allowed: boolean
      subscription_status: string | null
      reason_de: string
      running_critical_ops: number
      interrupt_forbidden: boolean
    }>(`/api/subscriptions/me/entitlements/${encodeURIComponent(feature)}${qs}`)
  },
  listDevices() {
    return request<DeviceBinding[]>('/api/subscriptions/me/devices')
  },
  bindDevice(body: { device_name: string; device_fingerprint: string; platform?: string }) {
    return request<DeviceBinding>('/api/subscriptions/me/devices', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  revokeDevice(deviceId: string) {
    return request<DeviceBinding>(`/api/subscriptions/me/devices/${deviceId}/revoke`, {
      method: 'POST',
    })
  },
  listInvitations() {
    return request<Invitation[]>('/api/workshop/me/invitations')
  },
  createInvitation(email: string, role: UserRole = 'technician') {
    return request<Invitation>('/api/workshop/me/invitations', {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    })
  },
  acceptInvitation(body: { token: string; full_name: string; password: string }) {
    return request<Invitation>('/api/invitations/accept', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  registerTenant(body: {
    workshop_name: string
    admin_email: string
    admin_full_name: string
    password: string
    country?: string
    plan_code?: string
    acknowledge_demo: boolean
  }) {
    return request<{
      workshop_id: string
      user_id: string
      subscription_id: string
      message_de: string
      is_example_data: boolean
    }>('/api/tenants/register', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  billingStubInfo() {
    return request<{
      provider: string
      live_payments: boolean
      message_de: string
      legal_note_de: string
    }>('/api/billing/stub-info')
  },
  signStubWebhook(body: Record<string, unknown>) {
    return request<{
      signature: string
      header: string
      body_raw: string
      payment_note_de: string
    }>('/api/billing/demo/sign-payload', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  postStubWebhook(bodyRaw: string, signatureHeader: string) {
    return request<{
      id: string
      event_id: string
      status: string
      signature_valid: boolean
      message_de: string
      subscription: SubscriptionInfo | null
    }>('/api/billing/webhooks/mock', {
      method: 'POST',
      body: bodyRaw,
      headers: { 'X-DiagNova-Stub-Signature': signatureHeader },
    })
  },
  startCriticalOp(operation_kind: string, resource_ref: string, message_de?: string) {
    return request<{
      id: string
      status: string
      operation_kind: string
      resource_ref: string
      message_de: string | null
    }>('/api/subscriptions/me/critical-ops', {
      method: 'POST',
      body: JSON.stringify({ operation_kind, resource_ref, message_de }),
    })
  },
  finishCriticalOp(opId: string) {
    return request<{ id: string; status: string }>(
      `/api/subscriptions/me/critical-ops/${opId}/finish`,
      { method: 'POST' },
    )
  },
  adminDashboard() {
    return request<AdminDashboard>('/api/admin/dashboard')
  },
  operatorConsole() {
    return request<
      AdminDashboard & {
        console?: string
        base_path?: string
        customers?: Record<string, unknown>[]
        invoices?: Record<string, unknown>[]
        devices?: Record<string, unknown>[]
        users?: Record<string, unknown>[]
        site_settings?: Record<string, unknown>
        adapter_test_paths_de?: string[]
        rbac_de?: string
      }
    >('/api/admin/console')
  },
  mollieStatus() {
    return request<Record<string, unknown>>('/api/billing/mollie/status')
  },
  mollieConfig() {
    return request<Record<string, unknown>>('/api/billing/mollie/config')
  },
  mollieConfigSave(body: {
    api_key?: string
    webhook_secret?: string
    webhook_url?: string
    live_charges_allowed?: boolean
    clear_api_key?: boolean
    clear_webhook_secret?: boolean
  }) {
    return request<Record<string, unknown>>('/api/billing/mollie/config', {
      method: 'PUT',
      body: JSON.stringify(body),
    })
  },
  mollieConnectionTest() {
    return request<Record<string, unknown>>('/api/billing/mollie/connection-test', {
      method: 'POST',
      body: '{}',
    })
  },
  adminUsers() {
    return request<
      {
        id: string
        email: string
        full_name: string
        role: string
        workshop_id: string | null
        workshop_name: string | null
        is_active: boolean
        is_platform_admin: boolean
      }[]
    >('/api/admin/users')
  },
  adminSupport() {
    return request<{
      past_due: SubscriptionInfo[]
      pending_invitations: number
      running_critical_ops: Record<string, unknown>[]
      payment_note_de: string
      legal_open_items_de: string[]
    }>('/api/admin/support')
  },
  adminMfaStatus() {
    return request<Record<string, unknown>>('/api/admin/mfa/status')
  },
  adminMfaSetup() {
    return request<Record<string, unknown>>('/api/admin/mfa/setup', {
      method: 'POST',
      body: '{}',
    })
  },
  adminMfaConfirm(code: string) {
    return request<Record<string, unknown>>('/api/admin/mfa/confirm', {
      method: 'POST',
      body: JSON.stringify({ code }),
    })
  },
  adminHardwareProbe() {
    return request<Record<string, unknown>>('/api/admin/hardware-probe')
  },
  operatorNav() {
    return request<Record<string, unknown>>('/api/admin/operator-nav')
  },
  softwareUpdatesDashboard() {
    return request<SoftwareUpdatesDashboard>('/api/software-updates/dashboard')
  },
  softwareBusy() {
    return request<SoftwareBusyGate>('/api/software-updates/busy')
  },
  ingestSoftwarePackage(body: {
    channel_key?: string
    fixture_name: string
    claimed_sha256?: string | null
    signature_hex?: string | null
    tamper?: boolean
  }) {
    return request<SoftwarePackage>('/api/software-updates/packages/ingest', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  approveSoftwarePackage(packageId: string, force_healthcheck_fail = false) {
    return request<SoftwareRun>(`/api/software-updates/packages/${packageId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ force_healthcheck_fail }),
    })
  },
  rejectSoftwarePackage(packageId: string, reason_de?: string) {
    return request<SoftwarePackage>(`/api/software-updates/packages/${packageId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason_de }),
    })
  },
  rollbackSoftwareComponent(component: string) {
    return request<SoftwareRun>(`/api/software-updates/components/${encodeURIComponent(component)}/rollback`, {
      method: 'POST',
    })
  },
  abortSoftwareRun(runId: string, reason_de?: string) {
    return request<SoftwareRun>(`/api/software-updates/runs/${runId}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason_de }),
    })
  },
  checkSoftwareCompatibility(component: string, version: string) {
    return request<{
      compatible: boolean
      warnings_de: string[]
      violations: Record<string, unknown>[]
      installed: Record<string, string>
    }>('/api/software-updates/compatibility/check', {
      method: 'POST',
      body: JSON.stringify({ component, version }),
    })
  },
  softwareInstallerDocs() {
    return request<Record<string, unknown>>('/api/software-updates/installer-docs')
  },
  securityDashboard() {
    return request<SecurityDashboard>('/api/security/dashboard')
  },
  securityPrivacy() {
    return request<SecurityPrivacy>('/api/security/privacy')
  },
  securityBackup() {
    return request<SecurityBackup>('/api/security/backup')
  },
  securityAudit(limit = 50) {
    return request<SecurityAuditList>(`/api/security/audit?limit=${limit}`)
  },
  lkwArchitecture() {
    return request<LkwArchitecture>('/api/lkw/architecture')
  },
  lkwBrands(q?: string) {
    const qs = q ? `?q=${encodeURIComponent(q)}` : ''
    return request<LkwBrandsResponse>(`/api/lkw/brands${qs}`)
  },
  lkwCapabilities() {
    return request<LkwCapabilities>('/api/lkw/capabilities')
  },
  commerceOverview() {
    return request<{
      phase: number
      live_payments: boolean
      payment_note_de: string
      supports: string[]
      tax_review_status: string
      message_de: string
      consumer_disclaimers_de: Record<string, string>
    }>('/api/commerce/overview')
  },
  commerceAccounts() {
    return request<{ count: number; accounts: Record<string, unknown>[] }>('/api/commerce/accounts')
  },
  commerceInvoices(accountId?: string) {
    const qs = accountId ? `?account_id=${encodeURIComponent(accountId)}` : ''
    return request<{ count: number; invoices: Record<string, unknown>[] }>(`/api/commerce/invoices${qs}`)
  },
  commerceCancel(accountId: string, atPeriodEnd = true) {
    return request<Record<string, unknown>>(`/api/commerce/accounts/${accountId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ at_period_end: atPeriodEnd }),
    })
  },
  commerceInvoiceDownloadUrl(invoiceId: string) {
    return `/api/commerce/invoices/${invoiceId}/download`
  },
  logout() {
    return request<{ status: string; message_de: string }>('/api/auth/logout', { method: 'POST' })
  },
}

export { ApiError }
