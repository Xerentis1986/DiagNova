"""Phase 13 – Mandanten-Einladungen und Selbstregistrierung."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.subscriptions import WorkshopInvitation
from app.schemas.subscriptions import (
    InvitationAccept,
    InvitationCreate,
    InvitationOut,
    TenantRegisterOut,
    TenantRegisterRequest,
)
from app.services import subscriptions as subsvc
from app.services.tenant import require_admin_role, require_workshop_id

router = APIRouter(tags=["invitations"])


@router.post("/tenants/register", response_model=TenantRegisterOut)
def register_tenant(body: TenantRegisterRequest, db: DbSession) -> TenantRegisterOut:
    result = subsvc.register_tenant(
        db,
        workshop_name=body.workshop_name,
        admin_email=str(body.admin_email),
        admin_full_name=body.admin_full_name,
        password=body.password,
        country=body.country,
        plan_code=body.plan_code,
        acknowledge_demo=body.acknowledge_demo,
    )
    return TenantRegisterOut(**result)


@router.get("/workshop/me/invitations", response_model=list[InvitationOut])
def list_invitations(user: CurrentUser, db: DbSession) -> list[InvitationOut]:
    require_admin_role(user)
    wid = require_workshop_id(user)
    rows = (
        db.query(WorkshopInvitation)
        .filter(WorkshopInvitation.workshop_id == wid)
        .order_by(WorkshopInvitation.created_at.desc())
        .all()
    )
    return [
        InvitationOut(
            id=r.id,
            workshop_id=r.workshop_id,
            email=r.email,
            role=r.role,
            status=r.status,
            expires_at=r.expires_at,
            accepted_at=r.accepted_at,
            token=r.token if r.status == "pending" else None,
        )
        for r in rows
    ]


@router.post("/workshop/me/invitations", response_model=InvitationOut)
def create_invitation(body: InvitationCreate, user: CurrentUser, db: DbSession) -> InvitationOut:
    require_admin_role(user)
    wid = require_workshop_id(user)
    inv = subsvc.create_invitation(
        db, wid, user, email=str(body.email), role=body.role
    )
    return InvitationOut(
        id=inv.id,
        workshop_id=inv.workshop_id,
        email=inv.email,
        role=inv.role,
        status=inv.status,
        expires_at=inv.expires_at,
        accepted_at=inv.accepted_at,
        token=inv.token,
    )


@router.post("/invitations/accept", response_model=InvitationOut)
def accept_invitation(body: InvitationAccept, db: DbSession) -> InvitationOut:
    _user, inv = subsvc.accept_invitation(
        db,
        token=body.token,
        full_name=body.full_name,
        password=body.password,
    )
    return InvitationOut(
        id=inv.id,
        workshop_id=inv.workshop_id,
        email=inv.email,
        role=inv.role,
        status=inv.status,
        expires_at=inv.expires_at,
        accepted_at=inv.accepted_at,
        token=None,
    )
