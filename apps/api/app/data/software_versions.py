"""Phase 14 – Komponentenversionen, Kompatibilitätsmatrix, Migrationsplan.

Software-Updates sind strikt getrennt von Diagnosedaten-Updates (Phase 07).
"""

from __future__ import annotations

# SemVer der aktuellen Build-Linie (simuliert / Demo).
COMPONENT_VERSIONS: dict[str, str] = {
    "api": "0.14.0",
    "web": "0.14.0",
    "connector": "0.14.0",
}

COMPONENT_LABELS_DE: dict[str, str] = {
    "api": "DiagNova API",
    "web": "DiagNova Web",
    "connector": "Windows-Connector",
}

# Mindest-Kompatibilität: Zielkomponente → erforderliche Partnerversionen.
# Format requires: { component: "x.y.z" } (exakt oder als Untergrenze via parse).
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
        "notes_de": "API 0.14 bleibt mit Web 0.13 lesekompatibel; Admin-UI Updates braucht 0.14.",
    },
    {
        "id": "web-0.15-requires-api-0.15",
        "component": "web",
        "version": "0.15.0",
        "requires": {"api": "0.15.0"},
        "notes_de": "Zukünftiges Demo-Paket – inkompatibel mit aktueller API 0.14.",
    },
    {
        "id": "connector-0.15-requires-api-0.15",
        "component": "connector",
        "version": "0.15.0",
        "requires": {"api": "0.15.0"},
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
        "require_signing_cert": False,  # Demo-HMAC reicht für Simulation
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
        "enabled": True,  # sichtbar, aber Install/Ingest ohne Zertifikat → rejected
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
