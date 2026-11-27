# Diagnosedatenmodell (Phase 06)

Versionierte Entities mit Pflicht-Herkunft (`source_id` → `data_license_sources`).

## Entitäten

| Tabelle | Inhalt |
|---------|--------|
| `data_license_sources` | URL, Version, Lizenz, commercial_use, Attribution, checked_at |
| `diag_dataset_versions` | Version-Label, Status (draft/published/rolled_back) |
| `diag_manufacturers` / `diag_models` / `diag_variants` | Hersteller → Modell → Variante (Jahre, Motor) |
| `diag_ecu_definitions` | ECU, Protokoll, Request/Response, Softwarevariante |
| `diag_dtc_definitions` | DTC-Code, Beschreibung (nullable), description_status |
| `diag_pid_definitions` | PID/DID, Einheit, Umrechnungsformel |
| `diag_unit_definitions` | Einheiten |
| `diag_service_procedures` | Service mit `prerequisites_json`; `enabled` default false |
| `import_batches` | preview / quarantine / applied / rolled_back / rejected |
| `import_quarantine_items` | abgelehnte Zeilen + Grund |
| `import_applied_records` | Entity-IDs für Rollback |

## Scopes

- `generic` – OBD/ISO-Standard, strukturell
- `oem` – nur mit redistributable Lizenzquelle

## Importfluss

1. **Preview** (JSON oder CSV) – Schema-Validierung, Dubletten, Blocklist
2. Fehler → **Quarantäne** (`can_apply=false`)
3. **Apply** – Transaktion + Dataset-Version `published`
4. **Rollback** – löscht alle `import_applied_records` dieses Batches

ODX/PDX: Endpoint vorhanden, antwortet **403**.

## API (Auszug)

| Methode | Pfad |
|---------|------|
| GET | `/api/diagnostic-data/sources` |
| GET | `/api/diagnostic-data/dtcs/{code}` |
| GET | `/api/diagnostic-data/pids` · `/ecus` · `/coverage` |
| POST | `/api/diagnostic-data/import/preview` |
| POST | `/api/diagnostic-data/import/preview-csv` |
| POST | `/api/diagnostic-data/import/{id}/apply` |
| POST | `/api/diagnostic-data/import/{id}/rollback` |
| POST | `/api/diagnostic-data/import/odx` → 403 |

Migration: `003_phase06`.
