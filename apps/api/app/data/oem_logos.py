"""Zuordnung Katalog-Slug → Original-Herstellerlogo-Paket (brands.json).

Nur bestehende DACH-Katalogmarken; keine neuen Marken ohne Diagnosedaten.
Statische Assets liegen unter apps/web/public/oem-logos/.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_PKG = Path(__file__).with_name("oem_logo_brands.json")

# Katalog-Slug → Paket-ID (wenn abweichend)
_SLUG_TO_ASSET: dict[str, str] = {
    "vw": "volkswagen",
    "ds": "ds-automobiles",
}


@lru_cache(maxsize=1)
def _index() -> dict[str, dict[str, Any]]:
    raw = json.loads(_PKG.read_text(encoding="utf-8"))
    return {row["id"]: row for row in raw}


def asset_id_for_slug(slug: str) -> str | None:
    return _SLUG_TO_ASSET.get(slug, slug)


def logo_fields_for_slug(slug: str) -> dict[str, Any] | None:
    """Liefert logo_url / tiles für eine Katalogmarke oder None."""
    asset_id = asset_id_for_slug(slug)
    if not asset_id:
        return None
    row = _index().get(asset_id)
    if not row or not row.get("originalLogoIncluded"):
        return None
    base = "/oem-logos"
    logo = row["logo"]  # z. B. logos/volkswagen.svg
    return {
        "logo_mode": "image",
        "logo_rights_cleared": True,
        "logo_asset_id": asset_id,
        "logo_url": f"{base}/{logo}",
        "logo_tile_light": f"{base}/{row['tileLight']}",
        "logo_tile_dark": f"{base}/{row['tileDark']}",
    }
