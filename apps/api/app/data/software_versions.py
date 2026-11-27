"""Komponentenversionen, Kompatibilitätsmatrix, Migrationsplan.

Software-Updates sind strikt getrennt von Diagnosedaten-Updates (Phase 07).
Phase 15: Versionen 0.15.x (Security/Datenschutz/QA).
"""

from __future__ import annotations

# SemVer der aktuellen Build-Linie (simuliert / Demo).
COMPONENT_VERSIONS: dict[str, str] = {
    "api": "0.15.0",
    "web": "0.15.0",
    "connector": "0.15.0",
}

COMPONENT_LABELS_DE: dict[str, str] = {
    "api": "DiagNova API",
    "web": "DiagNova Web",
    "connector": "Windows-Connector",
}

# Mindest-Kompatibilität: Zielkomponente → erforderliche Partnerversionen.
COMPATIBILITY_MATRIX: list[dict] = [
    {
        "id": "web-0.14-requires-api",
        "component": "web",
        "version": "0.14.0",
        "requires": {"api": "0.14.0"},
        "notes_de": "Web 0.14 erwartet API 0.14 (Schema/Entitlements).",
    },
    {
        "id": "connector-0.14-requires-api",
        "component": "connector",
        "version": "0.14.0",
        "requires": {"api": "0.13.0"},
        "notes_de": "Connector 0.14 akzeptiert API ab 0.13 (Update-Endpunkte optional).",
    },
    {
        "id": "api-0.14-requires-web-min",
        "component": "api",
        "version": "0.14.0",
        "requires": {"web": "0.13.0"},
        "notes_de": "API 0.14 bleibt mit Web 0.13 lesekompatibel.",
    },
    {
        "id": "web-0.15-requires-api",
        "component": "web",
        "version": "0.15.0",
        "requires": {"api": "0.15.0"},
        "notes_de": "Web 0.15 erwartet API 0.15 (Security-Dashboard).",
    },
    {
        "id": "web-0.15.1-requires-api",
        "component": "web",
        "version": "0.15.1",
        "requires": {"api": "0.15.0"},
        "notes_de": "Patch Web 0.15.1 kompatibel zu API 0.15.",
    },
    {
        "id": "connector-0.15-requires-api",
        "component": "connector",
        "version": "0.15.0",
        "requires": {"api": "0.14.0"},
        "notes_de": "Connector 0.15 akzeptiert API ab 0.14.",
    },
    {
        "id": "connector-0.15.1-requires-api",
        "component": "connector",
        "version": "0.15.1",
        "requires": {"api": "0.15.0"},
        "notes_de": "Patch Connector 0.15.1.",
    },
    {
        "id": "api-0.15-requires-web-min",
        "component": "api",
        "version": "0.15.0",
        "requires": {"web": "0.14.0"},
        "notes_de": "API 0.15 lesekompatibel mit Web ab 0.14; Security-UI braucht 0.15.",
    },
    {
        "id": "web-0.16-requires-api-0.16",
        "component": "web",
        "version": "0.16.0",
        "requires": {"api": "0.16.0"},
        "notes_de": "Demo-Inkompatibilität für Abnahmetests (Phase 15).",
    },
    {
        "id": "connector-0.16-requires-api-0.16",
        "component": "connector",
        "version": "0.16.0",
        "requires": {"api": "0.16.0"},
        "notes_de": "Demo-Inkompatibilität für Abnahmetests.",
    },
]

# Alembic-/DB-Migrationsplan inkl. Backup/Restore (Dokumentation, keine Auto-Migration).
DB_MIGRATION_PLAN: list[dict] = [
    {
        "revision": "011_phase14",
        "from_revision": "010_phase13",
        "backup_required": True,
        "backup_steps_de": [
            "pg_dump vor alembic upgrade (oder Plesk-DB-Backup).",
            "Dump-Datei mit Zeitstempel und Revision kennzeichnen.",
            "Integrität des Dumps prüfen (Dateigröße / pg_restore --list).",
        ],
        "restore_steps_de": [
            "API/Web stoppen bzw. Wartungsmodus.",
            "pg_restore aus dem Backup vor der fehlgeschlagenen Migration.",
            "Alembic-Versionstabelle auf bekannten Stand setzen falls nötig.",
            "Healthcheck /health und Admin-Versionsanzeige prüfen.",
        ],
        "notes_de": "Phase-14-Tabellen für Software-Updates. Kein Prod-Deploy ohne Backup.",
    },
    {
        "revision": "012_phase15",
        "from_revision": "011_phase14",
        "backup_required": True,
        "backup_steps_de": [
            "pg_dump vor alembic upgrade.",
            "Security-/Audit-Konfiguration (JWT_SECRET, CORS) separat sichern – nicht in Dump committen.",
        ],
        "restore_steps_de": [
            "Restore DB-Dump.",
            "JWT_SECRET und CORS_ORIGINS aus Secret-Store wiederherstellen.",
            "GET /health und /api/security/dashboard prüfen.",
        ],
        "notes_de": "Phase 15: Audit-Metadaten optional; App-Logik primär. Backup vor Deploy.",
    },
]

UPDATE_CHANNELS_SEED: list[dict] = [
    {
        "key": "stable-fixture",
        "name": "Stable (Simulation/Fixture)",
        "channel_type": "stable",
        "fetch_mode": "fixture",
        "enabled": True,
        "auto_install_allowed": False,
        "require_signature": True,
        "require_signing_cert": False,
        "notes_de": (
            "Simulierter Stable-Kanal. Keine ungeprüften Auto-Installs. "
            "Admin-Freigabe Pflicht. Getrennt von Diagnosedaten-Updates."
        ),
    },
    {
        "key": "production-blocked",
        "name": "Production (gesperrt ohne Zertifikat)",
        "channel_type": "production",
        "fetch_mode": "https",
        "enabled": True,
        "auto_install_allowed": False,
        "require_signature": True,
        "require_signing_cert": True,
        "notes_de": (
            "Produktive Auto-Updates gesperrt, solange kein Signaturzertifikat "
            "konfiguriert ist (software_update_signing_cert_configured=false)."
        ),
    },
]

DISCLAIMER_DE = (
    "Software-Updates (API/Web/Connector) sind von Diagnosedaten-Updates getrennt. "
    "Keine ungeprüften Auto-Installs. Signatur/Checksum Pflicht. "
    "Während Diagnose, Service oder Flash/Codierung sind Installationen gesperrt. "
    "Produktive Auto-Updates ohne Signaturzertifikat deaktiviert. Simulation/Demo."
)
