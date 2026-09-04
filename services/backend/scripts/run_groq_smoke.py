import argparse
import asyncio
import json

from app.domain.redaction import redact_for_llm
from app.domain.scribe import ScribeInteractionType
from app.infrastructure.llm import GroqScribeProvider, ProviderError
from app.worker.config import get_worker_settings

_SYNTHETIC_TRANSCRIPT = """Patient Name: Parker Patient
Doctor: What has changed since the last review?
Patient: The cough is still waking me at night, especially when the room is cold.
Doctor: Please continue the prescribed inhaler and record a seven-day peak-flow diary.
Patient: Should I arrange an earlier review if the nighttime cough becomes worse?
Doctor: Yes, contact the clinic if symptoms worsen or you develop breathing difficulty."""

_SYNTHETIC_NURSE_TRANSCRIPT = """Patient Name: Parker Patient
Nurse: Please show me how you use the inhaler.
Patient: I breathe in before pressing the canister.
Nurse: Press first, then breathe in slowly. You have now demonstrated the steps correctly.
Patient: I will practise twice daily and record any difficulty."""

_SYNTHETIC_PATIENT_SESSION = """Patient Name: Parker Patient
Assistant: What has changed since your consultation?
Patient: My cough has been worse at night and woke me twice.
Assistant: Is there anything you want the clinic to answer?
Patient: Should the planned review be brought forward?"""

_TRANSCRIPTS = {
    ScribeInteractionType.DOCTOR_CONSULT: _SYNTHETIC_TRANSCRIPT,
    ScribeInteractionType.NURSE_CONSULT: _SYNTHETIC_NURSE_TRANSCRIPT,
    ScribeInteractionType.AI_PATIENT_SESSION: _SYNTHETIC_PATIENT_SESSION,
}


async def run(interaction_type: ScribeInteractionType) -> None:
    settings = get_worker_settings()
    if settings.llm_provider != "groq":
        raise SystemExit("LLM_PROVIDER must be groq for this smoke command")
    if not settings.llm_api_key.get_secret_value():
        raise SystemExit("LLM_API_KEY is not configured in the ignored root .env")

    redaction = redact_for_llm(
        _TRANSCRIPTS[interaction_type],
        known_names=("Parker Patient",),
    )
    provider = GroqScribeProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=str(settings.llm_base_url),
    )
    try:
        result = await provider.generate(
            redaction,
            interaction_type=interaction_type,
        )
    except ProviderError as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "provider": "groq",
                    "model": settings.llm_model,
                    "safe_error_code": error.code,
                    "retryable": error.retryable,
                },
                indent=2,
            )
        )
        raise SystemExit(1) from None
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--interaction-type",
        choices=[item.value for item in ScribeInteractionType],
        default=ScribeInteractionType.DOCTOR_CONSULT.value,
    )
    arguments = parser.parse_args()
    asyncio.run(run(ScribeInteractionType(arguments.interaction_type)))
