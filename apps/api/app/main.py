from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.security import is_insecure_default_secret
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.base import Base
from app.db.seed import seed_all
from app.db.session import SessionLocal, engine
from app.data.software_versions import COMPONENT_VERSIONS
from app.services.data_updates.scheduler import start_background_scheduler, stop_background_scheduler
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # For Docker/dev: create tables if migrations not yet applied (Alembic preferred).
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
    start_background_scheduler(SessionLocal)
    yield
    stop_background_scheduler()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=COMPONENT_VERSIONS["api"],
    description="DiagNova API – MVP mit simuliertem OBD. Keine echte Fahrzeugdiagnose.",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health() -> dict:
    insecure = is_insecure_default_secret()
    pilot = bool(getattr(settings, "pilot_mode", True))
    commercial = bool(getattr(settings, "commercial_go", False))
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "pilot_mode": pilot,
        "commercial_go": commercial,
        "go_status": "PILOT" if pilot and not commercial else ("GO" if commercial else "NO-GO"),
        "data_source_default": "simulated",
        "version": COMPONENT_VERSIONS["api"],
        "components": COMPONENT_VERSIONS,
        "security": {
            "jwt_secret_insecure_default": insecure,
            "headers": True,
            "login_rate_limit": True,
        },
        "message_de": (
            "API bereit – PILOT (Demo/Trial). Kein kommerzielles Voll-GO "
            "(Mollie-Key, SMTP, Rechtsfreigabe, HW fehlen)."
            if pilot and not commercial
            else "API bereit. Fahrzeugdaten im MVP sind simuliert."
        ),
        "prod_ready_hint_de": (
            "Nicht produktionsbereit: Default-JWT-Secret."
            if insecure
            else "JWT-Secret gesetzt; kommerzielles GO weiterhin an Checkliste gebunden."
        ),
        "customer_signup_de": {
            "register_ui": "/register",
            "login_ui": "/login",
            "invite_ui": "/invite?token=…",
            "billing_after_login": "/commerce",
            "operator": "/operator",
            "api_register": "POST /api/tenants/register",
        },
    }


@app.get("/version")
def version() -> dict:
    return {
        "api": COMPONENT_VERSIONS["api"],
        "web_expected": COMPONENT_VERSIONS["web"],
        "connector_expected": COMPONENT_VERSIONS["connector"],
        "components": COMPONENT_VERSIONS,
        "note_de": "Software-Versionen (Phase 14). Diagnosedaten-Versionen separat unter /api/data-updates.",
    }
