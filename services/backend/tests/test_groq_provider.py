import json
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from app.domain.redaction import redact_for_llm
from app.domain.scribe import ScribeInteractionType, ScribeOutput
from app.infrastructure.llm import GroqScribeProvider, ProviderError

FIXTURE = Path(__file__).parent / "fixtures/scribe_doctor_consult.json"


def fixture_output() -> ScribeOutput:
    return ScribeOutput.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_groq_request_contains_only_redacted_text_and_strict_schema() -> None:
    raw_name = "Parker Patient"
    redaction = redact_for_llm(
        f"{raw_name} says the cough is still waking me at night.",
        known_names=[raw_name],
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        request_body = json.loads(request.content)
        serialized = json.dumps(request_body)
        assert raw_name not in serialized
        assert "[REDACTED_NAME]" in serialized
        assert request_body["model"] == "openai/gpt-oss-20b"
        response_format = request_body["response_format"]
        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["strict"] is True
        schema = response_format["json_schema"]["schema"]
        assert set(schema["required"]) == set(schema["properties"])
        return httpx.Response(
            200,
            headers={"x-request-id": "groq-request-1"},
            json={
                "id": "completion-1",
                "choices": [{"message": {"content": fixture_output().model_dump_json()}}],
                "usage": {"prompt_tokens": 200, "completion_tokens": 100},
            },
        )

    provider = GroqScribeProvider(
        api_key=SecretStr("test-key-never-log"),
        transport=httpx.MockTransport(handler),
    )
    result = await provider.generate(
        redaction,
        interaction_type=ScribeInteractionType.DOCTOR_CONSULT,
    )

    assert result.output.interaction_type is ScribeInteractionType.DOCTOR_CONSULT
    assert result.request_id == "groq-request-1"
    assert result.input_tokens == 200
    assert result.output_tokens == 100


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "code", "retryable"),
    [
        (401, "provider_authentication_error", False),
        (400, "provider_request_rejected", False),
        (429, "provider_transient_error", True),
        (503, "provider_transient_error", True),
    ],
)
async def test_provider_errors_are_classified_without_response_body(
    status_code: int,
    code: str,
    retryable: bool,
) -> None:
    secret_body = "provider echoed a sensitive request"
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code, text=secret_body))
    provider = GroqScribeProvider(api_key=SecretStr("test-key"), transport=transport)

    with pytest.raises(ProviderError) as raised:
        await provider.generate(
            redact_for_llm("Synthetic cough consultation."),
            interaction_type=ScribeInteractionType.DOCTOR_CONSULT,
        )

    assert raised.value.code == code
    assert raised.value.retryable is retryable
    assert secret_body not in str(raised.value)


@pytest.mark.asyncio
async def test_invalid_or_mismatched_output_is_rejected() -> None:
    output = fixture_output().model_copy(
        update={"interaction_type": ScribeInteractionType.NURSE_CONSULT}
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": output.model_dump_json()}}]},
        )
    )
    provider = GroqScribeProvider(api_key=SecretStr("test-key"), transport=transport)

    with pytest.raises(ProviderError, match="interaction_type_mismatch"):
        await provider.generate(
            redact_for_llm("Synthetic cough consultation."),
            interaction_type=ScribeInteractionType.DOCTOR_CONSULT,
        )


def test_provider_requires_a_key_without_revealing_configuration() -> None:
    with pytest.raises(ProviderError, match="provider_not_configured") as raised:
        GroqScribeProvider(api_key=SecretStr(""))

    assert raised.value.retryable is False
