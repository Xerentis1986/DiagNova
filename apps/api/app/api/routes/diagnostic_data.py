"""Phase 06 – Diagnosedatenbank, Lookup, Import/Quarantäne/Rollback."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import User
from app.models.diagnostic_data import (
    DataLicenseSource,
    DiagDatasetVersion,
    DiagEcuDefinition,
    DiagManufacturer,
    ImportBatch,
)
from app.schemas.diagnostic_data import (
    DataSourceOut,
    DatasetVersionOut,
    DtcLookupOut,
    EcuDefinitionOut,
    ImportBatchOut,
    ImportPreviewOut,
    ManufacturerOut,
    PidDefinitionOut,
)
from app.services.audit import write_audit
from app.services.diagnostic_data import (
    apply_import_batch,
    lookup_dtc,
    preview_csv_import,
    preview_json_import,
    reject_odx_import,
    rollback_import_batch,
)
from app.services.diagnostic_data.import_pipeline import get_batch
from app.services.diagnostic_data.lookup import list_pids, provenance_for_source

router = APIRouter(prefix="/diagnostic-data", tags=["diagnostic-data"])
AdminOrTech = Annotated[User, Depends(require_roles("admin", "technician"))]


def _src_out(s: DataLicenseSource) -> DataSourceOut:
    return DataSourceOut(
        key=s.key,
        name=s.name,
        url=s.url,
        version=s.version,
        license_name=s.license_name,
        commercial_use=s.commercial_use,
        attribution=s.attribution,
        scope=s.scope,
        notes_de=s.notes_de,
        checked_at=s.checked_at,
        redistributable=s.redistributable,
    )


@router.get("/sources", response_model=list[DataSourceOut])
def list_sources(_user: CurrentUser, db: DbSession) -> list[DataSourceOut]:
    rows = db.scalars(select(DataLicenseSource).order_by(DataLicenseSource.key)).all()
    return [_src_out(s) for s in rows]


@router.get("/versions", response_model=list[DatasetVersionOut])
def list_versions(_user: CurrentUser, db: DbSession) -> list[DatasetVersionOut]:
    rows = db.scalars(select(DiagDatasetVersion).order_by(DiagDatasetVersion.created_at.desc())).all()
    return [
        DatasetVersionOut(
            id=r.id,
            version_label=r.version_label,
            status=r.status,
            notes_de=r.notes_de,
            created_at=r.created_at,
            published_at=r.published_at,
        )
        for r in rows
    ]


@router.get("/manufacturers", response_model=list[ManufacturerOut])
def list_manufacturers(_user: CurrentUser, db: DbSession) -> list[ManufacturerOut]:
    rows = db.scalars(select(DiagManufacturer).order_by(DiagManufacturer.slug)).all()
    out: list[ManufacturerOut] = []
    for r in rows:
        src = db.get(DataLicenseSource, r.source_id)
        if src is None:
            continue
        out.append(
            ManufacturerOut(
                id=r.id,
                slug=r.slug,
                name=r.name,
                data_scope=r.data_scope,
                provenance=provenance_for_source(src),
            )
        )
    return out


@router.get("/ecus", response_model=list[EcuDefinitionOut])
def list_ecus(_user: CurrentUser, db: DbSession) -> list[EcuDefinitionOut]:
    rows = db.scalars(select(DiagEcuDefinition).order_by(DiagEcuDefinition.code)).all()
    out: list[EcuDefinitionOut] = []
    for r in rows:
        src = db.get(DataLicenseSource, r.source_id)
        if src is None:
            continue
        out.append(
            EcuDefinitionOut(
                id=r.id,
                code=r.code,
                name_de=r.name_de,
                category=r.category,
                protocol_id=r.protocol_id,
                request_address=r.request_address,
                response_address=r.response_address,
                software_variant=r.software_variant,
                data_scope=r.data_scope,
                verified=r.verified,
                provenance=provenance_for_source(src),
            )
        )
    return out


@router.get("/pids", response_model=list[PidDefinitionOut])
def get_pids(_user: CurrentUser, db: DbSession) -> list[PidDefinitionOut]:
    return list_pids(db)


@router.get("/dtcs/{code}", response_model=DtcLookupOut)
def get_dtc(code: str, _user: CurrentUser, db: DbSession) -> DtcLookupOut:
    return lookup_dtc(db, code)


@router.post("/import/preview", response_model=ImportPreviewOut)
def import_preview_json(
    payload: dict[str, Any],
    user: AdminOrTech,
    db: DbSession,
) -> ImportPreviewOut:
    """JSON-Vorschau: Schema/Quarantäne/Konflikte – kein Commit der Nutzdaten."""
    result = preview_json_import(db, payload, user_id=user.id, filename=None)
    write_audit(
        db,
        user_id=user.id,
        action="diagnostic_data.import.preview",
        resource=f"batch:{result.batch_id}",
        detail=result.status,
    )
    return result


@router.post("/import/preview-file", response_model=ImportPreviewOut)
async def import_preview_file(
    user: AdminOrTech,
    db: DbSession,
    file: UploadFile = File(...),
) -> ImportPreviewOut:
    """JSON-Datei-Upload zur Vorschau. ODX/PDX → 403."""
    filename = file.filename or "upload.json"
    name = filename.lower()
    if name.endswith(".odx") or name.endswith(".pdx"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reject_odx_import())
    if name.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV bitte über /import/preview-csv senden.",
        )
    raw = (await file.read()).decode("utf-8")
    result = preview_json_import(db, raw, user_id=user.id, filename=filename)
    write_audit(
        db,
        user_id=user.id,
        action="diagnostic_data.import.preview_file",
        resource=f"batch:{result.batch_id}",
        detail=result.status,
    )
    return result


@router.post("/import/preview-csv", response_model=ImportPreviewOut)
async def import_preview_csv(
    user: AdminOrTech,
    db: DbSession,
    source_key: Annotated[str, Form()],
    dataset_version_label: Annotated[str, Form()],
    entity_type: Annotated[str, Form()] = "dtc",
    file: UploadFile = File(...),
) -> ImportPreviewOut:
    if entity_type not in ("dtc", "pid"):
        raise HTTPException(status_code=400, detail="entity_type muss dtc oder pid sein")
    content = (await file.read()).decode("utf-8")
    result = preview_csv_import(
        db,
        content,
        entity_type=entity_type,  # type: ignore[arg-type]
        source_key=source_key,
        dataset_version_label=dataset_version_label,
        user_id=user.id,
        filename=file.filename,
    )
    write_audit(
        db,
        user_id=user.id,
        action="diagnostic_data.import.preview_csv",
        resource=f"batch:{result.batch_id}",
        detail=result.status,
    )
    return result


@router.post("/import/odx")
def import_odx(_user: AdminOrTech) -> dict:
    """Bewusst abgelehnt bis Lizenz/Spezifikation."""
    body = reject_odx_import()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=body)


@router.post("/import/{batch_id}/apply", response_model=ImportBatchOut)
def import_apply(batch_id: str, user: AdminOrTech, db: DbSession) -> ImportBatchOut:
    try:
        out = apply_import_batch(db, batch_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=user.id,
        action="diagnostic_data.import.apply",
        resource=f"batch:{batch_id}",
        detail=out.status,
    )
    return out


@router.post("/import/{batch_id}/rollback", response_model=ImportBatchOut)
def import_rollback(batch_id: str, user: AdminOrTech, db: DbSession) -> ImportBatchOut:
    try:
        out = rollback_import_batch(db, batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=user.id,
        action="diagnostic_data.import.rollback",
        resource=f"batch:{batch_id}",
        detail=out.status,
    )
    return out


@router.get("/import/{batch_id}", response_model=ImportBatchOut)
def import_status(batch_id: str, _user: CurrentUser, db: DbSession) -> ImportBatchOut:
    out = get_batch(db, batch_id)
    if out is None:
        raise HTTPException(status_code=404, detail="Batch nicht gefunden")
    return out


@router.get("/import", response_model=list[ImportBatchOut])
def list_imports(_user: CurrentUser, db: DbSession) -> list[ImportBatchOut]:
    rows = db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(50)).all()
    return [get_batch(db, r.id) for r in rows if get_batch(db, r.id) is not None]  # type: ignore[misc]


@router.get("/coverage")
def coverage_summary(_user: CurrentUser, db: DbSession) -> dict:
    """Keine Vollständigkeit vortäuschen – explizite Lücken."""
    return {
        "disclaimer_de": (
            "Diagnosedatenbank ist unvollständig. Generische OBD-PIDs und ISO-15765-4-Adressen "
            "vorhanden. OEM-ECU/DTC-Texte und ODX fehlen (BLK-OEM). Unbekannte DTCs → „unbekannt“."
        ),
        "generic_pids": len(list_pids(db)),
        "ecu_count": int(db.scalar(select(func.count()).select_from(DiagEcuDefinition)) or 0),
        "manufacturer_count": int(db.scalar(select(func.count()).select_from(DiagManufacturer)) or 0),
        "sources": [_src_out(s) for s in db.scalars(select(DataLicenseSource)).all()],
        "odx_import": "disabled",
        "blocked_vendors": ["Bosch", "Gutmann", "Delphi"],
        "phase_07": "implemented_simulated",
        "data_updates": "/api/data-updates/dashboard",
    }
