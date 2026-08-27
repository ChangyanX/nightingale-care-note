from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infrastructure.llm import GroqScribeProvider, OllamaScribeProvider, ScribeProvider


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


def create_scribe_provider(settings: WorkerSettings) -> ScribeProvider:
    if settings.llm_provider == "groq":
        return GroqScribeProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=str(settings.llm_base_url),
        )
    if settings.llm_provider == "ollama":
        return OllamaScribeProvider(
            model=settings.llm_model,
            base_url=str(settings.llm_base_url),
        )
    raise ValueError("Unsupported LLM provider")
