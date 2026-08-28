from typing import Any, Protocol
from uuid import UUID

import httpx

from app.domain.redaction import VerifiedRedaction
from app.domain.scribe import ScribeInteractionType, prepare_scribe_persistence
from app.infrastructure.llm import ProviderResult
from app.worker.config import WorkerSettings
from app.worker.scribe import ScribeJob, SourceDocument, WorkerBackendError


class SourceDocumentLoader(Protocol):
    async def load(self, job: ScribeJob) -> SourceDocument: ...


class SupabaseWorkerBackend:
    """Service-role job backend with atomic, RPC-owned output persistence."""

    def __init__(
        self,
        settings: WorkerSettings,
        source_loader: SourceDocumentLoader,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        service_key = settings.supabase_service_role_key.get_secret_value()
        if not service_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required by the worker")
        self.base_url = str(settings.supabase_url).rstrip("/")
        self.service_key = service_key
        self.provider_name = settings.llm_provider
        self.source_loader = source_loader
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_key,
            "authorization": f"Bearer {self.service_key}",
            "content-type": "application/json",
        }

    async def _rpc(self, function_name: str, payload: dict[str, Any]) -> object:
        async with httpx.AsyncClient(timeout=15.0, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/rest/v1/rpc/{function_name}",
                headers=self._headers(),
                json=payload,
            )
        if response.is_error:
            raise WorkerBackendError("worker_database_error", retryable=response.status_code >= 500)
        return response.json()

    async def _insert(self, table: str, payload: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=15.0, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/rest/v1/{table}",
                headers={**self._headers(), "prefer": "return=minimal"},
                json=payload,
            )
        if response.is_error:
            raise WorkerBackendError("worker_database_error", retryable=response.status_code >= 500)

    async def claim(self) -> ScribeJob | None:
        body = await self._rpc("claim_ai_scribe_job", {"p_lease_seconds": 120})
        if body is None:
            return None
        if not isinstance(body, dict):
            raise WorkerBackendError("worker_database_shape_error", retryable=False)
        try:
            return ScribeJob(
                id=UUID(str(body["id"])),
                clinic_id=UUID(str(body["clinic_id"])),
                patient_id=UUID(str(body["patient_id"])),
                source_record_id=UUID(str(body["source_record_id"])),
                interaction_type=ScribeInteractionType(str(body["interaction_type"])),
                attempt_count=int(body["attempt_count"]),
                max_attempts=int(body["max_attempts"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise WorkerBackendError("worker_database_shape_error", retryable=False) from error

    async def load_source(self, job: ScribeJob) -> SourceDocument:
        return await self.source_loader.load(job)

    async def complete(
        self,
        job: ScribeJob,
        redaction: VerifiedRedaction,
        result: ProviderResult,
    ) -> None:
        del redaction
        prepared = prepare_scribe_persistence(result.output)
        await self._rpc(
            "complete_ai_scribe_job",
            {
                "p_job_id": str(job.id),
                "p_content": prepared.content,
                "p_schema_version": result.output.schema_version,
                "p_provider_name": self.provider_name,
                "p_model_name": result.model,
                "p_input_tokens": result.input_tokens,
                "p_output_tokens": result.output_tokens,
                "p_highlights": list(prepared.highlights),
            },
        )

    async def fail(
        self,
        job: ScribeJob,
        *,
        safe_error_code: str,
        retryable: bool,
        retry_delay_seconds: int,
    ) -> None:
        await self._rpc(
            "fail_ai_scribe_job",
            {
                "p_job_id": str(job.id),
                "p_safe_error_code": safe_error_code,
                "p_retryable": retryable,
                "p_retry_delay_seconds": retry_delay_seconds,
            },
        )

    async def progress(self, job: ScribeJob, event: str) -> None:
        if event not in {"generating", "validating", "persisting"}:
            raise WorkerBackendError("worker_progress_event_invalid", retryable=False)
        await self._insert(
            "ai_job_events",
            {
                "clinic_id": str(job.clinic_id),
                "patient_id": str(job.patient_id),
                "job_id": str(job.id),
                "event_kind": event,
                "safe_metadata": {},
            },
        )
