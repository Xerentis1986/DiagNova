"""JSON/CSV-Import: Schema-Prüfung, Quarantäne, Konflikte, Apply, Rollback. ODX gesperrt."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.diagnostic_data import (
    DataLicenseSource,
    DiagDatasetVersion,
    DiagDtcDefinition,
    DiagEcuDefinition,
    DiagManufacturer,
    DiagModel,
    DiagPidDefinition,
    DiagServiceProcedure,
    DiagUnitDefinition,
    DiagVariant,
    ImportAppliedRecord,
    ImportBatch,
    ImportQuarantineItem,
)
from app.schemas.diagnostic_data import (
    ConflictItemOut,
    DiagnosticImportPackage,
    ImportBatchOut,
    ImportDtcIn,
    ImportPidIn,
    ImportPreviewOut,
    QuarantineItemOut,
)

# Quellen, die wir bewusst ablehnen (keine Kopien)
BLOCKED_SOURCE_KEYWORDS = (
    "bosch",
    "gutmann",
    "delphi",
    "autocom",
    "esi[tronic]",
    "esi-tronic",
)


def reject_odx_import() -> dict[str, Any]:
    return {
        "accepted": False,
        "status": "rejected",
        "format": "odx",
        "message_de": (
            "ODX/PDX-Import ist deaktiviert, bis Spezifikation und Nutzungsrechte "
            "vorliegen (REQ-06-ODX). Keine stillen Importe."
        ),
        "blocker": "BLK-OEM",
    }


def _is_blocked_source(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in BLOCKED_SOURCE_KEYWORDS)


def _batch_out(db: Session, batch: ImportBatch) -> ImportBatchOut:
    return ImportBatchOut(
        id=batch.id,
        format=batch.format,
        status=batch.status,
        filename=batch.filename,
        source_key=batch.source_key,
        summary=json.loads(batch.summary_json or "{}"),
        conflicts=json.loads(batch.conflict_report_json or "[]"),
        quarantine_count=len(batch.quarantine_items),
        applied_count=len(batch.applied_records),
        created_at=batch.created_at,
        applied_at=batch.applied_at,
        rolled_back_at=batch.rolled_back_at,
    )


def _quarantine(
    db: Session,
    batch: ImportBatch,
    *,
    entity_type: str,
    row_index: int,
    reason_de: str,
    payload: dict[str, Any],
) -> QuarantineItemOut:
    item = ImportQuarantineItem(
        batch_id=batch.id,
        entity_type=entity_type,
        row_index=row_index,
        reason_de=reason_de,
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    db.add(item)
    return QuarantineItemOut(
        entity_type=entity_type,
        row_index=row_index,
        reason_de=reason_de,
        payload=payload,
    )


def preview_json_import(
    db: Session,
    payload: dict[str, Any] | str,
    *,
    user_id: str | None = None,
    filename: str | None = None,
) -> ImportPreviewOut:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            batch = ImportBatch(
                format="json",
                status="rejected",
                filename=filename,
                created_by=user_id,
                summary_json=json.dumps({"error": "invalid_json"}),
                conflict_report_json="[]",
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)
            return ImportPreviewOut(
                batch_id=batch.id,
                status="rejected",
                format="json",
                summary={"error": "invalid_json", "detail": str(exc)},
                conflicts=[],
                quarantine=[],
                can_apply=False,
                message_de="JSON ungültig – Import abgewiesen.",
            )

    assert isinstance(payload, dict)

    if _is_blocked_source(json.dumps(payload).lower()) or _is_blocked_source(
        str(payload.get("source_key", ""))
    ):
        batch = ImportBatch(
            format="json",
            status="rejected",
            filename=filename,
            created_by=user_id,
            source_key=str(payload.get("source_key", "")),
            summary_json=json.dumps({"error": "blocked_source"}),
            conflict_report_json="[]",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return ImportPreviewOut(
            batch_id=batch.id,
            status="rejected",
            format="json",
            summary={"error": "blocked_source"},
            conflicts=[],
            quarantine=[],
            can_apply=False,
            message_de=(
                "Quelle abgelehnt: keine Daten aus Bosch/Gutmann/Delphi oder vergleichbaren "
                "kommerziellen Katalogen."
            ),
        )

    batch = ImportBatch(
        format="json",
        status="preview",
        filename=filename,
        created_by=user_id,
        source_key=str(payload.get("source_key", "")) or None,
        summary_json="{}",
        conflict_report_json="[]",
    )
    db.add(batch)
    db.flush()

    quarantine: list[QuarantineItemOut] = []
    conflicts: list[ConflictItemOut] = []
    valid_counts: dict[str, int] = {
        "manufacturers": 0,
        "models": 0,
        "variants": 0,
        "ecus": 0,
        "dtcs": 0,
        "pids": 0,
        "units": 0,
        "service_procedures": 0,
    }

    try:
        package = DiagnosticImportPackage.model_validate(payload)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()))
            quarantine.append(
                _quarantine(
                    db,
                    batch,
                    entity_type="package",
                    row_index=0,
                    reason_de=f"Schema-Fehler bei {loc}: {err.get('msg')}",
                    payload={"error": err},
                )
            )
        batch.status = "quarantine"
        batch.summary_json = json.dumps({"schema_valid": False, "valid_counts": valid_counts})
        batch.conflict_report_json = json.dumps([])
        db.commit()
        db.refresh(batch)
        return ImportPreviewOut(
            batch_id=batch.id,
            status=batch.status,
            format="json",
            summary=json.loads(batch.summary_json),
            conflicts=[],
            quarantine=quarantine,
            can_apply=False,
            message_de="Schema-Prüfung fehlgeschlagen – Datensatz in Quarantäne.",
        )

    source = db.scalar(select(DataLicenseSource).where(DataLicenseSource.key == package.source_key))
    if source is None:
        quarantine.append(
            _quarantine(
                db,
                batch,
                entity_type="source",
                row_index=0,
                reason_de=f"Unbekannte source_key „{package.source_key}“ – erst registrieren.",
                payload={"source_key": package.source_key},
            )
        )
    elif not source.redistributable and source.scope != "structural":
        quarantine.append(
            _quarantine(
                db,
                batch,
                entity_type="source",
                row_index=0,
                reason_de=(
                    f"Quelle „{source.key}“ ist nicht als redistributable markiert "
                    f"(commercial_use={source.commercial_use})."
                ),
                payload={"source_key": source.key},
            )
        )

    # Row-level validation for nested lists already done by pydantic;
    # additional business rules + conflicts
    existing_version = db.scalar(
        select(DiagDatasetVersion).where(DiagDatasetVersion.version_label == package.dataset_version_label)
    )
    if existing_version and existing_version.status == "published":
        conflicts.append(
            ConflictItemOut(
                entity_type="dataset_version",
                key=package.dataset_version_label,
                reason_de="Version bereits veröffentlicht – Import würde Dublette erzeugen.",
            )
        )

    for i, dtc in enumerate(package.dtcs):
        # description_status=known ohne Text → Quarantäne
        if dtc.description_status == "known" and not (dtc.description_de or "").strip():
            quarantine.append(
                _quarantine(
                    db,
                    batch,
                    entity_type="dtc",
                    row_index=i,
                    reason_de="description_status=known ohne description_de.",
                    payload=dtc.model_dump(),
                )
            )
            continue
        # OEM-Texte ohne explizite Quelle ablehnen (source muss redistributable sein – oben)
        if dtc.data_scope == "oem" and (source is None or not source.redistributable):
            quarantine.append(
                _quarantine(
                    db,
                    batch,
                    entity_type="dtc",
                    row_index=i,
                    reason_de="OEM-DTC ohne redistributable Lizenzquelle.",
                    payload=dtc.model_dump(),
                )
            )
            continue
        # Dublette innerhalb des Pakets
        if any(x.code == dtc.code and x.data_scope == dtc.data_scope for x in package.dtcs[:i]):
            conflicts.append(
                ConflictItemOut(
                    entity_type="dtc",
                    key=f"{dtc.code}:{dtc.data_scope}",
                    reason_de="Dublette im Importpaket.",
                )
            )
            continue
        valid_counts["dtcs"] += 1

    for i, mfr in enumerate(package.manufacturers):
        if any(x.slug == mfr.slug for x in package.manufacturers[:i]):
            conflicts.append(
                ConflictItemOut(entity_type="manufacturer", key=mfr.slug, reason_de="Dublette im Paket.")
            )
            continue
        valid_counts["manufacturers"] += 1

    valid_counts["models"] = len(package.models)
    valid_counts["variants"] = len(package.variants)
    valid_counts["ecus"] = len(package.ecus)
    valid_counts["pids"] = len(package.pids)
    valid_counts["units"] = len(package.units)
    valid_counts["service_procedures"] = len(package.service_procedures)

    # Store validated package for apply
    summary = {
        "schema_valid": True,
        "dataset_version_label": package.dataset_version_label,
        "source_key": package.source_key,
        "valid_counts": valid_counts,
        "package": package.model_dump(),
    }

    has_blocking = bool(quarantine) or any(c.entity_type == "dataset_version" for c in conflicts)
    if has_blocking:
        batch.status = "quarantine"
        can_apply = False
        message = "Vorschau mit Quarantäne-/Konfliktfällen – Apply gesperrt."
    else:
        batch.status = "preview"
        can_apply = valid_counts["dtcs"] + valid_counts["manufacturers"] + valid_counts["pids"] + valid_counts[
            "ecus"
        ] + valid_counts["models"] + valid_counts["units"] + valid_counts["service_procedures"] + valid_counts[
            "variants"
        ] > 0
        message = "Vorschau OK – Apply möglich." if can_apply else "Leeres Paket – nichts anzuwenden."

    batch.summary_json = json.dumps(summary, ensure_ascii=False)
    batch.conflict_report_json = json.dumps([c.model_dump() for c in conflicts], ensure_ascii=False)
    db.commit()
    db.refresh(batch)

    return ImportPreviewOut(
        batch_id=batch.id,
        status=batch.status,
        format="json",
        summary={k: v for k, v in summary.items() if k != "package"},
        conflicts=conflicts,
        quarantine=quarantine,
        can_apply=can_apply and not has_blocking,
        message_de=message,
    )


def preview_csv_import(
    db: Session,
    content: str,
    *,
    entity_type: Literal["dtc", "pid"] = "dtc",
    source_key: str,
    dataset_version_label: str,
    user_id: str | None = None,
    filename: str | None = None,
) -> ImportPreviewOut:
    """CSV-Import für dtcs oder pids (Spalten je Typ)."""
    entity = entity_type
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        batch = ImportBatch(
            format="csv",
            status="rejected",
            filename=filename,
            created_by=user_id,
            source_key=source_key,
            summary_json=json.dumps({"error": "empty_csv"}),
            conflict_report_json="[]",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return ImportPreviewOut(
            batch_id=batch.id,
            status="rejected",
            format="csv",
            summary={"error": "empty_csv"},
            conflicts=[],
            quarantine=[],
            can_apply=False,
            message_de="CSV leer oder ohne Kopfzeile.",
        )

    rows: list[dict[str, Any]] = []
    quarantine_payloads: list[tuple[int, str, dict]] = []

    for idx, raw in enumerate(reader, start=1):
        cleaned = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items() if k}
        try:
            if entity == "dtc":
                item = ImportDtcIn(
                    code=cleaned.get("code", ""),
                    description_de=cleaned.get("description_de") or None,
                    description_status=cleaned.get("description_status") or "unknown",  # type: ignore[arg-type]
                    data_scope=cleaned.get("data_scope") or "generic",  # type: ignore[arg-type]
                )
                rows.append(item.model_dump())
            elif entity == "pid":
                item = ImportPidIn(
                    pid_hex=cleaned.get("pid_hex", ""),
                    name=cleaned.get("name", ""),
                    description_de=cleaned.get("description_de", ""),
                    unit=cleaned.get("unit", ""),
                    bytes_needed=int(cleaned.get("bytes_needed") or 1),
                    conversion_formula=cleaned.get("conversion_formula") or None,
                    data_scope=cleaned.get("data_scope") or "generic",  # type: ignore[arg-type]
                    kind=cleaned.get("kind") or "pid",  # type: ignore[arg-type]
                )
                rows.append(item.model_dump())
            else:
                quarantine_payloads.append((idx, f"Unbekannter entity_type {entity}", cleaned))
        except (ValidationError, ValueError, TypeError) as exc:
            quarantine_payloads.append((idx, str(exc), cleaned))

    package: dict[str, Any] = {
        "schema_version": "diagnova.diagnostic-import.v1",
        "dataset_version_label": dataset_version_label,
        "source_key": source_key,
        "manufacturers": [],
        "models": [],
        "variants": [],
        "ecus": [],
        "dtcs": rows if entity == "dtc" else [],
        "pids": rows if entity == "pid" else [],
        "units": [],
        "service_procedures": [],
    }
    preview = preview_json_import(db, package, user_id=user_id, filename=filename)
    # Attach CSV-specific quarantine rows to the same batch
    batch = db.get(ImportBatch, preview.batch_id)
    assert batch is not None
    batch.format = "csv"
    extra_q: list[QuarantineItemOut] = list(preview.quarantine)
    for row_index, reason, payload in quarantine_payloads:
        extra_q.append(
            _quarantine(
                db,
                batch,
                entity_type=entity,
                row_index=row_index,
                reason_de=reason,
                payload=payload,
            )
        )
    if quarantine_payloads:
        batch.status = "quarantine"
    db.commit()
    db.refresh(batch)
    summary = json.loads(batch.summary_json)
    summary.pop("package", None)
    return ImportPreviewOut(
        batch_id=batch.id,
        status=batch.status,
        format="csv",
        summary=summary,
        conflicts=preview.conflicts,
        quarantine=extra_q,
        can_apply=batch.status == "preview" and preview.can_apply and not quarantine_payloads,
        message_de=preview.message_de if not quarantine_payloads else "CSV-Zeilen in Quarantäne.",
    )


def apply_import_batch(db: Session, batch_id: str, *, user_id: str | None = None) -> ImportBatchOut:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise ValueError("Import-Batch nicht gefunden")
    if batch.status not in ("preview",):
        raise ValueError(f"Batch-Status „{batch.status}“ erlaubt kein Apply")

    summary = json.loads(batch.summary_json or "{}")
    package_data = summary.get("package")
    if not package_data:
        raise ValueError("Kein validiertes Paket in der Vorschau")

    package = DiagnosticImportPackage.model_validate(package_data)
    source = db.scalar(select(DataLicenseSource).where(DataLicenseSource.key == package.source_key))
    if source is None:
        raise ValueError("Quelle fehlt")

    # Transaktion: Dataset-Version + Entities
    version = DiagDatasetVersion(
        version_label=package.dataset_version_label,
        status="published",
        source_id=source.id,
        notes_de=f"Import-Batch {batch.id}",
        published_at=datetime.now(timezone.utc),
    )
    db.add(version)
    db.flush()

    mfr_by_slug: dict[str, DiagManufacturer] = {}
    model_by_key: dict[str, DiagModel] = {}

    def _track(entity_type: str, entity_id: str) -> None:
        db.add(ImportAppliedRecord(batch_id=batch.id, entity_type=entity_type, entity_id=entity_id))

    _track("dataset_version", version.id)

    for m in package.manufacturers:
        row = DiagManufacturer(
            dataset_version_id=version.id,
            source_id=source.id,
            slug=m.slug,
            name=m.name,
            data_scope=m.data_scope,
            notes_de=m.notes_de,
        )
        db.add(row)
        db.flush()
        mfr_by_slug[m.slug] = row
        _track("manufacturer", row.id)

    for m in package.models:
        mfr = mfr_by_slug.get(m.manufacturer_slug)
        if mfr is None:
            mfr = db.scalar(
                select(DiagManufacturer).where(
                    DiagManufacturer.slug == m.manufacturer_slug,
                    DiagManufacturer.dataset_version_id == version.id,
                )
            )
        if mfr is None:
            continue
        row = DiagModel(
            manufacturer_id=mfr.id,
            source_id=source.id,
            code=m.code,
            name=m.name,
            year_from=m.year_from,
            year_to=m.year_to,
            data_scope=m.data_scope,
        )
        db.add(row)
        db.flush()
        model_by_key[f"{m.manufacturer_slug}:{m.code}"] = row
        _track("model", row.id)

    for v in package.variants:
        model = model_by_key.get(f"{v.manufacturer_slug}:{v.model_code}")
        if model is None:
            continue
        row = DiagVariant(
            model_id=model.id,
            source_id=source.id,
            code=v.code,
            name=v.name,
            year_from=v.year_from,
            year_to=v.year_to,
            engine=v.engine,
            data_scope=v.data_scope,
        )
        db.add(row)
        db.flush()
        _track("variant", row.id)

    for e in package.ecus:
        row = DiagEcuDefinition(
            dataset_version_id=version.id,
            source_id=source.id,
            code=e.code,
            name_de=e.name_de,
            category=e.category,
            protocol_id=e.protocol_id,
            request_address=e.request_address,
            response_address=e.response_address,
            software_variant=e.software_variant,
            data_scope=e.data_scope,
            verified=e.verified,
            notes_de=e.notes_de,
        )
        db.add(row)
        db.flush()
        _track("ecu", row.id)

    for d in package.dtcs:
        system = d.code[0] if d.code else None
        desc_status = d.description_status
        desc = d.description_de
        if desc_status != "known" or not desc:
            desc_status = "unknown"
            desc = None
        row = DiagDtcDefinition(
            dataset_version_id=version.id,
            source_id=source.id,
            code=d.code,
            description_de=desc,
            description_status=desc_status,
            data_scope=d.data_scope,
            system=system,
            notes_de=d.notes_de,
        )
        db.add(row)
        db.flush()
        _track("dtc", row.id)

    for p in package.pids:
        row = DiagPidDefinition(
            dataset_version_id=version.id,
            source_id=source.id,
            pid_hex=p.pid_hex,
            name=p.name,
            description_de=p.description_de,
            unit=p.unit,
            bytes_needed=p.bytes_needed,
            conversion_formula=p.conversion_formula,
            data_scope=p.data_scope,
            kind=p.kind,
        )
        db.add(row)
        db.flush()
        _track("pid", row.id)

    for u in package.units:
        row = DiagUnitDefinition(
            dataset_version_id=version.id,
            source_id=source.id,
            code=u.code,
            label_de=u.label_de,
            symbol=u.symbol,
        )
        db.add(row)
        db.flush()
        _track("unit", row.id)

    for s in package.service_procedures:
        row = DiagServiceProcedure(
            dataset_version_id=version.id,
            source_id=source.id,
            code=s.code,
            name_de=s.name_de,
            prerequisites_json=json.dumps(s.prerequisites, ensure_ascii=False),
            data_scope=s.data_scope,
            enabled=False,  # nie still aktivieren ohne Review
            notes_de=s.notes_de,
        )
        db.add(row)
        db.flush()
        _track("service_procedure", row.id)

    batch.status = "applied"
    batch.dataset_version_id = version.id
    batch.applied_at = datetime.now(timezone.utc)
    if user_id:
        batch.created_by = batch.created_by or user_id
    db.commit()
    db.refresh(batch)
    return _batch_out(db, batch)


_ENTITY_DELETE_MAP = {
    "service_procedure": DiagServiceProcedure,
    "unit": DiagUnitDefinition,
    "pid": DiagPidDefinition,
    "dtc": DiagDtcDefinition,
    "ecu": DiagEcuDefinition,
    "variant": DiagVariant,
    "model": DiagModel,
    "manufacturer": DiagManufacturer,
    "dataset_version": DiagDatasetVersion,
}


def rollback_import_batch(db: Session, batch_id: str) -> ImportBatchOut:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise ValueError("Import-Batch nicht gefunden")
    if batch.status != "applied":
        raise ValueError(f"Rollback nur für applied (aktuell: {batch.status})")

    # In Abhängigkeit umgekehrter Reihenfolge löschen
    order = [
        "service_procedure",
        "unit",
        "pid",
        "dtc",
        "ecu",
        "variant",
        "model",
        "manufacturer",
        "dataset_version",
    ]
    records = list(batch.applied_records)
    for entity_type in order:
        model_cls = _ENTITY_DELETE_MAP[entity_type]
        for rec in records:
            if rec.entity_type != entity_type:
                continue
            obj = db.get(model_cls, rec.entity_id)
            if obj is not None:
                db.delete(obj)

    # Applied-Records und Quarantäne behalten wir für Audit
    batch.status = "rolled_back"
    batch.rolled_back_at = datetime.now(timezone.utc)
    if batch.dataset_version_id:
        # version already deleted via records
        batch.dataset_version_id = None
    db.commit()
    db.refresh(batch)
    return _batch_out(db, batch)


def get_batch(db: Session, batch_id: str) -> ImportBatchOut | None:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        return None
    return _batch_out(db, batch)
