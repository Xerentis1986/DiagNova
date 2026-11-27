from fastapi import APIRouter

from app.api.routes import auth, catalog, dashboard, diagnostics, preferences, vehicles

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(vehicles.router)
api_router.include_router(dashboard.router)
api_router.include_router(diagnostics.router)
api_router.include_router(catalog.router)
api_router.include_router(preferences.router)
