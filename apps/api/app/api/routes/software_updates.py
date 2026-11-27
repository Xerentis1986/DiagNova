"""Phase 14 – Admin-API für Software-/Connector-Updates."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_roles
from app.core.config import get_settings
from app.data.software_versions import DB_MIGRATION_PLAN, DISCLAIMER_DE
from app.models import User
from app.models.software_updates import (
    SoftwareCompatibilityRule,
    SoftwareComponent,
    SoftwareUpdateChannel,
    SoftwareUpdateEvent,
    SoftwareUpdatePackage,
    SoftwareUpdateRun,
)
from app.schemas.software_updates import (
    AbortRunIn,
    ApproveInstallIn,
    BusyGateOut,
    CompatibilityCheckIn,
    CompatibilityCheckOut,
    CompatibilityRuleOut,
    IngestPackageIn,
    MigrationPlanOut,
    RejectPackageIn,
    SoftwareChannelOut,
    SoftwareComponentOut,
    SoftwareEventOut,
    SoftwarePackageOut,
    SoftwareRunOut,
    SoftwareUpdatesDashboardOut,
)
from app.services.software_updates.busy_gate import check_update_allowed
from app.services.software_updates.compatibility import check_compatibility
from app.services.software_updates.pipeline import (
    abort_run,
    approve_and_install,
    ingest_fixture_package,
    reject_package,
    rollback_component,
)

router = APIRouter(prefix="/software-updates", tags=["software-updates"])
AdminOnly = Annotated[User, Depends(require_roles("admin"))]


def _channel_out(c: SoftwareUpdateChannel) -> SoftwareChannelOut:
    return SoftwareChannelOut(
        id=c.id,
        key=c.key,
        name=c.name,
        channel_type=c.channel_type,
        fetch_mode=c.fetch_mode,
        enabled=c.enabled,
        auto_install_allowed=c.auto_install_allowed,
        require_signature=c.require_signature,
        require_signing_cert=c.require_signing_cert,
        notes_de=c.notes_de,
    )


def _component_out(c: SoftwareComponent) -> SoftwareComponentOut:
    return SoftwareComponentOut(
        key=c.key,
        label_de=c.label_de,
        current_version=c.current_version,
        previous_version=c.previous_version,
        channel_key=c.channel_key,
        health_status=c.health_status,
        last_healthcheck_at=c.last_healthcheck_at,
        last_error_de=c.last_error_de,
        updated_at=c.updated_at,
    )


def _package_out(db, p: SoftwareUpdatePackage) -> SoftwarePackageOut:
    ch = db.get(SoftwareUpdateChannel, p.channel_id)
    try:
        migration = json.loads(p.migration_plan_json or "[]")
    except json.JSONDecodeError:
        migration = []
    return SoftwarePackageOut(
        id=p.id,
        channel_id=p.channel_id,
        channel_key=ch.key if ch else None,
        component=p.component,
        version=p.version,
        package_filename=p.package_filename,
        content_sha256=p.content_sha256,
        signature_ok=p.signature_ok,
        release_notes_de=p.release_notes_de,
        migration_plan=migration if isinstance(migration, list) else [],
        status=p.status,
        error_de=p.error_de,
        created_at=p.created_at,
        approved_by=p.approved_by,
        approved_at=p.approved_at,
    )


def _run_out(r: SoftwareUpdateRun) -> SoftwareRunOut:
    try:
        summary = json.loads(r.summary_json or "{}")
    except json.JSONDecodeError:
        summary = {}
    return SoftwareRunOut(
        id=r.id,
        package_id=r.package_id,
        component=r.component,
        action=r.action,
        status=r.status,
        from_version=r.from_version,
        to_version=r.to_version,
        healthcheck_ok=r.healthcheck_ok,
        busy_reason_de=r.busy_reason_de,
        error_de=r.error_de,
        summary=summary if isinstance(summary, dict) else {},
        triggered_by=r.triggered_by,
        started_at=r.started_at,
        finished_at=r.finished_at,
    )


@router.get("/dashboard", response_model=SoftwareUpdatesDashboardOut)
def dashboard(user: AdminOnly, db: DbSession) -> SoftwareUpdatesDashboardOut:
    settings = get_settings()
    cert = settings.software_update_signing_cert_configured
    components = db.scalars(select(SoftwareComponent).order_by(SoftwareComponent.key)).all()
    channels = db.scalars(select(SoftwareUpdateChannel).order_by(SoftwareUpdateChannel.key)).all()
    pending = db.scalars(
        select(SoftwareUpdatePackage)
        .where(SoftwareUpdatePackage.status == "awaiting_approval")
        .order_by(SoftwareUpdatePackage.created_at.desc())
        .limit(50)
    ).all()
    recent_pkg = db.scalars(
        select(SoftwareUpdatePackage).order_by(SoftwareUpdatePackage.created_at.desc()).limit(30)
    ).all()
    runs = db.scalars(select(SoftwareUpdateRun).order_by(SoftwareUpdateRun.started_at.desc()).limit(30)).all()
    events = db.scalars(
        select(SoftwareUpdateEvent).order_by(SoftwareUpdateEvent.created_at.desc()).limit(40)
    ).all()
    rules = db.scalars(select(SoftwareCompatibilityRule)).all()
    busy = check_update_allowed(db, workshop_id=user.workshop_id)

    return SoftwareUpdatesDashboardOut(
        disclaimer_de=DISCLAIMER_DE,
        signing_cert_configured=cert,
        auto_install_enabled=settings.software_update_auto_install_enabled,
        productive_auto_updates_blocked=not cert,
        components=[_component_out(c) for c in components],
        channels=[_channel_out(c) for c in channels],
        pending_packages=[_package_out(db, p) for p in pending],
        recent_packages=[_package_out(db, p) for p in recent_pkg],
        recent_runs=[_run_out(r) for r in runs],
        recent_events=[
            SoftwareEventOut(
                id=e.id,
                package_id=e.package_id,
                run_id=e.run_id,
                component=e.component,
                event=e.event,
                detail_de=e.detail_de,
                created_at=e.created_at,
            )
            for e in events
        ],
        compatibility_rules=[
            CompatibilityRuleOut(
                id=r.id,
                component=r.component,
                version=r.version,
                requires=json.loads(r.requires_json or "{}"),
                notes_de=r.notes_de,
            )
            for r in rules
        ],
        migration_plan=[MigrationPlanOut(**m) for m in DB_MIGRATION_PLAN],
        busy=BusyGateOut(**busy),
    )


@router.get("/components", response_model=list[SoftwareComponentOut])
def list_components(user: AdminOnly, db: DbSession) -> list[SoftwareComponentOut]:
    _ = user
    rows = db.scalars(select(SoftwareComponent).order_by(SoftwareComponent.key)).all()
    return [_component_out(c) for c in rows]


@router.get("/busy", response_model=BusyGateOut)
def busy_status(user: AdminOnly, db: DbSession) -> BusyGateOut:
    return BusyGateOut(**check_update_allowed(db, workshop_id=user.workshop_id))


@router.post("/compatibility/check", response_model=CompatibilityCheckOut)
def compatibility_check(
    body: CompatibilityCheckIn, user: AdminOnly, db: DbSession
) -> CompatibilityCheckOut:
    _ = user
    result = check_compatibility(
        db,
        component=body.component,
        target_version=body.version,
        proposed_versions=body.proposed_versions,
    )
    return CompatibilityCheckOut(**result)


@router.post("/packages/ingest", response_model=SoftwarePackageOut)
def ingest_package(body: IngestPackageIn, user: AdminOnly, db: DbSession) -> SoftwarePackageOut:
    try:
        pkg = ingest_fixture_package(
            db,
            channel_key=body.channel_key,
            fixture_name=body.fixture_name,
            claimed_sha256=body.claimed_sha256,
            signature_hex=body.signature_hex,
            tamper=body.tamper,
            user_id=user.id,
            workshop_id=user.workshop_id,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _package_out(db, pkg)


@router.post("/packages/{package_id}/approve", response_model=SoftwareRunOut)
def approve_package(
    package_id: str,
    user: AdminOnly,
    db: DbSession,
    body: ApproveInstallIn | None = None,
) -> SoftwareRunOut:
    pkg = db.get(SoftwareUpdatePackage, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Paket nicht gefunden")
    body = body or ApproveInstallIn()
    try:
        run = approve_and_install(
            db,
            pkg,
            user_id=user.id,
            workshop_id=user.workshop_id,
            force_healthcheck_fail=body.force_healthcheck_fail,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_out(run)


@router.post("/packages/{package_id}/reject", response_model=SoftwarePackageOut)
def reject_pkg(
    package_id: str, body: RejectPackageIn, user: AdminOnly, db: DbSession
) -> SoftwarePackageOut:
    pkg = db.get(SoftwareUpdatePackage, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Paket nicht gefunden")
    try:
        pkg = reject_package(
            db,
            pkg,
            reason_de=body.reason_de,
            user_id=user.id,
            workshop_id=user.workshop_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _package_out(db, pkg)


@router.post("/components/{component}/rollback", response_model=SoftwareRunOut)
def rollback(component: str, user: AdminOnly, db: DbSession) -> SoftwareRunOut:
    try:
        run = rollback_component(
            db, component, user_id=user.id, workshop_id=user.workshop_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_out(run)


@router.post("/runs/{run_id}/abort", response_model=SoftwareRunOut)
def abort(run_id: str, body: AbortRunIn, user: AdminOnly, db: DbSession) -> SoftwareRunOut:
    run = db.get(SoftwareUpdateRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Lauf nicht gefunden")
    try:
        run = abort_run(
            db,
            run,
            reason_de=body.reason_de,
            user_id=user.id,
            workshop_id=user.workshop_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_out(run)


@router.get("/installer-docs")
def installer_docs(user: AdminOnly) -> dict[str, Any]:
    """Dokumentierte Installation/Deinstallation (kein echter Signatur-Installer ohne Zertifikat)."""
    _ = user
    settings = get_settings()
    return {
        "component": "connector",
        "platform": "Windows",
        "signing_cert_configured": settings.software_update_signing_cert_configured,
        "auto_update_blocked": not settings.software_update_signing_cert_configured,
        "install_steps_de": [
            "DiagNova.Connector-Release-ZIP aus vertrauenswürdigem Kanal laden.",
            "SHA-256 und Signatur gegen Admin-Anzeige prüfen.",
            "Installer/Portable entpacken; keine Diagnose/Service/Flash während Update.",
            "Als Benutzer mit lokalen Rechten installieren; Dienst/Prozess neu starten.",
            "GET http://127.0.0.1:8765/version und /health prüfen.",
        ],
        "uninstall_steps_de": [
            "Connector-Prozess beenden (kein offenes Fahrzeug).",
            "Programm deinstallieren bzw. Ordner entfernen.",
            "Pairing-Token und lokale Logs optional löschen.",
            "Gerätebindung in der Web-Admin-UI widerrufen falls nötig.",
        ],
        "note_de": (
            "Ohne konfiguriertes Code-Signing-Zertifikat sind produktive Auto-Updates gesperrt. "
            "Demo nutzt nur HMAC-Simulation."
        ),
        "docs_path": "docs/connector-installer.md",
    }
