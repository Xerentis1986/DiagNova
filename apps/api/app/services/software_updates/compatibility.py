"""Kompatibilitätsmatrix für API / Web / Connector."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.software_versions import COMPATIBILITY_MATRIX
from app.models.software_updates import SoftwareCompatibilityRule, SoftwareComponent


def _parse_tuple(v: str) -> tuple[int, ...] | None:
    try:
        parts = []
        for p in v.strip().split("."):
            # Pre-Release-Suffix ignorieren (z. B. 1.0.0-rc1 → 1.0.0)
            num = "".join(ch for ch in p if ch.isdigit())
            if num == "":
                return None
            parts.append(int(num))
        return tuple(parts) if parts else None
    except ValueError:
        return None


def _satisfies(installed: str, required: str) -> bool:
    """required ist Mindestversion (installed >= required)."""
    a = _parse_tuple(installed)
    b = _parse_tuple(required)
    if a is None or b is None:
        return installed == required
    # Auf gleiche Länge auffüllen
    n = max(len(a), len(b))
    a = a + (0,) * (n - len(a))
    b = b + (0,) * (n - len(b))
    return a >= b


def check_compatibility(
    db: Session,
    *,
    component: str,
    target_version: str,
    proposed_versions: dict[str, str] | None = None,
) -> dict:
    """Prüft ob target_version mit aktuell installierten Partnern kompatibel ist.

    proposed_versions kann geplante Versionen überschreiben (z. B. simultane Updates).
    """
    installed: dict[str, str] = {}
    for row in db.scalars(select(SoftwareComponent)).all():
        installed[row.key] = row.current_version
    if proposed_versions:
        installed.update(proposed_versions)
    # Zielkomponente auf Zielversion setzen
    installed[component] = target_version

    rules = list(db.scalars(select(SoftwareCompatibilityRule)).all())
    if not rules:
        # Fallback auf statische Matrix
        matrix = COMPATIBILITY_MATRIX
    else:
        import json

        matrix = [
            {
                "id": r.id,
                "component": r.component,
                "version": r.version,
                "requires": json.loads(r.requires_json or "{}"),
                "notes_de": r.notes_de,
            }
            for r in rules
        ]

    applicable = [
        r for r in matrix if r["component"] == component and r["version"] == target_version
    ]
    if not applicable:
        # Keine Regel = vorsichtig erlauben, aber warnen
        return {
            "compatible": True,
            "warnings_de": [
                f"Keine Kompatibilitätsregel für {component}@{target_version} – manuell prüfen."
            ],
            "violations": [],
            "installed": installed,
        }

    violations: list[dict] = []
    for rule in applicable:
        for req_comp, req_ver in (rule.get("requires") or {}).items():
            cur = installed.get(req_comp)
            if cur is None:
                violations.append(
                    {
                        "rule_id": rule["id"],
                        "requires_component": req_comp,
                        "requires_version": req_ver,
                        "installed": None,
                        "detail_de": f"{req_comp} nicht installiert, benötigt ≥ {req_ver}.",
                    }
                )
            elif not _satisfies(cur, req_ver):
                violations.append(
                    {
                        "rule_id": rule["id"],
                        "requires_component": req_comp,
                        "requires_version": req_ver,
                        "installed": cur,
                        "detail_de": (
                            f"Inkompatibel: {component}@{target_version} braucht "
                            f"{req_comp}≥{req_ver}, installiert ist {cur}."
                        ),
                    }
                )

    return {
        "compatible": len(violations) == 0,
        "warnings_de": [],
        "violations": violations,
        "installed": installed,
        "rules_checked": [r["id"] for r in applicable],
    }
