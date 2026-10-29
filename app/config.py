from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATABASE_URL = "sqlite:///" + (_ROOT / "tasks.db").as_posix()
_PLACEHOLDER_SECRET = "changez-moi-par-un-secret-long"


class Settings(BaseSettings):
    app_name: str = "Tâches"
    database_url: str = _DEFAULT_DATABASE_URL
    jwt_secret: str
    jwt_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        extra="ignore",
    )

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_is_set(cls, value: str) -> str:
        secret = value.strip()
        if len(secret) < 16 or secret == _PLACEHOLDER_SECRET:
            raise ValueError("JWT_SECRET est absent ou trop court")
        return secret

    @field_validator("cors_origins")
    @classmethod
    def cors_origins_are_explicit(cls, value: str) -> str:
        origins = [item.strip() for item in value.split(",") if item.strip()]
        if not origins or "*" in origins:
            raise ValueError("CORS_ORIGINS doit lister des origines explicites")
        return ",".join(origins)

    @property
    def cors_origin_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
