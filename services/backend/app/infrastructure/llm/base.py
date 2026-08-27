from dataclasses import dataclass
from typing import Protocol

from app.domain.redaction import VerifiedRedaction
from app.domain.scribe import ScribeInteractionType, ScribeOutput


class ProviderError(RuntimeError):
    """Sanitized provider failure safe to store as a short job error code."""

    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class ProviderResult:
    output: ScribeOutput
    model: str
    request_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ScribeProvider(Protocol):
    async def generate(
        self,
        redaction: VerifiedRedaction,
        *,
        interaction_type: ScribeInteractionType,
    ) -> ProviderResult: ...
