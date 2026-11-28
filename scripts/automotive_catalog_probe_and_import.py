#!/usr/bin/env python3
"""Probe Prioritätsquellen und baue OBDex-Importpaket (lokal .cache/, nicht Git).

  python scripts/automotive_catalog_probe_and_import.py
  python scripts/automotive_catalog_probe_and_import.py --full-obdex

Keine Secrets. Keine kostenpflichtigen Downloads.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

CACHE = ROOT / ".cache" / "automotive"


def main() -> int:
    from app.services import automotive_catalog as cat

    ap = argparse.ArgumentParser()
    ap.add_argument("--full-obdex", action="store_true", help="Volles OBDex JSON in .cache laden")
    ap.add_argument("--no-probe", action="store_true")
    args = ap.parse_args()

    summary = cat.catalog_summary()
    print("Katalog:", summary["source_count"], "Quellen,", summary["categories"], "Kategorien")

    if not args.no_probe:
        probe = cat.probe_priority(live=True)
        print(probe["message_de"])
        for r in probe["results"]:
            status = "OK" if r.get("ok") else "FAIL"
            print(f"  [{status}] {r.get('catalog_id')} {r.get('name')} → {r.get('http_status')}")

    CACHE.mkdir(parents=True, exist_ok=True)
    if args.full_obdex:
        import httpx

        url = "https://foerbsnavi.github.io/OBDex/generic.min.json"
        out = CACHE / "obdex_generic.min.json"
        print("Lade", url, "…")
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            out.write_bytes(resp.content)
        data = json.loads(out.read_text(encoding="utf-8"))
        print("OBDex Einträge:", len(data), "→", out)
        # Schreibe großes Importpaket lokal (nicht committen)
        dtcs = []
        for row in data:
            code = str(row.get("code", "")).upper()
            if len(code) != 5:
                continue
            title = row.get("title") or {}
            desc = row.get("description") or {}
            de = (title.get("de") or title.get("en") or desc.get("de") or desc.get("en") or "").strip()
            dtcs.append(
                {
                    "code": code,
                    "description_de": (de[:2000] if de else None),
                    "description_status": "known" if de else "unknown",
                    "data_scope": "generic",
                    "notes_de": "OBDex Vollimport CC0-1.0; nicht fahrzeugvalidiert; write_enabled=0",
                }
            )
        pkg = {
            "schema_version": "diagnova.diagnostic-import.v1",
            "dataset_version_label": "automotive-catalog-obdex-full-v1",
            "source_key": "obdex-cc0",
            "dtcs": dtcs,
            "pids": [],
        }
        pkg_path = CACHE / "import_obdex_full_v1.json"
        pkg_path.write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")
        print("Importpaket:", pkg_path, "DTCs", len(dtcs))

    print("Fixture-Sample:", cat.fixture_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
