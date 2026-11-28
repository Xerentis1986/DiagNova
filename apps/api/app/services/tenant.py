"""Mandanten-/Rollenhilfen – workshop_id immer aus autorisierter Sitzung."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User, Workshop

# Rollen Phase 08 (Erweiterung bestehender Auth)
ROLE_ADMIN = "admin"
ROLE_TECHNICIAN = "technician"
ROLE_VIEWER = "viewer"
ALL_ROLES = {ROLE_ADMIN, ROLE_TECHNICIAN, ROLE_VIEWER}
WRITE_ROLES = {ROLE_ADMIN, ROLE_TECHNICIAN}
ADMIN_ROLES = {ROLE_ADMIN}


def require_workshop_id(user: User) -> str:
    if not user.workshop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kein Werkstatt-Mandant zugeordnet",
        )
    return user.workshop_id


def get_user_workshop(db: Session, user: User) -> Workshop:
    wid = require_workshop_id(user)
    workshop = db.get(Workshop, wid)
    if workshop is None or workshop.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Werkstatt ungültig oder archiviert",
        )
    return workshop


def assert_same_tenant(user: User, workshop_id: str | None) -> None:
    wid = require_workshop_id(user)
    if workshop_id != wid:
        # Kein Leak fremder IDs
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nicht gefunden")


def require_write_role(user: User) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Keine Schreibberechtigung")


def require_admin_role(user: User) -> None:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nur Werkstatt-Admin")
