from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    billing,
    catalog,
    coding,
    commerce,
    customers,
    dashboard,
    data_updates,
    diagnostic_data,
    diagnostics,
    guided,
    invitations,
    lkw,
    preferences,
    protocols,
    reports,
    security,
    service,
    software_updates,
    subscriptions,
    tuning,
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
api_router.include_router(service.router)
api_router.include_router(guided.router)
api_router.include_router(coding.router)
api_router.include_router(subscriptions.router)
api_router.include_router(invitations.router)
api_router.include_router(billing.router)
api_router.include_router(admin.router)
api_router.include_router(software_updates.router)
api_router.include_router(security.router)
api_router.include_router(tuning.router)
api_router.include_router(lkw.router)
api_router.include_router(commerce.router)
