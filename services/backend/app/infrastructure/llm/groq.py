import json
from copy import deepcopy
from typing import Any

import httpx
from pydantic import SecretStr, ValidationError

from app.domain.redaction import VerifiedRedaction
from app.domain.scribe import ScribeInteractionType, ScribeOutput
from app.infrastructure.llm.base import ProviderError, ProviderResult

_SYSTEM_PROMPT = """You are a clinical documentation extraction component.
Operate only on synthetic, redacted text. Return only the requested JSON schema.
Do not infer identities or facts absent from the source. Keep the summary concise.
Every fact, action, and highlight quote must be copied exactly from the redacted source.
Use occurrence_hint as the zero-based occurrence number when a quote repeats.
Use -1 when no occurrence hint is needed. Suggestions are unreviewed: never claim
that a clinician accepted or confirmed them."""


def _strict_response_schema() -> dict[str, Any]:
    """Return Groq strict-mode JSON Schema without weakening runtime validation."""

    schema = deepcopy(ScribeOutput.model_json_schema())

    def normalize(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if node.get("type") == "object" and isinstance(properties, dict):
                node["required"] = list(properties)
                node["additionalProperties"] = False
            # Pydantic emits defaults for nullable fields. Strict mode represents
            # optional values as required nullable properties and rejects defaults.
            node.pop("default", None)
            for value in node.values():
                normalize(value)
        elif isinstance(node, list):
            for value in node:
                normalize(value)

    normalize(schema)
    return schema


class GroqScribeProvider:
    def __init__(
        self,
        *,
        api_key: SecretStr,
        model: str = "openai/gpt-oss-20b",
        base_url: str = "https://api.groq.com/openai/v1",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key.get_secret_value():
            raise ProviderError("provider_not_configured", retryable=False)
        self._api_key = api_key
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
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Interaction type: {interaction_type.value}\n\n"
                        f"Redacted source:\n{redaction.text}"
                    ),
                },
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "nightingale_scribe_output",
                    "strict": True,
                    "schema": _strict_response_schema(),
                },
            },
        }
        headers = {
            "authorization": f"Bearer {self._api_key.get_secret_value()}",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise ProviderError("provider_unavailable", retryable=True) from error

        if response.is_error:
            raise self._response_error(response.status_code)

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
            request_id=response.headers.get("x-request-id") or self._string_value(body.get("id")),
            input_tokens=self._integer_value(usage.get("prompt_tokens")),
            output_tokens=self._integer_value(usage.get("completion_tokens")),
        )

    @staticmethod
    def _response_error(status_code: int) -> ProviderError:
        if status_code in (408, 409, 429) or status_code >= 500:
            return ProviderError("provider_transient_error", retryable=True)
        if status_code in (401, 403):
            return ProviderError("provider_authentication_error", retryable=False)
        return ProviderError("provider_request_rejected", retryable=False)

    @staticmethod
    def _integer_value(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @staticmethod
    def _string_value(value: Any) -> str | None:
        return value if isinstance(value, str) else None
