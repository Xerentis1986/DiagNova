"""Phase 15 – Security-Dashboard, Privacy-Übersicht, Audit-Einsicht, Backup-Hinweise."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import PASSWORD_MIN_LENGTH, validate_password_policy
from app.models import AuditLog
from app.schemas.security import (
    AuditEntryOut,
    AuditListOut,
    BackupOverviewOut,
    PasswordCheckRequest,
    PasswordCheckResponse,
    PasswordPolicyOut,
    PrivacyOverviewOut,
    SecurityDashboardOut,
)
from app.services.security_overview import (
    backup_overview,
    build_dashboard,
    privacy_overview,
)
from app.services.tenant import require_admin_role, require_workshop_id

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/dashboard", response_model=SecurityDashboardOut)
def security_dashboard(user: CurrentUser) -> SecurityDashboardOut:
    """Übersicht Threat Model / Findings – für Admin und Platform-Admin."""
    if user.role != "admin" and not getattr(user, "is_platform_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Keine Berechtigung")
    return SecurityDashboardOut(**build_dashboard())


@router.get("/privacy", response_model=PrivacyOverviewOut)
def security_privacy(user: CurrentUser) -> PrivacyOverviewOut:
    require_workshop_id(user)
    return PrivacyOverviewOut(**privacy_overview())


@router.get("/backup", response_model=BackupOverviewOut)
def security_backup(user: CurrentUser) -> BackupOverviewOut:
    if user.role != "admin" and not getattr(user, "is_platform_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Keine Berechtigung")
    return BackupOverviewOut(**backup_overview())


@router.get("/audit", response_model=AuditListOut)
def security_audit(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
) -> AuditListOut:
    """Mandantenbezogene Audit-Einsicht (bereits redaktiert gespeichert)."""
    require_admin_role(user)
    wid = require_workshop_id(user)
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.workshop_id == wid)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        AuditEntryOut(
            id=r.id,
            action=r.action,
            resource=r.resource,
            detail=r.detail,
            user_id=r.user_id,
            workshop_id=r.workshop_id,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]
    return AuditListOut(
        items=items,
        note_de="Details sind serverseitig redaktiert (keine Passwörter; VIN/E-Mail/Telefon maskiert).",
    )


@router.get("/password-policy", response_model=PasswordPolicyOut)
def password_policy(_user: CurrentUser) -> PasswordPolicyOut:
    return PasswordPolicyOut(
        min_length=PASSWORD_MIN_LENGTH,
        require_classes=3,
        note_de="Baseline für neue Passwörter; Seed-Demo-Accounts unverändert.",
    )


@router.post("/password-check", response_model=PasswordCheckResponse)
def password_check(body: PasswordCheckRequest, user: CurrentUser) -> PasswordCheckResponse:
    """Prüft Politik – speichert/loggt das Passwort nicht."""
    _ = user
    ok, msg = validate_password_policy(body.password)
    return PasswordCheckResponse(ok=ok, message_de=msg)
