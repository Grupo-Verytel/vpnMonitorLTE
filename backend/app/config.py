"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the FortiGate VPN Monitor backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # FortiGate
    FORTIGATE_HOST: str = "127.0.0.1"
    FORTIGATE_TOKEN: str = ""
    FORTIGATE_VERIFY_SSL: bool = False
    FORTIGATE_TIMEOUT_SECONDS: int = 15

    # Database (AWS RDS MySQL 8)
    DATABASE_URL: str = "mysql+pymysql://user:pass@localhost:3306/fortigate_monitor?charset=utf8mb4"
    DATABASE_SSL_CA: str = ""  # Ruta al CA bundle de AWS RDS (opcional)

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_MINUTES: int = 1

    # Security
    INTERNAL_CRON_TOKEN: str = ""
    CORS_ORIGINS: str = "http://localhost:5173"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # Timezone
    TZ: str = "America/Bogota"

    # Retention
    SNAPSHOT_RETENTION_DAYS: int = 60

    # App metadata
    APP_NAME: str = "FortiGate VPN Monitor"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", validation_alias="RAILWAY_ENVIRONMENT")

    @field_validator("FORTIGATE_VERIFY_SSL", mode="before")
    @classmethod
    def parse_verify_ssl(cls, value: object) -> bool:
        """Parse boolean-like env values for SSL verification."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    @field_validator("SCHEDULER_ENABLED", "LOG_JSON", mode="before")
    @classmethod
    def parse_bool_fields(cls, value: object) -> bool:
        """Parse boolean-like env values."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def fortigate_base_url(self) -> str:
        """Build FortiGate API base URL from host."""
        host = self.FORTIGATE_HOST.strip()
        if host.startswith("http://") or host.startswith("https://"):
            return host.rstrip("/")
        return f"https://{host}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


settings = get_settings()
