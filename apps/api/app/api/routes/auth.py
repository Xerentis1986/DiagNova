from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.api import LoginRequest, LoginResponse, TokenUser
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DbSession) -> LoginResponse:
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-Mail oder Passwort falsch")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Benutzer deaktiviert")
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
    )
    theme = user.theme_preference if getattr(user, "theme_preference", None) in {
        "light",
        "dark",
        "system",
    } else "system"
    return LoginResponse(
        access_token=token,
        user=TokenUser(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,  # type: ignore[arg-type]
            is_active=user.is_active,
            theme_preference=theme,  # type: ignore[arg-type]
            workshop_id=user.workshop_id,
            is_platform_admin=bool(getattr(user, "is_platform_admin", False)),
        ),
    )


@router.get("/me", response_model=TokenUser)
def me(user: CurrentUser) -> TokenUser:
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
