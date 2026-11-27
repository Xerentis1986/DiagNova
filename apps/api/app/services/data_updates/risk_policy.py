"""Risikopolitik: Auto-Aktivierung nur für risikoarme beschreibende Daten."""

from __future__ import annotations

from typing import Any

from app.services.data_updates.integrity import package_risk_flags

# content_kind → darf auto aktiviert werden, wenn Kanal auto_activate_allowed=True
AUTO_SAFE_KINDS = frozenset({"dtc_descriptive"})


def requires_manual_approval(
    *,
    content_kind: str,
    auto_activate_allowed: bool,
    payload: dict[str, Any],
    license_changed: bool,
    signature_required: bool,
    signature_ok: bool | None,
) -> tuple[bool, str]:
    """
    Returns (needs_manual, reason_de).
    Ausführbare Prozeduren, Adressen und sicherheitsrelevante Definitionen → immer manuell.
    Lizenzwechsel → immer manuell.
    Fehlende/ungültige Signatur wenn erforderlich → manuell (bzw. fail earlier).
    """
    if license_changed:
        return True, "Lizenzänderung erkannt – manuelle Freigabe erforderlich."

    if signature_required and signature_ok is not True:
        return True, "Signatur fehlt oder ungültig – manuelle Freigabe gesperrt."

    flags = package_risk_flags(payload)
    if flags["has_procedures"]:
        return True, "Serviceprozeduren erfordern manuelle Freigabe."
    if flags["has_ecu_addresses"]:
        return True, "ECU-Adressen/Definitionen erfordern manuelle Freigabe."

    if not auto_activate_allowed:
        return True, "Kanal erlaubt keine Auto-Aktivierung."

    if content_kind not in AUTO_SAFE_KINDS:
        return True, f"content_kind '{content_kind}' ist nicht auto-aktivierbar."

    # Nur beschreibende DTC-Texte (oder leere strukturelle Ergänzungen ohne Adressen)
    if flags["has_dtc_descriptive_text"] and not flags["has_procedures"] and not flags["has_ecu_addresses"]:
        return False, "Risikoarm: beschreibende DTC-Texte – Auto-Aktivierung erlaubt."

    # Rein strukturell ohne Adressen/Prozeduren und ohne Texte: trotzdem manuell, außer kind=dtc_descriptive
    if content_kind == "dtc_descriptive" and not flags["has_procedures"] and not flags["has_ecu_addresses"]:
        return False, "Risikoarm: DTC-beschreibender Kanal ohne sicherheitsrelevante Definitionen."

    return True, "Inhalt erfordert manuelle Admin-Freigabe."
