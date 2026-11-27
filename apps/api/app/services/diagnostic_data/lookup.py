"""DTC/PID-Lookup mit Herkunft; unbekannte DTCs → „unbekannt“."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.diagnostic_data import DataLicenseSource, DiagDtcDefinition, DiagPidDefinition
from app.schemas.diagnostic_data import DtcLookupOut, PidDefinitionOut, ProvenanceOut


def provenance_for_source(source: DataLicenseSource) -> ProvenanceOut:
    return ProvenanceOut(
        source_key=source.key,
        source_name=source.name,
        license_name=source.license_name,
        commercial_use=source.commercial_use,
        attribution=source.attribution,
        checked_at=source.checked_at,
        redistributable=source.redistributable,
        url=source.url,
        version=source.version,
    )


def lookup_dtc(db: Session, code: str) -> DtcLookupOut:
    normalized = code.strip().upper().replace(" ", "")
    # Bevorzuge bekannte Beschreibungstexte (z. B. nach Phase-07-Update) vor „unknown“-Baseline
    rows = db.scalars(
        select(DiagDtcDefinition).where(DiagDtcDefinition.code == normalized)
    ).all()
    row = None
    if rows:
        known = [
            r
            for r in rows
            if r.description_status == "known" and (r.description_de or "").strip()
        ]
        if known:
            # generic vor oem
            known.sort(key=lambda r: 0 if r.data_scope == "generic" else 1)
            row = known[0]
        else:
            rows_sorted = sorted(rows, key=lambda r: 0 if r.data_scope == "generic" else 1)
            row = rows_sorted[0]
    if row is None:
        return DtcLookupOut(
            code=normalized,
            known=False,
            description_de="unbekannt",
            description_status="unknown",
            data_scope=None,
            provenance=None,
            message_de="Kein Eintrag in der Diagnosedatenbank. Code wird als unbekannt angezeigt.",
        )

    source = db.get(DataLicenseSource, row.source_id)
    desc_status = row.description_status  # type: ignore[assignment]
    if desc_status != "known" or not row.description_de:
        return DtcLookupOut(
            code=row.code,
            known=True,
            description_de="unbekannt",
            description_status="unknown" if desc_status == "unknown" else desc_status,  # type: ignore[arg-type]
            data_scope=row.data_scope,
            provenance=provenance_for_source(source) if source else None,
            message_de="DTC-Code bekannt, Beschreibung fehlt oder ist zurückgehalten – Anzeige: unbekannt.",
        )

    return DtcLookupOut(
        code=row.code,
        known=True,
        description_de=row.description_de,
        description_status="known",
        data_scope=row.data_scope,
        provenance=provenance_for_source(source) if source else None,
        message_de="DTC-Eintrag mit dokumentierter Herkunft.",
    )


def list_pids(db: Session) -> list[PidDefinitionOut]:
    rows = db.scalars(select(DiagPidDefinition).order_by(DiagPidDefinition.pid_hex)).all()
    out: list[PidDefinitionOut] = []
    for row in rows:
        source = db.get(DataLicenseSource, row.source_id)
        if source is None:
            continue
        out.append(
            PidDefinitionOut(
                id=row.id,
                pid_hex=row.pid_hex,
                name=row.name,
                description_de=row.description_de,
                unit=row.unit,
                bytes_needed=row.bytes_needed,
                conversion_formula=row.conversion_formula,
                data_scope=row.data_scope,
                kind=row.kind,
                provenance=provenance_for_source(source),
            )
        )
    return out
