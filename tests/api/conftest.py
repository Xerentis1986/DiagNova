import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
PROTOCOLS = ROOT / "packages" / "diagnostic-protocols" / "src"

sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(PROTOCOLS))

os.environ["DATABASE_URL"] = "sqlite+psycopg:///:memory:"  # may fail – use sqlite:///
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-not-for-production"
os.environ["SEED_ADMIN_EMAIL"] = "admin@example.com"
os.environ["SEED_ADMIN_PASSWORD"] = "AdminDemo123!"
os.environ["SEED_TECH_EMAIL"] = "tech@example.com"
os.environ["SEED_TECH_PASSWORD"] = "TechDemo123!"
os.environ["PAYMENT_WEBHOOK_DEMO_SECRET"] = "diagnova-phase13-payment-stub-hmac-not-for-prod"

# Clear settings cache / re-import engine with sqlite
from app.core.config import get_settings

get_settings.cache_clear()

# Rebuild engine bound to sqlite for tests
import app.db.session as session_mod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session_mod.engine = engine
session_mod.SessionLocal = TestingSessionLocal

from app.db.base import Base
from app.db.seed import seed_all
from app.main import app
from app.db.session import get_db


@pytest.fixture()
def client():
    from app.core.rate_limit import login_limiter

    login_limiter.reset()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_all(db)
    db.close()

    def _override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    login_limiter.reset()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "AdminDemo123!"},
    )
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
