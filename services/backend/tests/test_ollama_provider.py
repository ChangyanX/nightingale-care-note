from pathlib import Path

import httpx
import pytest

from app.domain.redaction import redact_for_llm
from app.domain.scribe import ScribeInteractionType, ScribeOutput
from app.infrastructure.llm import OllamaScribeProvider


@pytest.mark.asyncio
async def test_ollama_adapter_validates_local_openai_compatible_output() -> None:
    output = ScribeOutput.model_validate_json(
        Path("tests/fixtures/scribe_nurse_consult.json").read_text()
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "127.0.0.1"
        assert "authorization" not in request.headers
        return httpx.Response(
            200,
            json={
                "id": "local-1",
                "choices": [{"message": {"content": output.model_dump_json()}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            },
        )

    provider = OllamaScribeProvider(transport=httpx.MockTransport(handler))
    result = await provider.generate(
        redact_for_llm("Synthetic coaching completed."),
        interaction_type=ScribeInteractionType.NURSE_CONSULT,
    )
    assert result.model == "qwen3:4b"
    assert result.input_tokens == 12
