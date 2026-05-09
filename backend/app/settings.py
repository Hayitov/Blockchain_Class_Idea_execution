from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/.env lives next to pyproject.toml; keep settings self-contained.
_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(
        ...,
        validation_alias="DATABASE_URL",
    )
    sepolia_rpc_url: str = Field(
        ...,
        validation_alias="SEPOLIA_RPC_URL",
        description="Required. No fallback to public RPCs. Boot fails if missing.",
    )

    siwe_domain: str = Field("localhost:5173", validation_alias="SIWE_DOMAIN")
    siwe_uri: str = Field("http://localhost:5173", validation_alias="SIWE_URI")
    session_ttl_hours: int = Field(12, validation_alias="SESSION_TTL_HOURS")
    nonce_ttl_minutes: int = Field(5, validation_alias="NONCE_TTL_MINUTES")
    cookie_secure: bool = Field(False, validation_alias="COOKIE_SECURE")

    cors_allow_origins: str = Field(
        "http://localhost:5173",
        validation_alias="CORS_ALLOW_ORIGINS",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


settings = Settings()
