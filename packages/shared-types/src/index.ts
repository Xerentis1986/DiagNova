/** Shared TypeScript contracts for DiagNova Web ↔ API (MVP). */

export type DataSource = "simulated" | "live";

export type UserRole = "admin" | "technician" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  vin: string;
  license_plate: string | null;
  engine: string | null;
  fuel_type: string | null;
  is_example_data: boolean;
  notes: string | null;
}

export type DtcStatus = "stored" | "pending" | "permanent";

export interface DtcEntry {
  code: string;
  status: DtcStatus;
  description_de: string;
  severity: "info" | "warning" | "critical";
}

export interface PidReading {
  pid: number;
  pid_hex: string;
  name: string;
  description_de: string;
  value: number;
  unit: string;
  timestamp: string;
}

export interface DiagnosticSessionSummary {
  id: string;
  vehicle_id: string;
  vehicle_label: string;
  started_at: string;
  ended_at: string | null;
  data_source: DataSource;
  dtc_count: number;
  status: "open" | "closed";
}

export interface ConnectionStatus {
  connected: boolean;
  mode: "simulator" | "connector" | "none";
  adapter_name: string;
  data_source: DataSource;
  message_de: string;
  last_heartbeat: string | null;
}

export const PLANNED_MODULES = [
  { id: "ecu", label: "Steuergeräte", status: "planned" as const },
  { id: "service", label: "Servicefunktionen", status: "planned" as const },
  { id: "coding", label: "Codierung", status: "planned" as const },
  { id: "actuator", label: "Stellglieddiagnose", status: "planned" as const },
  { id: "flash", label: "Programmierung", status: "planned" as const },
] as const;
