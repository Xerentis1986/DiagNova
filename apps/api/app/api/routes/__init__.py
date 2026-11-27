from fastapi import APIRouter

from app.api.routes import (
    auth,
    catalog,
    customers,
    dashboard,
    data_updates,
    diagnostic_data,
    diagnostics,
    preferences,
    protocols,
    reports,
    vehicle_history,
    vehicles,
    work_orders,
    workshop,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(workshop.router)
api_router.include_router(customers.router)
api_router.include_router(work_orders.router)
api_router.include_router(vehicles.router)
api_router.include_router(vehicle_history.router)
api_router.include_router(dashboard.router)
api_router.include_router(diagnostics.router)
api_router.include_router(reports.router)
api_router.include_router(catalog.router)
api_router.include_router(preferences.router)
api_router.include_router(protocols.router)
api_router.include_router(diagnostic_data.router)
api_router.include_router(data_updates.router)
