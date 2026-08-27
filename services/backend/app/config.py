from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or the repository .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Nightingale Care Note API"
    environment: str = "development"
    log_level: str = "INFO"
    api_cors_origins: str = "http://localhost:3000"
    supabase_url: AnyHttpUrl = Field(default=AnyHttpUrl("http://127.0.0.1:54321"))
    supabase_publishable_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
