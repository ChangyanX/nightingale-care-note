import logging
from pathlib import Path
from uuid import UUID

import pytest

from app.domain.redaction import VerifiedRedaction
from app.domain.scribe import ScribeInteractionType, ScribeOutput
from app.infrastructure.llm import FakeScribeProvider, ProviderError, ProviderResult
from app.worker import ScribeJob, ScribeWorker, SourceDocument

FIXTURE = Path(__file__).parent / "fixtures/scribe_doctor_consult.json"


def fixture_output() -> ScribeOutput:
    return ScribeOutput.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


def job(*, attempt_count: int = 1) -> ScribeJob:
    return ScribeJob(
        id=UUID("d0000000-0000-0000-0000-000000000001"),
        clinic_id=UUID("10000000-0000-0000-0000-000000000001"),
        patient_id=UUID("40000000-0000-0000-0000-000000000001"),
        source_record_id=UUID("60000000-0000-0000-0000-000000000003"),
        interaction_type=ScribeInteractionType.DOCTOR_CONSULT,
        attempt_count=attempt_count,
        max_attempts=3,
    )


class MemoryBackend:
    def __init__(self, source: SourceDocument, claimed_job: ScribeJob | None = None) -> None:
        self.source = source
        self.claimed_job = claimed_job or job()
        self.completed: list[tuple[ScribeJob, VerifiedRedaction, ProviderResult]] = []
        self.failures: list[tuple[str, bool, int]] = []

    async def claim(self) -> ScribeJob | None:
        claimed, self.claimed_job = self.claimed_job, None
        return claimed

    async def load_source(self, claimed_job: ScribeJob) -> SourceDocument:
        assert claimed_job.id == job().id
        return self.source

    async def complete(
        self,
        claimed_job: ScribeJob,
        redaction: VerifiedRedaction,
        result: ProviderResult,
    ) -> None:
        self.completed.append((claimed_job, redaction, result))

    async def fail(
        self,
        claimed_job: ScribeJob,
        *,
        safe_error_code: str,
        retryable: bool,
        retry_delay_seconds: int,
    ) -> None:
        assert claimed_job.id == job().id
        self.failures.append((safe_error_code, retryable, retry_delay_seconds))


@pytest.mark.asyncio
async def test_worker_redacts_before_provider_and_completes() -> None:
    backend = MemoryBackend(
        SourceDocument(
            "Parker Patient says the cough is still waking me at night.",
            known_names=("Parker Patient",),
        )
    )
    provider = FakeScribeProvider(fixture_output())

    processed = await ScribeWorker(backend, provider).run_once()

    assert processed is True
    assert backend.failures == []
    assert len(backend.completed) == 1
    assert len(provider.calls) == 1
    assert "Parker Patient" not in provider.calls[0][0].text
    assert "[REDACTED_NAME]" in provider.calls[0][0].text


@pytest.mark.asyncio
async def test_redaction_failure_never_calls_provider() -> None:
    backend = MemoryBackend(SourceDocument("   "))
    provider = FakeScribeProvider(fixture_output())

    await ScribeWorker(backend, provider).run_once()

    assert provider.calls == []
    assert backend.completed == []
    assert backend.failures == [("redaction_failed", False, 5)]


@pytest.mark.asyncio
async def test_transient_provider_failure_gets_deterministic_backoff() -> None:
    backend = MemoryBackend(
        SourceDocument("Synthetic cough consultation."),
        claimed_job=job(attempt_count=3),
    )
    provider = FakeScribeProvider(error=ProviderError("provider_transient_error", retryable=True))

    await ScribeWorker(backend, provider).run_once()

    assert backend.completed == []
    assert backend.failures == [("provider_transient_error", True, 20)]


@pytest.mark.asyncio
async def test_worker_rechecks_interaction_type_before_persistence() -> None:
    mismatched = fixture_output().model_copy(
        update={"interaction_type": ScribeInteractionType.NURSE_CONSULT}
    )
    backend = MemoryBackend(SourceDocument("Synthetic cough consultation."))

    await ScribeWorker(backend, FakeScribeProvider(mismatched)).run_once()

    assert backend.completed == []
    assert backend.failures == [("interaction_type_mismatch", False, 5)]


@pytest.mark.asyncio
async def test_safe_logs_do_not_contain_source_or_provider_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    source = "Sensitive synthetic source that must not enter logs."
    provider_error_body = "provider response body must not enter logs"
    backend = MemoryBackend(SourceDocument(source))
    provider = FakeScribeProvider(error=ProviderError("provider_unavailable", retryable=True))

    with caplog.at_level(logging.INFO):
        await ScribeWorker(backend, provider).run_once()

    assert source not in caplog.text
    assert provider_error_body not in caplog.text
    assert "provider_unavailable" not in source


@pytest.mark.asyncio
async def test_worker_returns_false_when_queue_is_empty() -> None:
    backend = MemoryBackend(SourceDocument("unused"))
    backend.claimed_job = None

    assert await ScribeWorker(backend, FakeScribeProvider(fixture_output())).run_once() is False
