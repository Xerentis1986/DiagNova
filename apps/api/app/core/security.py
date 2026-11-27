from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Minimale Passwortpolitik (Demo/Produktion-Baseline; keine Konformität behauptet)
PASSWORD_MIN_LENGTH = 10


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_policy(password: str) -> tuple[bool, str | None]:
    """Prüft Mindestlänge und Zeichenklassen. Keine Passwort-Hints zurückgeben die das Passwort leaken."""
    if not password or len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Passwort mindestens {PASSWORD_MIN_LENGTH} Zeichen"
    classes = 0
    if any(c.islower() for c in password):
        classes += 1
    if any(c.isupper() for c in password):
        classes += 1
    if any(c.isdigit() for c in password):
        classes += 1
    if any(not c.isalnum() for c in password):
        classes += 1
    if classes < 3:
        return False, "Passwort braucht mind. 3 aus: Klein-/Großbuchstaben, Ziffer, Sonderzeichen"
    # Häufige Demo-Schwächen nicht blockieren (Seed-Passwörter), aber Leerzeichen-only ablehnen
    if password.strip() == "":
        return False, "Passwort ungültig"
    return True, None


def create_access_token(subject: str, role: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
        "typ": "access",
    }
    if extra:
        # Nie Secrets/Passwörter in JWT-Claims
        safe = {k: v for k, v in extra.items() if k.lower() not in {"password", "secret", "token"}}
        payload.update(safe)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Ungültiges oder abgelaufenes Token") from exc
    if payload.get("typ") not in (None, "access"):
        # Legacy-Tokens ohne typ weiter akzeptieren; fremde Typen ablehnen
        raise ValueError("Ungültiger Token-Typ")
    return payload


def is_insecure_default_secret(secret: str | None = None) -> bool:
    settings = get_settings()
    value = secret if secret is not None else settings.jwt_secret
    return value in {
        "change-me-to-a-long-random-secret",
        "test-secret-not-for-production",
        "",
    }
