"""Phase 12 – Codierung / Programmierung: Identifikation, Gates, Framework."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import User
from app.schemas.coding import (
    CodingAbortRequest,
    CodingCatalogOut,
    CodingOperationOut,
    CodingRunOut,
    CodingStartRequest,
    CodingVehicleStateIn,
    CompatibilityCheckOut,
    EcuIdentificationOut,
    InterfacePrepOut,
)
from app.services import coding as svc

router = APIRouter(prefix="/coding", tags=["coding"])
Technician = Annotated[User, Depends(require_roles("admin", "technician"))]


@router.get("/catalog", response_model=CodingCatalogOut)
def get_catalog(_user: CurrentUser) -> CodingCatalogOut:
    payload = svc.catalog_payload()
    return CodingCatalogOut(
        data_source=payload["data_source"],
        disclaimer_de=payload["disclaimer_de"],
        operations=[CodingOperationOut.model_validate(o) for o in payload["operations"]],
        excluded=payload["excluded"],
        live_execution_available=payload["live_execution_available"],
        flash_available=payload["flash_available"],
        hardware_live=payload["hardware_live"],
        auto_retry_forbidden=payload["auto_retry_forbidden"],
        j2534_status=payload["j2534_status"],
        dpdu_status=payload["dpdu_status"],
    )


@router.get("/operations/{code}", response_model=CodingOperationOut)
def get_operation(code: str, _user: CurrentUser) -> CodingOperationOut:
    from app.data.coding_catalog import get_operation as _get

    op = _get(code)
    if op is None or op.get("safety_class") == "excluded":
        from fastapi import HTTPException, status

        if op and op.get("safety_class") == "excluded":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=op.get("reason_de", "Ausgeschlossen"),
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation nicht gefunden")
    return CodingOperationOut.model_validate(op)


@router.get("/identify", response_model=EcuIdentificationOut)
def identify(
    user: CurrentUser,
    db: DbSession,
    vehicle_id: str | None = Query(None),
) -> EcuIdentificationOut:
    return svc.identify_ecu(db, user, vehicle_id)


@router.post("/compatibility-check", response_model=CompatibilityCheckOut)
def compatibility_check(
    body: CodingVehicleStateIn,
    _user: CurrentUser,
) -> CompatibilityCheckOut:
    return svc.run_compatibility_checks(body)


@router.get("/interfaces", response_model=InterfacePrepOut)
def interfaces(_user: CurrentUser) -> InterfacePrepOut:
    return svc.interface_prep()


@router.get("/runs", response_model=list[CodingRunOut])
def list_runs(user: CurrentUser, db: DbSession) -> list[CodingRunOut]:
    return svc.list_runs(db, user)


@router.get("/runs/{run_id}", response_model=CodingRunOut)
def get_run(run_id: str, user: CurrentUser, db: DbSession) -> CodingRunOut:
    return svc.get_run(db, user, run_id)


@router.post("/operations/{code}/start", response_model=CodingRunOut)
def start_operation(
    code: str,
    body: CodingStartRequest,
    user: Technician,
    db: DbSession,
) -> CodingRunOut:
    return svc.start_run(db, user, code, body)


@router.post("/runs/{run_id}/abort", response_model=CodingRunOut)
def abort_operation(
    run_id: str,
    body: CodingAbortRequest,
    user: Technician,
    db: DbSession,
) -> CodingRunOut:
    return svc.abort_run(db, user, run_id, body)


@router.post("/operations/{code}/execute-live")
def execute_live(code: str, _user: Technician) -> None:
    """Immer gesperrt – dokumentierter Blocker für Live-Schreiben/Flash."""
    svc.execute_live_blocked(code)


@router.post("/operations/{code}/flash")
def flash(code: str, _user: Technician) -> None:
    """Immer gesperrt – keine echten Flash-Routinen ohne Spec/Freigabe."""
    svc.flash_blocked(code)
