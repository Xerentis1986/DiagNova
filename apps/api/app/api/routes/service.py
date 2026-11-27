"""Phase 11 – Servicekatalog und Gate-Simulation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import User
from app.schemas.service import (
    ServiceAbortRequest,
    ServiceCatalogOut,
    ServiceProcedureOut,
    ServiceRunOut,
    ServiceStartRequest,
)
from app.services import service_functions as svc

router = APIRouter(prefix="/service", tags=["service"])
Technician = Annotated[User, Depends(require_roles("admin", "technician"))]


@router.get("/catalog", response_model=ServiceCatalogOut)
def get_catalog(_user: CurrentUser) -> ServiceCatalogOut:
    payload = svc.catalog_payload()
    return ServiceCatalogOut(
        data_source=payload["data_source"],
        disclaimer_de=payload["disclaimer_de"],
        procedures=[ServiceProcedureOut.model_validate(p) for p in payload["procedures"]],
        excluded=payload["excluded"],
        live_execution_available=payload["live_execution_available"],
        hardware_live=payload["hardware_live"],
    )


@router.get("/procedures/{code}", response_model=ServiceProcedureOut)
def get_procedure(code: str, _user: CurrentUser) -> ServiceProcedureOut:
    from app.data.service_catalog import get_procedure as _get

    proc = _get(code)
    if proc is None or proc.get("safety_class") == "excluded":
        from fastapi import HTTPException, status

        if proc and proc.get("safety_class") == "excluded":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=proc.get("reason_de", "Ausgeschlossen"),
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prozedur nicht gefunden")
    return ServiceProcedureOut.model_validate(proc)


@router.get("/runs", response_model=list[ServiceRunOut])
def list_runs(user: CurrentUser, db: DbSession) -> list[ServiceRunOut]:
    return svc.list_runs(db, user)


@router.get("/runs/{run_id}", response_model=ServiceRunOut)
def get_run(run_id: str, user: CurrentUser, db: DbSession) -> ServiceRunOut:
    return svc.get_run(db, user, run_id)


@router.post("/procedures/{code}/start", response_model=ServiceRunOut)
def start_procedure(
    code: str,
    body: ServiceStartRequest,
    user: Technician,
    db: DbSession,
) -> ServiceRunOut:
    return svc.start_run(db, user, code, body)


@router.post("/runs/{run_id}/abort", response_model=ServiceRunOut)
def abort_procedure(
    run_id: str,
    body: ServiceAbortRequest,
    user: Technician,
    db: DbSession,
) -> ServiceRunOut:
    return svc.abort_run(db, user, run_id, body.reason_de)


@router.post("/procedures/{code}/execute-live")
def execute_live(code: str, _user: Technician) -> None:
    """Immer gesperrt – dokumentierter Blocker für Live-Schreiben."""
    svc.execute_live_blocked(code)
