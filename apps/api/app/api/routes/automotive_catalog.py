"""API: Automotive-Quellenkatalog + Prioritätsprobe + Fixture-Import."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import User
from app.models.diagnostic_data import DataLicenseSource
from app.services import automotive_catalog as svc
from app.services.admin_platform import require_platform_admin
from app.services.audit import write_audit
from app.services.diagnostic_data import apply_import_batch, preview_json_import
from sqlalchemy import select

router = APIRouter(prefix="/automotive-catalog", tags=["automotive-catalog"])
AdminOrTech = Annotated[User, Depends(require_roles("admin", "technician"))]


@router.get("/summary")
def summary(_user: CurrentUser) -> dict[str, Any]:
    return {
        **svc.catalog_summary(),
        **svc.fixture_status(),
        "coverage": svc.coverage_matrix_stub(),
        "ui_path": "/automotive-catalog",
        "go_note_de": "Pilot-Datenpfade; kommerzielles Voll-GO unverändert NO-GO.",
    }


@router.get("/sources")
def sources(
    _user: CurrentUser,
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return svc.list_sources(category=category, q=q, limit=limit, offset=offset)


@router.post("/probe")
def probe(
    user: CurrentUser,
    live: bool = Query(default=True),
) -> dict[str, Any]:
    """Erreichbarkeit Prioritätsquellen – keine Secrets, keine Downloads in die Antwort."""
    require_platform_admin(user)
    return svc.probe_priority(live=live)


@router.get("/fixtures/import-package")
def get_fixture_package(_user: AdminOrTech) -> dict[str, Any]:
    return svc.fixture_import_package()


@router.post("/fixtures/import-preview")
def preview_fixture_import(user: AdminOrTech, db: DbSession) -> dict[str, Any]:
    """Quarantäne/Preview des OBDex-Sample-Pakets (CC0)."""
    _ensure_obdex_source(db)
    pkg = svc.fixture_import_package()
    preview = preview_json_import(db, pkg, user_id=user.id)
    return preview.model_dump()


@router.post("/fixtures/import-apply")
def apply_fixture_import(user: CurrentUser, db: DbSession, batch_id: str = Query(...)) -> dict[str, Any]:
    require_platform_admin(user)
    try:
        out = apply_import_batch(db, batch_id, user_id=user.id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)[:400]) from exc
    write_audit(
        db,
        user_id=user.id,
        action="automotive_catalog_import_apply",
        resource=batch_id,
        detail="obdex_sample_v1",
        workshop_id=user.workshop_id,
    )
    return out


def _ensure_obdex_source(db: DbSession) -> DataLicenseSource:
    row = db.scalar(select(DataLicenseSource).where(DataLicenseSource.key == "obdex-cc0"))
    if row:
        return row
    row = DataLicenseSource(
        key="obdex-cc0",
        name="OBDex (CC0-1.0 Sample)",
        url="https://foerbsnavi.github.io/OBDex/generic.min.json",
        version="generic.min sample-200",
        license_name="CC0-1.0",
        commercial_use="allowed",
        attribution="OBDex / foerbsnavi – CC0",
        scope="generic_dtc",
        notes_de="200er Sample aus Gesamtkatalog-Import; Vollbestand via Skript .cache/",
        checked_at="2026-11-28",
        redistributable=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
