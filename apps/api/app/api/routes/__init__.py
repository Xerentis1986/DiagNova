from fastapi import APIRouter

from app.api.routes import auth, dashboard, diagnostics, vehicles

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(vehicles.router)
api_router.include_router(dashboard.router)
api_router.include_router(diagnostics.router)
