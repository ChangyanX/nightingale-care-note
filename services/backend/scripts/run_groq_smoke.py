import asyncio
import json

from app.domain.redaction import redact_for_llm
from app.domain.scribe import ScribeInteractionType
from app.infrastructure.llm import GroqScribeProvider
from app.worker.config import get_worker_settings

_SYNTHETIC_TRANSCRIPT = """Patient Name: Parker Patient
Doctor: What has changed since the last review?
Patient: The cough is still waking me at night, especially when the room is cold.
Doctor: Please continue the prescribed inhaler and record a seven-day peak-flow diary.
Patient: Should I arrange an earlier review if the nighttime cough becomes worse?
Doctor: Yes, contact the clinic if symptoms worsen or you develop breathing difficulty."""


async def run() -> None:
    settings = get_worker_settings()
    if settings.llm_provider != "groq":
        raise SystemExit("LLM_PROVIDER must be groq for this smoke command")
    if not settings.llm_api_key.get_secret_value():
        raise SystemExit("LLM_API_KEY is not configured in the ignored root .env")

    redaction = redact_for_llm(
        _SYNTHETIC_TRANSCRIPT,
        known_names=("Parker Patient",),
    )
    provider = GroqScribeProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=str(settings.llm_base_url),
    )
    result = await provider.generate(
        redaction,
        interaction_type=ScribeInteractionType.DOCTOR_CONSULT,
    )
    print(
        json.dumps(
            {
                "status": "validated",
                "provider": "groq",
                "model": result.model,
                "request_id": result.request_id,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "redaction": redaction.safe_metadata(),
                "schema_version": result.output.schema_version,
                "interaction_type": result.output.interaction_type.value,
                "fact_count": len(result.output.facts),
                "action_count": len(result.output.actions),
                "highlight_count": len(result.output.highlights),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(run())
