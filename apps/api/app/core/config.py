from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://diagnova:changeme_local_only@localhost:5432/diagnova"
    jwt_secret: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "AdminDemo123!"
    seed_tech_email: str = "tech@example.com"
    seed_tech_password: str = "TechDemo123!"
    app_name: str = "DiagNova API"
    demo_mode: bool = True

    # Phase 07 – Diagnosedaten-Updates (Standard: Scheduler aus, Intervall täglich)
    update_scheduler_enabled: bool = False
    update_interval_hours: int = 24
    update_fetch_timeout_sec: int = 30
    update_max_bytes: int = 2_000_000
    update_max_retries: int = 3
    update_retry_backoff_sec: float = 1.0
    update_scheduler_poll_sec: int = 60
    # HMAC-Schlüssel nur für Demo/Tests (nie Produktion-Secret committen)
    update_hmac_demo_secret: str = "diagnova-phase07-demo-hmac-not-for-prod"
    # Phase 13 – Payment-Stub Webhook-HMAC (kein echter PSP)
    payment_webhook_demo_secret: str = "diagnova-phase13-payment-stub-hmac-not-for-prod"
    # Phase 21 – Stripe (Testmodus; Live-Charges nur mit Freigabe-Flag)
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_live_charges_allowed: bool = False
    # Phase 21 – SMTP (leer = dry_run)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    # Phase 14 – Software-Updates (HMAC-Demo; produktives Code-Signing separat)
    software_update_hmac_demo_secret: str = "diagnova-phase14-software-hmac-not-for-prod"
    # Ohne echtes Signaturzertifikat: produktive Auto-Updates gesperrt
    software_update_signing_cert_configured: bool = False
    # Nie ungeprüfte Auto-Installs – Standard aus
    software_update_auto_install_enabled: bool = False

    # Phase 15 – Rate Limits / Security
    rate_limit_login_max: int = 10
    rate_limit_login_window_sec: float = 60.0
    rate_limit_write_max: int = 120
    rate_limit_write_window_sec: float = 60.0
    # Security-Header und Origin-Hinweis (Bearer-Auth → CSRF-Risiko gering)
    security_require_origin_for_cookie_auth: bool = False
    # Monitoring-Hinweis: kein echter Alert-Kanal ohne Zustimmung
    security_monitoring_enabled: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def is_allowed_origin(self, origin: str | None) -> bool:
        if not origin:
            return True  # native clients / curl ohne Origin
        return origin in self.cors_origin_list


@lru_cache
def get_settings() -> Settings:
    return Settings()
