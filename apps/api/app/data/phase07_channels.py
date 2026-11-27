"""Seed-Update-Kanäle Phase 07 – standardmäßig deaktiviert, keine kommerziellen Feeds."""

from __future__ import annotations

# Keine erfundenen kommerziellen Quellen. Fixture-Kanäle nur für Demo/Tests.
# HTTPS-Platzhalter bleiben disabled + rights_verified=False.

PHASE07_CHANNELS: list[dict] = [
    {
        "key": "sim-dtc-descriptive",
        "name": "Simulation: beschreibende DTC-Texte",
        "fetch_mode": "fixture",
        "url": "fixture://phase07_update_new.json",
        "enabled": False,
        "rights_verified": True,  # Fixture ist intern/simuliert
        "interval_hours": 24,
        "expected_license": "DiagNova structural",
        "source_key": "diagnova-structural",
        "content_kind": "dtc_descriptive",
        "auto_activate_allowed": True,
        "max_bytes": 500_000,
        "require_signature": True,
        "signature_key_id": "demo-hmac",
        "notes_de": (
            "Nur Simulation. Demo-DTC-Texte sind klar als simuliert gekennzeichnet. "
            "Kein kommerzieller Feed. Standard: deaktiviert."
        ),
    },
    {
        "key": "sim-procedures",
        "name": "Simulation: Serviceprozeduren",
        "fetch_mode": "fixture",
        "url": "fixture://phase07_update_procedures.json",
        "enabled": False,
        "rights_verified": True,
        "interval_hours": 24,
        "expected_license": "DiagNova structural",
        "source_key": "diagnova-structural",
        "content_kind": "procedures",
        "auto_activate_allowed": False,
        "max_bytes": 500_000,
        "require_signature": False,
        "signature_key_id": None,
        "notes_de": "Prozeduren immer manuelle Freigabe. Keine OEM-Schritte.",
    },
    {
        "key": "sim-ecu-addresses",
        "name": "Simulation: ECU-Adressen",
        "fetch_mode": "fixture",
        "url": "fixture://phase07_update_addresses.json",
        "enabled": False,
        "rights_verified": True,
        "interval_hours": 24,
        "expected_license": "DiagNova structural",
        "source_key": "diagnova-structural",
        "content_kind": "addresses",
        "auto_activate_allowed": False,
        "max_bytes": 500_000,
        "require_signature": False,
        "signature_key_id": None,
        "notes_de": "Adressen/sicherheitsrelevante Definitionen → manuelle Freigabe.",
    },
    {
        "key": "https-placeholder-disabled",
        "name": "HTTPS-Platzhalter (nicht aktiv)",
        "fetch_mode": "https",
        "url": "https://updates.example.invalid/diagnova/diagnostic-data.json",
        "enabled": False,
        "rights_verified": False,
        "interval_hours": 24,
        "expected_license": "pending-rights-review",
        "source_key": "diagnova-structural",
        "content_kind": "mixed",
        "auto_activate_allowed": False,
        "max_bytes": 2_000_000,
        "require_signature": True,
        "signature_key_id": "demo-hmac",
        "notes_de": (
            "Kein echter Feed. example.invalid ist bewusst ungültig. "
            "Erst nach Rechteprüfung und Allowlist-Freigabe aktivierbar."
        ),
    },
]
