"""Software-Update-Pipeline: Ingest → Integrität → Kompatibilität → Staging → Freigabe → Install/Rollback."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.data.software_versions import DB_MIGRATION_PLAN, DISCLAIMER_DE
from app.models.software_updates import (
    SoftwareComponent,
    SoftwareUpdateChannel,
    SoftwareUpdateEvent,
    SoftwareUpdatePackage,
    SoftwareUpdateRun,
)
from app.services.audit import write_audit
from app.services.software_updates.busy_gate import check_update_allowed
from app.services.software_updates.compatibility import check_compatibility
from app.services.software_updates.integrity import (
    canonical_package_bytes,
    sha256_hex,
    sign_package_bytes,
    verify_package_integrity,
)

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "data" / "fixtures"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event(
    db: Session,
    *,
    event: str,
    detail_de: str,
    package_id: str | None = None,
    run_id: str | None = None,
    component: str | None = None,
) -> None:
    db.add(
        SoftwareUpdateEvent(
            package_id=package_id,
            run_id=run_id,
            component=component,
            event=event,
            detail_de=detail_de,
        )
    )


def load_fixture_payload(name: str) -> dict[str, Any]:
    path = FIXTURE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Fixture nicht gefunden: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_signed_fixture_meta(payload: dict[str, Any]) -> dict[str, str]:
    body = canonical_package_bytes(payload)
    return {
        "sha256": sha256_hex(body),
        "signature": sign_package_bytes(body),
    }


def ingest_fixture_package(
    db: Session,
    *,
    channel_key: str,
    fixture_name: str,
    claimed_sha256: str | None = None,
    signature_hex: str | None = None,
    tamper: bool = False,
    user_id: str | None = None,
    workshop_id: str | None = None,
) -> SoftwareUpdatePackage:
    """Lädt Fixture-Paket, prüft Integrität/Kompatibilität, staged → awaiting_approval."""
    channel = db.scalar(
        select(SoftwareUpdateChannel).where(SoftwareUpdateChannel.key == channel_key)
    )
    if channel is None:
        raise ValueError(f"Unbekannter Updatekanal: {channel_key}")
    if not channel.enabled:
        raise ValueError("Updatekanal ist deaktiviert.")

    settings = get_settings()
    if channel.require_signing_cert and not settings.software_update_signing_cert_configured:
        pkg = SoftwareUpdatePackage(
            channel_id=channel.id,
            component="unknown",
            version="0.0.0",
            package_filename=fixture_name,
            content_sha256="",
            signature_hex=signature_hex,
            signature_ok=False,
            release_notes_de="",
            status="rejected",
            error_de=(
                "Produktive Auto-Updates gesperrt: kein Signaturzertifikat konfiguriert "
                "(software_update_signing_cert_configured=false)."
            ),
        )
        db.add(pkg)
        db.flush()
        _event(
            db,
            event="rejected_no_cert",
            detail_de=pkg.error_de or "",
            package_id=pkg.id,
        )
        db.commit()
        db.refresh(pkg)
        return pkg

    payload = load_fixture_payload(fixture_name)
    if tamper:
        # Simulierte Manipulation nach Signaturbildung
        payload = {**payload, "tampered": True}

    component = str(payload.get("component", "unknown"))
    version = str(payload.get("version", "0.0.0"))
    release_notes = str(payload.get("release_notes_de") or "")
    migration = payload.get("migration_plan") or DB_MIGRATION_PLAN

    meta = build_signed_fixture_meta(
        {k: v for k, v in payload.items() if k != "tampered"} if not tamper else payload
    )
    # Bei unverfälschtem Fixture: Signatur/Checksum aus Payload-Meta oder neu berechnet
    if claimed_sha256 is None and not tamper:
        claimed_sha256 = meta["sha256"]
    if signature_hex is None and not tamper:
        signature_hex = meta["signature"]
    if tamper and claimed_sha256 is None:
        # Angreifer behauptet alte Checksum
        clean = {k: v for k, v in payload.items() if k != "tampered"}
        claimed_sha256 = sha256_hex(canonical_package_bytes(clean))
        signature_hex = sign_package_bytes(canonical_package_bytes(clean))

    integrity = verify_package_integrity(
        payload,
        claimed_sha256=claimed_sha256 or "",
        signature_hex=signature_hex,
        require_signature=channel.require_signature,
    )

    pkg = SoftwareUpdatePackage(
        channel_id=channel.id,
        component=component,
        version=version,
        package_filename=fixture_name,
        content_sha256=integrity["actual_sha256"],
        signature_hex=signature_hex,
        signature_ok=integrity["signature_ok"],
        release_notes_de=release_notes,
        migration_plan_json=json.dumps(migration, ensure_ascii=False),
        payload_json=json.dumps(payload, ensure_ascii=False),
        status="staged",
    )
    db.add(pkg)
    db.flush()

    if not integrity["ok"]:
        pkg.status = "rejected"
        pkg.error_de = "; ".join(integrity["errors_de"])
        _event(
            db,
            event="rejected_integrity",
            detail_de=pkg.error_de,
            package_id=pkg.id,
            component=component,
        )
        write_audit(
            db,
            user_id=user_id,
            workshop_id=workshop_id,
            action="software_update_rejected",
            resource=f"{component}:{version}",
            detail="integrity",
        )
        db.commit()
        db.refresh(pkg)
        return pkg

    compat = check_compatibility(db, component=component, target_version=version)
    if not compat["compatible"]:
        pkg.status = "rejected"
        details = "; ".join(v["detail_de"] for v in compat["violations"])
        pkg.error_de = f"Inkompatible Version: {details}"
        _event(
            db,
            event="rejected_incompatible",
            detail_de=pkg.error_de,
            package_id=pkg.id,
            component=component,
        )
        write_audit(
            db,
            user_id=user_id,
            workshop_id=workshop_id,
            action="software_update_rejected",
            resource=f"{component}:{version}",
            detail="incompatible",
        )
        db.commit()
        db.refresh(pkg)
        return pkg

    # Nie ungeprüft auto-installieren
    if channel.auto_install_allowed and settings.software_update_auto_install_enabled:
        # Selbst dann nur wenn Zertifikat ok – hier bewusst trotzdem Freigabe erzwingen
        pass
    pkg.status = "awaiting_approval"
    _event(
        db,
        event="awaiting_approval",
        detail_de=(
            f"Paket {component}@{version} gestaged. Admin-Freigabe erforderlich. "
            + DISCLAIMER_DE
        ),
        package_id=pkg.id,
        component=component,
    )
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="software_update_staged",
        resource=f"{component}:{version}",
        detail=channel_key,
    )
    db.commit()
    db.refresh(pkg)
    return pkg


def reject_package(
    db: Session,
    pkg: SoftwareUpdatePackage,
    *,
    reason_de: str,
    user_id: str | None = None,
    workshop_id: str | None = None,
) -> SoftwareUpdatePackage:
    if pkg.status not in {"awaiting_approval", "staged"}:
        raise ValueError(f"Paketstatus „{pkg.status}“ erlaubt keine Ablehnung.")
    pkg.status = "rejected"
    pkg.error_de = reason_de
    _event(
        db,
        event="rejected_admin",
        detail_de=reason_de,
        package_id=pkg.id,
        component=pkg.component,
    )
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="software_update_admin_reject",
        resource=pkg.id,
        detail=reason_de,
    )
    db.commit()
    db.refresh(pkg)
    return pkg


def _simulate_healthcheck(component: str, version: str, *, fail: bool = False) -> dict:
    if fail:
        return {
            "ok": False,
            "component": component,
            "version": version,
            "checks": [{"name": "process_start", "ok": False, "detail_de": "Simulierter Healthcheck-Fehler."}],
        }
    return {
        "ok": True,
        "component": component,
        "version": version,
        "checks": [
            {"name": "process_start", "ok": True, "detail_de": "Start OK (Simulation)."},
            {"name": "version_endpoint", "ok": True, "detail_de": f"Version {version} gemeldet."},
        ],
    }


def approve_and_install(
    db: Session,
    pkg: SoftwareUpdatePackage,
    *,
    user_id: str | None = None,
    workshop_id: str | None = None,
    force_healthcheck_fail: bool = False,
    skip_busy_check: bool = False,
) -> SoftwareUpdateRun:
    """Admin-Freigabe → Busy-Gate → atomare Installation (Simulation) → Healthcheck → ggf. Rollback."""
    if pkg.status != "awaiting_approval":
        raise ValueError(f"Paketstatus „{pkg.status}“ – Freigabe nicht möglich.")

    settings = get_settings()
    channel = db.get(SoftwareUpdateChannel, pkg.channel_id)
    if channel and channel.require_signing_cert and not settings.software_update_signing_cert_configured:
        raise ValueError("Installation gesperrt: Signaturzertifikat nicht konfiguriert.")

    run = SoftwareUpdateRun(
        package_id=pkg.id,
        component=pkg.component,
        action="install",
        status="pending",
        to_version=pkg.version,
        triggered_by=user_id,
    )
    db.add(run)
    db.flush()

    if not skip_busy_check:
        busy = check_update_allowed(db, workshop_id=workshop_id)
        if not busy["allowed"]:
            run.status = "blocked_busy"
            run.busy_reason_de = busy["reason_de"]
            run.error_de = busy["reason_de"]
            run.finished_at = _now()
            run.summary_json = json.dumps({"blockers": busy["blockers"]}, ensure_ascii=False)
            _event(
                db,
                event="blocked_busy",
                detail_de=busy["reason_de"] or "Busy",
                package_id=pkg.id,
                run_id=run.id,
                component=pkg.component,
            )
            db.commit()
            db.refresh(run)
            return run

    comp = db.scalar(select(SoftwareComponent).where(SoftwareComponent.key == pkg.component))
    if comp is None:
        run.status = "failed"
        run.error_de = f"Komponente „{pkg.component}“ unbekannt."
        run.finished_at = _now()
        db.commit()
        db.refresh(run)
        return run

    run.from_version = comp.current_version
    run.status = "installing"
    pkg.approved_by = user_id
    pkg.approved_at = _now()
    db.flush()

    # Atomare Installation (Simulation): previous → current
    previous = comp.current_version
    comp.previous_version = previous
    comp.current_version = pkg.version
    run.status = "healthcheck"
    db.flush()

    health = _simulate_healthcheck(pkg.component, pkg.version, fail=force_healthcheck_fail)
    run.healthcheck_ok = health["ok"]
    run.summary_json = json.dumps({"health": health, "atomic": True}, ensure_ascii=False)

    if not health["ok"]:
        # Automatischer Rollback bei fehlgeschlagenem Healthcheck
        comp.current_version = previous
        comp.previous_version = pkg.version
        comp.health_status = "failed"
        comp.last_error_de = "Healthcheck fehlgeschlagen – Rollback ausgeführt."
        comp.last_healthcheck_at = _now()
        run.status = "rolled_back"
        run.action = "rollback"
        run.error_de = "Healthcheck fehlgeschlagen – automatischer Rollback."
        run.finished_at = _now()
        pkg.status = "failed"
        pkg.error_de = run.error_de
        _event(
            db,
            event="healthcheck_rollback",
            detail_de=run.error_de,
            package_id=pkg.id,
            run_id=run.id,
            component=pkg.component,
        )
        write_audit(
            db,
            user_id=user_id,
            workshop_id=workshop_id,
            action="software_update_rollback_auto",
            resource=f"{pkg.component}:{pkg.version}",
            detail="healthcheck_failed",
        )
        db.commit()
        db.refresh(run)
        return run

    comp.health_status = "ok"
    comp.last_error_de = None
    comp.last_healthcheck_at = _now()
    run.status = "succeeded"
    run.finished_at = _now()
    pkg.status = "installed"
    _event(
        db,
        event="installed",
        detail_de=f"{pkg.component} {previous} → {pkg.version} (Admin-Freigabe, Healthcheck OK).",
        package_id=pkg.id,
        run_id=run.id,
        component=pkg.component,
    )
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="software_update_installed",
        resource=f"{pkg.component}:{pkg.version}",
        detail=f"from:{previous}",
    )
    db.commit()
    db.refresh(run)
    return run


def _ensure_rollback_package(
    db: Session, component_key: str, target_version: str
) -> SoftwareUpdatePackage:
    pkg = db.scalar(
        select(SoftwareUpdatePackage)
        .where(SoftwareUpdatePackage.component == component_key)
        .order_by(SoftwareUpdatePackage.created_at.desc())
    )
    if pkg is not None:
        return pkg
    channel = db.scalar(select(SoftwareUpdateChannel).limit(1))
    if channel is None:
        raise ValueError("Kein Updatekanal für Rollback-Marker.")
    pkg = SoftwareUpdatePackage(
        channel_id=channel.id,
        component=component_key,
        version=target_version,
        package_filename="rollback-marker",
        content_sha256="",
        release_notes_de="Manueller Rollback",
        status="staged",
    )
    db.add(pkg)
    db.flush()
    return pkg


def rollback_component(
    db: Session,
    component_key: str,
    *,
    user_id: str | None = None,
    workshop_id: str | None = None,
) -> SoftwareUpdateRun:
    """Manueller Rollback auf previous_version."""
    comp = db.scalar(select(SoftwareComponent).where(SoftwareComponent.key == component_key))
    if comp is None or not comp.previous_version:
        raise ValueError("Kein vorheriger Stand für Rollback vorhanden.")

    pkg = _ensure_rollback_package(db, component_key, comp.previous_version)
    busy = check_update_allowed(db, workshop_id=workshop_id)
    if not busy["allowed"]:
        run = SoftwareUpdateRun(
            package_id=pkg.id,
            component=component_key,
            action="rollback",
            status="blocked_busy",
            busy_reason_de=busy["reason_de"],
            error_de=busy["reason_de"],
            finished_at=_now(),
            triggered_by=user_id,
            summary_json=json.dumps({"blockers": busy["blockers"]}, ensure_ascii=False),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    from_v = comp.current_version
    to_v = comp.previous_version
    run = SoftwareUpdateRun(
        package_id=pkg.id,
        component=component_key,
        action="rollback",
        status="installing",
        from_version=from_v,
        to_version=to_v,
        triggered_by=user_id,
    )
    db.add(run)
    db.flush()

    comp.current_version = to_v
    comp.previous_version = from_v
    health = _simulate_healthcheck(component_key, to_v)
    run.healthcheck_ok = health["ok"]
    run.summary_json = json.dumps({"health": health, "manual_rollback": True}, ensure_ascii=False)
    if health["ok"]:
        run.status = "succeeded"
        comp.health_status = "ok"
        if pkg.status == "installed":
            pkg.status = "rolled_back"
    else:
        run.status = "failed"
        run.error_de = "Rollback-Healthcheck fehlgeschlagen."
        comp.health_status = "degraded"
    run.finished_at = _now()
    _event(
        db,
        event="manual_rollback",
        detail_de=f"Rollback {component_key}: {from_v} → {to_v}",
        package_id=pkg.id,
        run_id=run.id,
        component=component_key,
    )
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="software_update_rollback",
        resource=f"{component_key}:{to_v}",
        detail=f"from:{from_v}",
    )
    db.commit()
    db.refresh(run)
    return run


def abort_run(
    db: Session,
    run: SoftwareUpdateRun,
    *,
    reason_de: str,
    user_id: str | None = None,
    workshop_id: str | None = None,
) -> SoftwareUpdateRun:
    """Bricht einen laufenden/pending Installationslauf ab und rollt zurück falls nötig."""
    if run.status in {"succeeded", "rolled_back", "aborted", "failed", "blocked_busy"}:
        raise ValueError(f"Lauf „{run.status}“ kann nicht abgebrochen werden.")

    comp = db.scalar(select(SoftwareComponent).where(SoftwareComponent.key == run.component))
    if comp and run.from_version and comp.current_version == run.to_version:
        comp.current_version = run.from_version
        if run.to_version:
            comp.previous_version = run.to_version

    run.status = "aborted"
    run.action = "abort"
    run.error_de = reason_de
    run.finished_at = _now()
    pkg = db.get(SoftwareUpdatePackage, run.package_id)
    if pkg and pkg.status in {"awaiting_approval", "approved", "installed"}:
        pkg.status = "failed"
        pkg.error_de = f"Abbruch: {reason_de}"

    _event(
        db,
        event="aborted",
        detail_de=reason_de,
        package_id=run.package_id,
        run_id=run.id,
        component=run.component,
    )
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="software_update_aborted",
        resource=run.id,
        detail=reason_de,
    )
    db.commit()
    db.refresh(run)
    return run
