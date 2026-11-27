"""Phase 15: Sicherheit, Datenschutz, Rate-Limits, Audit-Redaction, IDOR/RBAC."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.rate_limit import login_limiter
from app.core.security import validate_password_policy
from app.db.session import SessionLocal
from app.models import AuditLog, User, Workshop
from app.models.workshop import Customer
from app.core.security import hash_password
from app.services.audit import redact_audit_detail


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_health_security_headers_and_version(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    body = res.json()
    assert body["version"] == "0.15.0"
    assert "security" in body
    assert body["security"]["login_rate_limit"] is True
    # Test-Secret ist als insecure markiert
    assert body["security"]["jwt_secret_insecure_default"] is True


def test_login_failed_audited_without_password(client: TestClient):
    login_limiter.reset()
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password-xyz"},
    )
    assert res.status_code == 401
    db = SessionLocal()
    try:
        row = (
            db.query(AuditLog)
            .filter(AuditLog.action == "login_failed")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert row is not None
        assert row.outcome == "failure"
        assert row.detail is not None
        assert "wrong-password" not in (row.detail or "").lower()
        assert "password=" not in (row.detail or "").lower()
    finally:
        db.close()


def test_login_rate_limit(client: TestClient):
    login_limiter.reset()
    # Limit in Tests: Settings default 10 / 60s – bewusst unter Limit bleiben für andere Tests
    # Hier Limit manuell eng prüfen über viele Fehlversuche mit eigener E-Mail
    for i in range(10):
        r = client.post(
            "/api/auth/login",
            json={"email": "ratelimit@example.com", "password": f"bad-pass-{i:02d}"},
        )
        assert r.status_code == 401, r.text
    blocked = client.post(
        "/api/auth/login",
        json={"email": "ratelimit@example.com", "password": "bad-pass-final"},
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    login_limiter.reset()


def test_security_dashboard_admin_only(client: TestClient, auth_headers: dict[str, str]):
    dash = client.get("/api/security/dashboard", headers=auth_headers)
    assert dash.status_code == 200, dash.text
    body = dash.json()
    assert body["audit_redaction"] is True
    assert body["security_headers"] is True
    assert len(body["threat_model"]) >= 8
    assert any(n["id"] == "T-RBAC-IDOR" for n in body["threat_model"])
    assert body["version"] == "0.15.0"

    tech = _login(client, "tech@example.com", "TechDemo123!")
    denied = client.get("/api/security/dashboard", headers=tech)
    assert denied.status_code == 403


def test_privacy_and_backup_endpoints(client: TestClient, auth_headers: dict[str, str]):
    priv = client.get("/api/security/privacy", headers=auth_headers)
    assert priv.status_code == 200
    assert "Keine rechtliche" in priv.json()["disclaimer_de"] or "keine" in priv.json()["disclaimer_de"].lower()
    assert len(priv.json()["processes"]) >= 3

    backup = client.get("/api/security/backup", headers=auth_headers)
    assert backup.status_code == 200
    assert backup.json()["recommended_steps_de"]
    assert "phase-16" in backup.json()["phase16_checklist_hint"]


def test_audit_list_redacted(client: TestClient, auth_headers: dict[str, str]):
    # Login erzeugt Audit
    res = client.get("/api/security/audit?limit=20", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "redaktiert" in body["note_de"].lower() or "Passwort" in body["note_de"]
    for item in body["items"]:
        detail = item.get("detail") or ""
        assert "AdminDemo123" not in detail
        assert "password=" not in detail.lower()


def test_redact_helper_masks_vin_and_password():
    raw = "password=SuperSecret123! vin=WVWZZZ3CZWE123456 email=kunde@example.com"
    out = redact_audit_detail(raw)
    assert out is not None
    assert "SuperSecret" not in out
    assert "[REDACTED]" in out
    assert "WVWZZZ3CZWE123456" not in out
    assert "kunde@example.com" not in out


def test_password_policy_and_check_endpoint(client: TestClient, auth_headers: dict[str, str]):
    ok, _ = validate_password_policy("short")
    assert ok is False
    ok, _ = validate_password_policy("GoodPass1!")
    assert ok is True

    weak = client.post(
        "/api/security/password-check",
        headers=auth_headers,
        json={"password": "abc"},
    )
    assert weak.status_code == 200
    assert weak.json()["ok"] is False

    strong = client.post(
        "/api/security/password-check",
        headers=auth_headers,
        json={"password": "Str0ng!Pass"},
    )
    assert strong.status_code == 200
    assert strong.json()["ok"] is True


def test_logout_audits(client: TestClient, auth_headers: dict[str, str]):
    res = client.post("/api/auth/logout", headers=auth_headers)
    assert res.status_code == 200
    db = SessionLocal()
    try:
        row = db.query(AuditLog).filter(AuditLog.action == "logout").first()
        assert row is not None
        assert row.outcome == "success"
    finally:
        db.close()


def test_idor_foreign_customer_stays_404(client: TestClient, auth_headers: dict[str, str]):
    db = SessionLocal()
    try:
        other = Workshop(
            name="Phase15 Fremd",
            country="AT",
            retention_days=365,
            is_example_data=True,
        )
        db.add(other)
        db.flush()
        foreign = Customer(
            workshop_id=other.id,
            display_name="Geheim",
            email="geheim@example.com",
            is_example_data=True,
        )
        db.add(foreign)
        db.commit()
        fid = foreign.id
    finally:
        db.close()

    res = client.get(f"/api/customers/{fid}", headers=auth_headers)
    assert res.status_code == 404
    # Security-Audit darf fremde IDs nicht leaken über andere Mandanten-Listen
    own = client.get("/api/customers", headers=auth_headers)
    assert fid not in {c["id"] for c in own.json()}


def test_viewer_cannot_write_customer(client: TestClient):
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        assert admin and admin.workshop_id
        viewer = User(
            email="viewer15@example.com",
            full_name="Viewer 15",
            hashed_password=hash_password("ViewerDemo123!"),
            role="viewer",
            workshop_id=admin.workshop_id,
        )
        db.add(viewer)
        db.commit()
    finally:
        db.close()

    headers = _login(client, "viewer15@example.com", "ViewerDemo123!")
    create = client.post(
        "/api/customers",
        headers=headers,
        json={"display_name": "Sollte scheitern", "force": True},
    )
    assert create.status_code == 403


def test_login_rejects_disallowed_origin(client: TestClient):
    login_limiter.reset()
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "AdminDemo123!"},
        headers={"Origin": "https://evil.example"},
    )
    assert res.status_code == 403
    login_limiter.reset()


def test_jwt_contains_typ_and_role(client: TestClient, auth_headers: dict[str, str]):
    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"
