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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
