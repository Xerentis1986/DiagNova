"""Automotive-Quellenkatalog (447 Einstiege) – Übersicht, Probe, Import-Hinweise.

Keine Secrets. Keine Live-Flash/Schreibdiagnose. Lizenzklarheit vor Redistribution.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

_DATA = Path(__file__).resolve().parents[1] / "data"
_CATALOG_PATH = _DATA / "automotive_quellenkatalog.json"
_FIXTURES = _DATA / "automotive_fixtures"

# Priorisierte Open-Data-Ziele (kostenlos, lizenzklar oder klar dokumentiert)
PRIORITY_PROBES: list[dict[str, str]] = [
    {
        "catalog_id": "M0268",
        "name": "OBDex JSON",
        "url": "https://foerbsnavi.github.io/OBDex/generic.min.json",
        "license": "CC0-1.0",
        "role": "dtc_bulk",
    },
    {
        "catalog_id": "M0266",
        "name": "OBDb Toyota Prius",
        "url": "https://raw.githubusercontent.com/OBDb/Toyota-Prius/main/signalsets/v3/default.json",
        "license": "CC BY-SA 4.0",
        "role": "signalset",
    },
    {
        "catalog_id": "M0267",
        "name": "OBDb Ford Focus",
        "url": "https://raw.githubusercontent.com/OBDb/Ford-Focus/main/signalsets/v3/default.json",
        "license": "CC BY-SA 4.0",
        "role": "signalset",
    },
    {
        "catalog_id": "M0269",
        "name": "Wal33D DTC SQLite",
        "url": "https://raw.githubusercontent.com/Wal33D/dtc-database/main/data/dtc_codes.db",
        "license": "check_repo",
        "role": "dtc_sqlite",
    },
    {
        "catalog_id": "M0265",
        "name": "python-obd Command Tables",
        "url": "https://python-obd.readthedocs.io/en/latest/Command%20Tables/",
        "license": "GPL-ref",
        "role": "pid_docs",
    },
    {
        "catalog_id": "M0077",
        "name": "OpenDBC",
        "url": "https://github.com/commaai/opendbc",
        "license": "MIT",
        "role": "dbc",
    },
]


def catalog_path() -> Path:
    return _CATALOG_PATH


def load_catalog() -> dict[str, Any]:
    raw = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "sources" not in raw:
        raise ValueError("Katalogformat ungültig")
    return raw


def catalog_summary() -> dict[str, Any]:
    cat = load_catalog()
    sources = cat.get("sources") or []
    by_cat: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for s in sources:
        c = str(s.get("category") or "unbekannt")
        t = str(s.get("type") or "unbekannt") or "unbekannt"
        by_cat[c] = by_cat.get(c, 0) + 1
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "title": cat.get("title"),
        "note": cat.get("note"),
        "source_count": len(sources),
        "categories": len(by_cat),
        "by_category": dict(sorted(by_cat.items(), key=lambda x: -x[1])),
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "catalog_path": str(_CATALOG_PATH.name),
        "write_diag_flash": "gesperrt",
        "commercial_orders": "verboten_ohne_freigabe",
        "secrets_in_repo": False,
    }


def list_sources(
    *,
    category: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    sources = load_catalog().get("sources") or []
    qn = (q or "").strip().lower()
    out = []
    for s in sources:
        if category and str(s.get("category") or "") != category:
            continue
        blob = f"{s.get('name')}|{s.get('url')}|{s.get('scope')}|{s.get('catalog_id')}".lower()
        if qn and qn not in blob:
            continue
        out.append(
            {
                "catalog_id": s.get("catalog_id"),
                "name": s.get("name"),
                "category": s.get("category"),
                "url": s.get("url"),
                "scope": s.get("scope"),
                "type": s.get("type"),
                "previous_verification": s.get("previous_verification"),
                "reference_ids": s.get("reference_ids"),
            }
        )
    total = len(out)
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {"total": total, "offset": offset, "limit": limit, "items": out[offset : offset + limit]}


def probe_url(url: str, *, timeout: float = 15.0) -> dict[str, Any]:
    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            # HEAD first; some hosts dislike HEAD → GET range
            try:
                resp = client.head(url)
                if resp.status_code >= 400 or resp.status_code == 405:
                    resp = client.get(url, headers={"Range": "bytes=0-2047"})
            except httpx.HTTPError:
                resp = client.get(url, headers={"Range": "bytes=0-2047"})
        ms = int((time.monotonic() - t0) * 1000)
        return {
            "url": url,
            "ok": resp.status_code < 400,
            "http_status": resp.status_code,
            "elapsed_ms": ms,
            "content_type": resp.headers.get("content-type"),
            "bytes_seen": len(resp.content or b""),
        }
    except httpx.HTTPError as exc:
        return {
            "url": url,
            "ok": False,
            "http_status": None,
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
            "error_de": str(exc)[:300],
        }


def probe_priority(*, live: bool = True) -> dict[str, Any]:
    results = []
    if not live:
        return {
            "live": False,
            "results": [],
            "message_de": "Live-Probe deaktiviert (live=false).",
        }
    for item in PRIORITY_PROBES:
        r = probe_url(item["url"])
        results.append({**item, **r})
    ok_n = sum(1 for r in results if r.get("ok"))
    return {
        "live": True,
        "probed": len(results),
        "reachable": ok_n,
        "results": results,
        "message_de": f"{ok_n}/{len(results)} Prioritätsquellen erreichbar (Stand Probe).",
        "blockers_note_de": (
            "OEM-Portale, kommerzielle APIs und zahlungspflichtige Pakete bleiben blockiert "
            "ohne Betreiber-Freigabe/Kostenfreigabe. Keine Schreibdiagnose/Flash."
        ),
    }


def fixture_import_package() -> dict[str, Any]:
    path = _FIXTURES / "import_obdex_sample_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_status() -> dict[str, Any]:
    files = []
    if _FIXTURES.is_dir():
        for p in sorted(_FIXTURES.glob("*")):
            files.append({"name": p.name, "bytes": p.stat().st_size})
    return {
        "fixtures_dir": "apps/api/app/data/automotive_fixtures",
        "files": files,
        "import_package": "import_obdex_sample_v1.json",
        "obdex_sample_dtcs": 200,
        "obdb_prius": "metadata_only_v1",
        "write_enabled": False,
    }


def coverage_matrix_stub() -> dict[str, Any]:
    """Ehrliche Abdeckung – keine Vollständigkeitsbehauptung."""
    return {
        "areas_documented": 46,
        "areas_fully_covered": 0,
        "partial": [
            "B01 OBD-II PID/DTC generisch (SAE + OBDex Sample)",
            "B02 Signalsets OBDb (Metadaten Prius/Focus; Bulk BY-SA Attribution folgt)",
        ],
        "blocked": [
            "OEM RMI / SERMI / Secure Gateway – Portal/Auth",
            "Firmware/Flash – gesperrt bis Freigabe",
            "Kostenpflichtige MechanicDB/ALLDATA/Autodata – keine Bestellung",
            "Schreibdiagnose / Coding Write – gesperrt",
        ],
        "message_de": "Keine vollständige Herstellerabdeckung behauptet.",
    }
