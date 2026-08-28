import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.domain.redaction import RedactionError, VerifiedRedaction, redact_for_llm
from app.domain.scribe import ScribeInteractionType
from app.infrastructure.llm import ProviderError, ProviderResult, ScribeProvider

logger = logging.getLogger(__name__)


class WorkerBackendError(RuntimeError):
    """Sanitized worker storage failure safe to persist as a short code."""

    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class ScribeJob:
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    source_record_id: UUID
    interaction_type: ScribeInteractionType
    attempt_count: int
    max_attempts: int


@dataclass(frozen=True, slots=True)
class SourceDocument:
    text: str
    known_names: tuple[str, ...] = ()


class WorkerBackend(Protocol):
    async def claim(self) -> ScribeJob | None: ...

    async def load_source(self, job: ScribeJob) -> SourceDocument: ...

    async def complete(
        self,
        job: ScribeJob,
        redaction: VerifiedRedaction,
        result: ProviderResult,
    ) -> None: ...

    async def fail(
        self,
        job: ScribeJob,
        *,
        safe_error_code: str,
        retryable: bool,
        retry_delay_seconds: int,
    ) -> None: ...


@runtime_checkable
class ProgressBackend(Protocol):
    async def progress(self, job: ScribeJob, event: str) -> None: ...


class ScribeWorker:
    def __init__(self, backend: WorkerBackend, provider: ScribeProvider) -> None:
        self.backend = backend
        self.provider = provider

    async def run_once(self) -> bool:
        job = await self.backend.claim()
        if job is None:
            return False

        logger.info(
            "scribe_job_started",
            extra={"job_id": str(job.id), "attempt_count": job.attempt_count},
        )
        try:
            source = await self.backend.load_source(job)
            redaction = redact_for_llm(source.text, known_names=source.known_names)
            await self._progress(job, "generating")
            result = await self.provider.generate(
                redaction,
                interaction_type=job.interaction_type,
            )
            if result.output.interaction_type is not job.interaction_type:
                raise ProviderError("interaction_type_mismatch", retryable=False)
            await self._progress(job, "validating")
            await self._progress(job, "persisting")
            await self.backend.complete(job, redaction, result)
        except RedactionError:
            await self._fail(job, "redaction_failed", retryable=False)
        except WorkerBackendError as error:
            await self._fail(job, error.code, retryable=error.retryable)
        except ProviderError as error:
            await self._fail(job, error.code, retryable=error.retryable)
        except Exception:
            # Never log exception text: third-party errors may embed prompts or response bodies.
            await self._fail(job, "worker_unexpected_error", retryable=True)
        else:
            logger.info(
                "scribe_job_completed",
                extra={"job_id": str(job.id), "model": result.model},
            )
        return True

    async def _progress(self, job: ScribeJob, event: str) -> None:
        if isinstance(self.backend, ProgressBackend):
            await self.backend.progress(job, event)

    async def _fail(self, job: ScribeJob, safe_error_code: str, *, retryable: bool) -> None:
        retry_delay_seconds = min(300, 5 * (2 ** max(0, job.attempt_count - 1)))
        await self.backend.fail(
            job,
            safe_error_code=safe_error_code,
            retryable=retryable,
            retry_delay_seconds=retry_delay_seconds,
        )
        logger.warning(
            "scribe_job_failed",
            extra={
                "job_id": str(job.id),
                "safe_error_code": safe_error_code,
                "retryable": retryable,
            },
        )
