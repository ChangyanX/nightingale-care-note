import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.domain.redaction import VerifiedRedaction
from app.domain.scribe import ScribeInteractionType, ScribeOutput
from app.infrastructure.llm.base import ProviderError, ProviderResult


class OllamaScribeProvider:
    """Second, fully local OpenAI-compatible provider adapter."""

    def __init__(
        self,
        *,
        model: str = "qwen3:4b",
        base_url: str = "http://127.0.0.1:11434/v1",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._transport = transport

    async def generate(
        self,
        redaction: VerifiedRedaction,
        *,
        interaction_type: ScribeInteractionType,
    ) -> ProviderResult:
        if not redaction.verified:
            raise ProviderError("redaction_not_verified", retryable=False)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only valid JSON matching the supplied schema; never infer identity."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Type: {interaction_type.value}\nRedacted source:\n{redaction.text}"
                    ),
                },
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "scribe", "schema": ScribeOutput.model_json_schema()},
            },
        }
        try:
            async with httpx.AsyncClient(timeout=60, transport=self._transport) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise ProviderError("provider_unavailable", retryable=True) from error
        if response.is_error:
            raise ProviderError(
                "provider_transient_error"
                if response.status_code >= 500
                else "provider_request_rejected",
                retryable=response.status_code >= 500,
            )
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError
            output = ScribeOutput.model_validate_json(content)
            usage = body.get("usage", {})
        except (KeyError, TypeError, ValueError, ValidationError, json.JSONDecodeError) as error:
            raise ProviderError("invalid_structured_output", retryable=False) from error
        if output.interaction_type is not interaction_type:
            raise ProviderError("interaction_type_mismatch", retryable=False)
        return ProviderResult(
            output=output,
            model=self.model,
            request_id=_string(body.get("id")),
            input_tokens=_integer(usage.get("prompt_tokens")),
            output_tokens=_integer(usage.get("completion_tokens")),
        )


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None
