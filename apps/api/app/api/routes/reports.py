"""Phase 10 – Berichtsliste, Archiv, Löschung, Mandantenschutz."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import DiagnosticReport, DiagnosticSession, User, Vehicle, Workshop
from app.schemas.api import ReportCreate, ReportOut, ReportPurgeOut, ReportSummaryOut
from app.services.audit import write_audit
from app.services.reports import (
    archive_report,
    create_report,
    list_reports,
    purge_expired_reports,
    report_summary,
    report_to_csv,
    report_to_pdf,
    soft_delete_report,
)
from app.services.tenant import require_workshop_id

router = APIRouter(tags=["reports"])

Technician = Annotated[User, Depends(require_roles("admin", "technician"))]
Admin = Annotated[User, Depends(require_roles("admin"))]


def _tenant_report(db: DbSession, user: User, report_id: str) -> DiagnosticReport:
    wid = require_workshop_id(user)
    report = db.get(DiagnosticReport, report_id)
    if report is None or report.workshop_id != wid:
        # Fremde Mandanten und Unbekannt → 404 (kein Leak)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bericht nicht gefunden")
    if report.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bericht nicht gefunden")
    return report


def _to_out(report: DiagnosticReport) -> ReportOut:
    return ReportOut(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        created_at=report.created_at,
        content=json.loads(report.content_json),
        report_number=report.report_number,
        workshop_id=report.workshop_id,
        vehicle_id=report.vehicle_id,
        customer_id=report.customer_id,
        data_source=report.data_source,
        data_version=report.data_version,
        content_sha256=report.content_sha256,
        auto_generated=bool(report.auto_generated),
        frozen_at=report.frozen_at,
        archived_at=report.archived_at,
        deleted_at=report.deleted_at,
        notes=report.notes,
        recommendations=report.recommendations,
    )


@router.get("/reports", response_model=list[ReportSummaryOut])
def search_reports(
    user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None, max_length=128),
    vin: str | None = Query(default=None, max_length=17),
    include_archived: bool = False,
) -> list[ReportSummaryOut]:
    wid = require_workshop_id(user)
    rows = list_reports(
        db, wid, q=q, vin=vin, include_archived=include_archived, include_deleted=False
    )
    return [ReportSummaryOut(**report_summary(r)) for r in rows]


@router.post("/reports/purge-expired", response_model=ReportPurgeOut)
def purge_reports(user: Admin, db: DbSession) -> ReportPurgeOut:
    wid = require_workshop_id(user)
    workshop = db.get(Workshop, wid)
    if workshop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Werkstatt nicht gefunden")
    n = purge_expired_reports(db, workshop)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="report.purge_expired",
        resource=f"workshop:{wid}",
        detail=f"purged={n}",
    )
    return ReportPurgeOut(purged=n, retention_days=workshop.retention_days)


@router.post("/reports", response_model=ReportOut)
def create_diagnostic_report(body: ReportCreate, user: Technician, db: DbSession) -> ReportOut:
    wid = require_workshop_id(user)
    session = db.get(DiagnosticSession, body.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    vehicle = db.get(Vehicle, session.vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    # workshop_id an Sitzung nachziehen falls älterer MVP-Datensatz
    if session.workshop_id is None:
        session.workshop_id = wid
        db.commit()
        db.refresh(session)
    report = create_report(
        db,
        session,
        body.title,
        notes=body.notes,
        recommendations=body.recommendations,
        auto_generated=body.auto_generate,
    )
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="report.create",
        resource=f"report:{report.id}",
        detail=report.report_number,
    )
    return _to_out(report)


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, user: CurrentUser, db: DbSession) -> ReportOut:
    return _to_out(_tenant_report(db, user, report_id))


@router.get("/reports/{report_id}/export.csv")
def export_csv(report_id: str, user: CurrentUser, db: DbSession) -> Response:
    report = _tenant_report(db, user, report_id)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=report.workshop_id,
        action="report.download_csv",
        resource=f"report:{report.id}",
    )
    csv_text = report_to_csv(report)
    fname = report.report_number or report_id
    return Response(
        content=csv_text.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="diagnova-report-{fname}.csv"'},
    )


@router.get("/reports/{report_id}/export.pdf")
def export_pdf(report_id: str, user: CurrentUser, db: DbSession) -> Response:
    report = _tenant_report(db, user, report_id)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=report.workshop_id,
        action="report.download_pdf",
        resource=f"report:{report.id}",
    )
    pdf = report_to_pdf(report)
    fname = report.report_number or report_id
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="diagnova-report-{fname}.pdf"'},
    )


@router.post("/reports/{report_id}/archive", response_model=ReportOut)
def archive_diagnostic_report(report_id: str, user: Technician, db: DbSession) -> ReportOut:
    report = _tenant_report(db, user, report_id)
    archive_report(db, report)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=report.workshop_id,
        action="report.archive",
        resource=f"report:{report.id}",
    )
    return _to_out(report)


@router.delete("/reports/{report_id}", response_model=ReportOut)
def delete_diagnostic_report(report_id: str, user: Admin, db: DbSession) -> ReportOut:
    report = _tenant_report(db, user, report_id)
    soft_delete_report(db, report)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=report.workshop_id,
        action="report.delete",
        resource=f"report:{report.id}",
    )
    return _to_out(report)
