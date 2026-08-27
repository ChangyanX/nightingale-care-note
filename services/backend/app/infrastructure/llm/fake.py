from app.domain.redaction import VerifiedRedaction
from app.domain.scribe import ScribeInteractionType, ScribeOutput
from app.infrastructure.llm.base import ProviderError, ProviderResult


class FakeScribeProvider:
    """Deterministic offline provider used by unit tests and fixtures."""

    def __init__(
        self,
        output: ScribeOutput | None = None,
        *,
        error: ProviderError | None = None,
    ) -> None:
        self.output = output
        self.error = error
        self.calls: list[tuple[VerifiedRedaction, ScribeInteractionType]] = []

    async def generate(
        self,
        redaction: VerifiedRedaction,
        *,
        interaction_type: ScribeInteractionType,
    ) -> ProviderResult:
        if not redaction.verified:
            raise ProviderError("redaction_not_verified", retryable=False)
        self.calls.append((redaction, interaction_type))
        if self.error is not None:
            raise self.error
        if self.output is None:
            raise ProviderError("fake_output_missing", retryable=False)
        return ProviderResult(output=self.output, model="fake-scribe-v1", request_id="fake-request")
