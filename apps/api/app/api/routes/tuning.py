"""Phase 18 – Optionales Chiptuning: Architektur-API (Geplant/deaktiviert)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import User
from app.schemas.tuning import (
    LegalGateCheckOut,
    TuningAbortRequest,
    TuningApprovalCreate,
    TuningApprovalOut,
    TuningBaselineCreate,
    TuningBaselineOut,
    TuningCatalogOut,
    TuningGateStateIn,
    TuningHistoryOut,
    TuningModuleStatusOut,
    TuningOperationOut,
    TuningRunOut,
    TuningStartRequest,
)
from app.services import tuning as svc

router = APIRouter(prefix="/tuning", tags=["tuning"])
Technician = Annotated[User, Depends(require_roles("admin", "technician"))]


@router.get("/status", response_model=TuningModuleStatusOut)
def get_status(_user: CurrentUser) -> TuningModuleStatusOut:
    return svc.module_status()


@router.get("/catalog", response_model=TuningCatalogOut)
def get_catalog(_user: CurrentUser) -> TuningCatalogOut:
    return svc.catalog_out()


@router.get("/operations/{code}", response_model=TuningOperationOut)
def get_operation(code: str, _user: CurrentUser) -> TuningOperationOut:
    from app.data.tuning_catalog import get_operation as _get
    from fastapi import HTTPException, status

    op = _get(code)
    if op is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation nicht gefunden")
    if op.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=op.get("reason_de", "Ausgeschlossen"),
        )
    return TuningOperationOut.model_validate(op)


@router.get("/baselines", response_model=list[TuningBaselineOut])
def baselines(user: CurrentUser, db: DbSession) -> list[TuningBaselineOut]:
    return svc.list_baselines(db, user)


@router.post("/baselines", response_model=TuningBaselineOut)
def create_baseline(
    body: TuningBaselineCreate,
    user: Technician,
    db: DbSession,
) -> TuningBaselineOut:
    return svc.register_baseline(db, user, body)


@router.get("/approvals", response_model=list[TuningApprovalOut])
def approvals(user: CurrentUser, db: DbSession) -> list[TuningApprovalOut]:
    return svc.list_approvals(db, user)


@router.post("/approvals", response_model=TuningApprovalOut)
def create_approval(
    body: TuningApprovalCreate,
    user: Technician,
    db: DbSession,
) -> TuningApprovalOut:
    return svc.register_approval(db, user, body)


@router.get("/history", response_model=list[TuningHistoryOut])
def history(
    user: CurrentUser,
    db: DbSession,
    vehicle_id: str | None = Query(None),
) -> list[TuningHistoryOut]:
    return svc.list_history(db, user, vehicle_id=vehicle_id)


@router.post("/legal-gates", response_model=LegalGateCheckOut)
def legal_gates(body: TuningGateStateIn, _user: CurrentUser) -> LegalGateCheckOut:
    return svc.run_legal_gates(body)


@router.get("/runs", response_model=list[TuningRunOut])
def list_runs(user: CurrentUser, db: DbSession) -> list[TuningRunOut]:
    return svc.list_runs(db, user)


@router.get("/runs/{run_id}", response_model=TuningRunOut)
def get_run(run_id: str, user: CurrentUser, db: DbSession) -> TuningRunOut:
    return svc.get_run(db, user, run_id)


@router.post("/operations/{code}/start", response_model=TuningRunOut)
def start_operation(
    code: str,
    body: TuningStartRequest,
    user: Technician,
    db: DbSession,
) -> TuningRunOut:
    return svc.start_run(db, user, code, body)


@router.post("/runs/{run_id}/abort", response_model=TuningRunOut)
def abort_operation(
    run_id: str,
    body: TuningAbortRequest,
    user: Technician,
    db: DbSession,
) -> TuningRunOut:
    return svc.abort_run(db, user, run_id, body)


@router.post("/operations/{code}/activate")
def activate(code: str, _user: Technician) -> None:
    """Immer gesperrt – produktive Tuning-Aktivierung."""
    svc.activate_blocked(code)


@router.post("/operations/{code}/map-change")
def map_change(code: str, _user: Technician) -> None:
    """Immer gesperrt – keine Kennfeldänderungen."""
    svc.map_change_blocked(code)


@router.post("/operations/{code}/flash")
def flash(code: str, _user: Technician) -> None:
    """Immer gesperrt – kein Tuning-Flash."""
    svc.flash_blocked(code)
