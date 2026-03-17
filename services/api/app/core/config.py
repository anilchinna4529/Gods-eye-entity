from __future__ import annotations

import os


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


class Settings:
    environment: str = os.getenv("ENVIRONMENT", "local")

    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://godseye:godseye@localhost:5432/godseye"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    events_channel: str = os.getenv("EVENTS_CHANNEL", "godseye.events")

    jwt_secret: str = os.getenv("JWT_SECRET", "dev-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_exp_minutes: int = int(os.getenv("JWT_EXP_MINUTES", "720"))
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "godseye_session")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

    cors_origins: list[str] = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000"))

    data_dir: str = os.getenv("DATA_DIR", "/data")

    bootstrap_admin_email: str = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
    bootstrap_admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "change-me")


settings = Settings()

