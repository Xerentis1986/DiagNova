from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import login_limiter
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.api import LoginRequest, LoginResponse, TokenUser
from app.services.audit import hash_ip_hint, write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _token_user(user: User) -> TokenUser:
    theme = user.theme_preference if getattr(user, "theme_preference", None) in {
        "light",
        "dark",
        "system",
    } else "system"
    return TokenUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        is_active=user.is_active,
        theme_preference=theme,  # type: ignore[arg-type]
        workshop_id=user.workshop_id,
        is_platform_admin=bool(getattr(user, "is_platform_admin", False)),
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DbSession, request: Request) -> LoginResponse:
    settings = get_settings()
    ip = _client_ip(request)
    ip_hint = hash_ip_hint(ip)
    # Rate-Limit nach IP und E-Mail (verhindert Credential-Stuffing)
    email_key = (body.email or "").strip().lower()
    for key in (f"ip:{ip}", f"email:{email_key}"):
        result = login_limiter.check(
            key,
            limit=settings.rate_limit_login_max,
            window_sec=settings.rate_limit_login_window_sec,
        )
        if not result.allowed:
            write_audit(
                db,
                user_id=None,
                workshop_id=None,
                action="login_rate_limited",
                resource="auth",
                detail=f"key={key.split(':', 1)[0]}",
                outcome="denied",
                ip_hint=ip_hint,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Zu viele Anmeldeversuche – bitte kurz warten",
                headers={"Retry-After": str(max(1, int(result.retry_after_sec)))},
            )

    user = db.query(User).filter(User.email == email_key).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        write_audit(
            db,
            user_id=user.id if user else None,
            workshop_id=user.workshop_id if user else None,
            action="login_failed",
            resource="auth",
            detail="invalid_credentials",
            outcome="failure",
            ip_hint=ip_hint,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-Mail oder Passwort falsch")
    if not user.is_active:
        write_audit(
            db,
            user_id=user.id,
            workshop_id=user.workshop_id,
            action="login_failed",
            resource="auth",
            detail="user_disabled",
            outcome="denied",
            ip_hint=ip_hint,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Benutzer deaktiviert")

    from app.services.mfa_totp import require_mfa_if_enabled

    require_mfa_if_enabled(user, getattr(body, "mfa_code", None))

    # Origin-Hinweis: bei gesetztem Origin gegen Allowlist prüfen (kein harter Block für curl/tests)
    origin = request.headers.get("origin")
    if origin and not settings.is_allowed_origin(origin):
        write_audit(
            db,
            user_id=user.id,
            workshop_id=user.workshop_id,
            action="login_origin_rejected",
            resource="auth",
            detail=f"origin={origin}",
            outcome="denied",
            ip_hint=ip_hint,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin nicht erlaubt",
        )

    token = create_access_token(
        user.id,
        user.role,
        extra={"workshop_id": user.workshop_id} if user.workshop_id else None,
    )
    write_audit(
        db,
        user_id=user.id,
        workshop_id=user.workshop_id,
        action="login",
        resource="auth",
        outcome="success",
        ip_hint=ip_hint,
    )
    return LoginResponse(access_token=token, user=_token_user(user))


@router.get("/me", response_model=TokenUser)
def me(user: CurrentUser) -> TokenUser:
    return _token_user(user)


@router.post("/logout")
def logout(user: CurrentUser, db: DbSession) -> dict[str, str]:
    """Client verwirft Token; serverseitig Audit. Keine Server-Session (stateless JWT)."""
    write_audit(
        db,
        user_id=user.id,
        workshop_id=user.workshop_id,
        action="logout",
        resource="auth",
        outcome="success",
    )
    return {"status": "ok", "message_de": "Token clientseitig verwerfen. JWT ist stateless."}


@router.post("/password-reset/request")
def password_reset_request(body: dict, db: DbSession) -> dict:
    """Startet Passwort-Reset – E-Mail dry_run ohne SMTP. Keine User-Enumeration."""
    from app.services import email_service

    email = str((body or {}).get("email") or "").strip().lower()
    user = db.query(User).filter(User.email == email).first() if email else None
    if user:
        email_service.send_template_email(
            template="password_reset",
            to_email=user.email,
            extra_body="Token-Flow lokal: Demo – Link in der App setzen.",
            force_dry_run=True,
        )
        write_audit(
            db,
            user_id=user.id,
            workshop_id=user.workshop_id,
            action="password_reset_requested",
            resource="auth",
            outcome="success",
        )
    return {
        "ok": True,
        "message_de": "Falls Konto existiert: Reset-Mail vorbereitet (dry_run ohne SMTP).",
    }


@router.post("/email-confirm/request")
def email_confirm_request(user: CurrentUser) -> dict:
    from app.services import email_service

    return email_service.send_template_email(
        template="email_confirm",
        to_email=user.email,
        force_dry_run=True,
    )
