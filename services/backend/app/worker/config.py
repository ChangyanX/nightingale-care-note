from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Privileged settings imported only by the separately started worker process."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: AnyHttpUrl = Field(default=AnyHttpUrl("http://127.0.0.1:54321"))
    supabase_service_role_key: SecretStr = SecretStr("")
    llm_provider: str = "groq"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "openai/gpt-oss-20b"
    llm_base_url: AnyHttpUrl = Field(default=AnyHttpUrl("https://api.groq.com/openai/v1"))


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
