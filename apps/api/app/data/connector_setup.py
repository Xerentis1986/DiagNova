"""Kunden-Frontend: legale Connector-Installation & LIVE-Assistent (kein OEM-Raubkopie-Pfad)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Phase-24 UNSIGNED Inno-Artefakt (CI). EXE nicht im Git – Operator legt sie unter /downloads ab.
INSTALLER_FILENAME = "DiagNovaConnectorSetup-0.23.0-unsigned.exe"
INSTALLER_VERSION = "0.23.0"
INSTALLER_SHA256 = "b6c4bcb53938ca4f3d2e6c409f2633225a7df41a2296ca6887d957148024f0a9"
INSTALLER_SIZE_BYTES = 32_294_999
INSTALLER_PUBLIC_PATH = f"/downloads/{INSTALLER_FILENAME}"
INSTALLER_SIGNING = "UNSIGNED"

LEGAL_NOTICE_DE = (
    "Nur legale Wege: Windows-Connector (UNSIGNED Setup), Vgate iCar Pro 2S (BT/ELM) "
    "und/oder CDP+, Standard-OBD-II (SAE J1979). Keine Darknet-/OEM-Raubkopien, "
    "keine unlizenzierte Firmware, keine SERMI-Umgehung. OEM-Diagnose/Coding nur über "
    "Hersteller-Portale und lizenzierte Verträge."
)

INSTALL_STEPS_DE: list[str] = [
    "UNSIGNED-Installer DiagNovaConnectorSetup herunterladen (nur aus diesem DiagNova-Kanal).",
    "SHA-256 der EXE mit der Anzeige in dieser UI vergleichen.",
    "Unter Windows ausführen. SmartScreen kann UNSIGNED warnen – erwartbar ohne Code-Signing.",
    "Connector starten (Startmenü / DiagNova Connector). Loopback: http://127.0.0.1:8765.",
    "Im Browser GET /health und /version am Connector prüfen (lokal).",
    "Mit DiagNova-Web pairen (Origin-Allowlist / Pairing-Token laut Connector-UI).",
]

PAIRING_STEPS_DE: list[str] = [
    "Connector läuft und zeigt Pairing/Health auf dem Werkstatt-PC.",
    "In DiagNova unter „Connector & LIVE“ den LIVE-Modus wählen (kein DEMO-Fallback).",
    "Adapter anschließen: Vgate iCar Pro 2S per Bluetooth (SPP/COM) oder CDP+ per USB.",
    "Adapter in der Connector-Inventur auswählen und Verbindungstest starten.",
    "OBD-II-Stecker am Fahrzeug, Zündung ein; dann OBD-Init / VIN / DTCs in der Diagnose.",
]

LIVE_CHECKLIST_DE: list[dict[str, str]] = [
    {
        "id": "connector_running",
        "title_de": "Windows-Connector läuft",
        "hint_de": "Loopback 127.0.0.1:8765 erreichbar; Health/Version OK.",
    },
    {
        "id": "adapter_detected",
        "title_de": "Adapter erkannt",
        "hint_de": "Vgate iCar Pro 2S (BT/ELM) oder CDP+ in der Inventur sichtbar.",
    },
    {
        "id": "live_mode",
        "title_de": "LIVE-Modus aktiv",
        "hint_de": "In der Diagnose LIVE wählen – kein Simulator-Fallback bei Fehlern.",
    },
    {
        "id": "adapter_path",
        "title_de": "BT/Vgate oder CDP+",
        "hint_de": "Nur dokumentierte Adapterpfade; OBD-DIAG ohne Inventur nicht erzwingen.",
    },
    {
        "id": "obd_basics",
        "title_de": "OBD-II Basics",
        "hint_de": "VIN, DTCs, Readiness, Freeze Frame, Live-PIDs (SAE J1979).",
    },
]

ADAPTER_HINTS_DE: list[dict[str, str]] = [
    {
        "id": "vgate-icar-pro-2s",
        "label_de": "Vgate iCar Pro 2S (Bluetooth / ELM327)",
        "notes_de": "ELM327-kompatibel, ca. ≤ 100 €. Pairing über Windows-BT → COM/SPP.",
    },
    {
        "id": "cdp-plus",
        "label_de": "Delphi/Autocom CDP+",
        "notes_de": "USB; Safe-Reads wo implementiert. Keine erfundenen Protokolle.",
    },
]


def _installer_candidates() -> list[Path]:
    """Mögliche Ablageorte der UNSIGNED EXE (Deploy / Dev)."""
    here = Path(__file__).resolve()
    repo = here.parents[4]  # apps/api/app/data → repo root
    return [
        Path("/usr/share/nginx/html/downloads") / INSTALLER_FILENAME,
        repo / "apps" / "web" / "public" / "downloads" / INSTALLER_FILENAME,
        Path("/opt/diagnova/downloads") / INSTALLER_FILENAME,
        Path("/opt/cursor/artifacts") / INSTALLER_FILENAME,
    ]


def installer_present() -> dict[str, Any]:
    for path in _installer_candidates():
        if path.is_file():
            return {
                "available": True,
                "path_hint": str(path),
                "size_bytes": path.stat().st_size,
            }
    return {
        "available": False,
        "path_hint": None,
        "size_bytes": None,
        "operator_de": (
            "Installer-Datei fehlt lokal. Operator: UNSIGNED EXE aus CI-Artefakt "
            f"„diagnova-connector-installer-unsigned“ nach apps/web/public/downloads/ "
            f"bzw. Server /opt/diagnova/downloads/ als {INSTALLER_FILENAME} legen und Web neu bauen/deployen."
        ),
    }


def setup_guide_payload() -> dict[str, Any]:
    present = installer_present()
    return {
        "title_de": "Windows-Connector & LIVE-Start",
        "legal_notice_de": LEGAL_NOTICE_DE,
        "signing": INSTALLER_SIGNING,
        "installer": {
            "filename": INSTALLER_FILENAME,
            "version": INSTALLER_VERSION,
            "sha256": INSTALLER_SHA256,
            "size_bytes_expected": INSTALLER_SIZE_BYTES,
            "download_path": INSTALLER_PUBLIC_PATH,
            "signing": INSTALLER_SIGNING,
            "available": present["available"],
            "size_bytes_on_disk": present.get("size_bytes"),
            "operator_de": present.get("operator_de"),
        },
        "install_steps_de": INSTALL_STEPS_DE,
        "pairing_steps_de": PAIRING_STEPS_DE,
        "live_checklist": LIVE_CHECKLIST_DE,
        "adapters": ADAPTER_HINTS_DE,
        "obd_basics_de": [
            "VIN lesen",
            "DTCs (gespeichert / pending / permanent)",
            "Readiness-Monitore",
            "Freeze Frame",
            "Live-PIDs (u. a. RPM, Geschwindigkeit, Kühlmittel)",
        ],
        "ui_separation_de": (
            "Kunden-Frontend: Diagnose & Connector-Hilfe. Betreiberkonsole /operator: "
            "Verwaltung, Mollie, Hardware-Probe – getrennt."
        ),
        "docs_ref": "docs/connector-installer.md",
    }
