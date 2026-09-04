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


def _worker_http_error(status_code: int) -> WorkerBackendError:
    if status_code in {401, 403}:
        return WorkerBackendError("worker_database_authorization_failed", retryable=False)
    return WorkerBackendError(
        "worker_database_error",
        retryable=status_code >= 500,
    )


class SupabaseSourceDocumentLoader:
    """Loads the role-authored source text with the worker's service identity."""

    def __init__(
        self,
        settings: WorkerSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        service_key = settings.supabase_service_role_key.get_secret_value()
        if not service_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required by the source loader")
        self.base_url = str(settings.supabase_url).rstrip("/")
        self.service_key = service_key
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_key,
            "authorization": f"Bearer {self.service_key}",
        }

    async def _select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0, transport=self.transport) as client:
            response = await client.get(
                f"{self.base_url}/rest/v1/{table}",
                headers=self._headers(),
                params=params,
            )
        if response.is_error:
            if response.status_code in {401, 403}:
                raise _worker_http_error(response.status_code)
            raise WorkerBackendError(
                "worker_source_load_failed", retryable=response.status_code >= 500
            )
        body = response.json()
        if not isinstance(body, list) or not all(isinstance(item, dict) for item in body):
            raise WorkerBackendError("worker_database_shape_error", retryable=False)
        return body

    async def load(self, job: ScribeJob) -> SourceDocument:
        sources = await self._select(
            "source_records",
            {
                "select": "id,clinic_id,patient_id,created_by",
                "id": f"eq.{job.source_record_id}",
                "clinic_id": f"eq.{job.clinic_id}",
                "patient_id": f"eq.{job.patient_id}",
                "limit": "1",
            },
        )
        if not sources:
            raise WorkerBackendError("worker_source_not_found", retryable=False)

        source_entries = await self._select(
            "entries",
            {
                "select": "id,content_plaintext,author_role,created_at",
                "source_record_id": f"eq.{job.source_record_id}",
                "clinic_id": f"eq.{job.clinic_id}",
                "patient_id": f"eq.{job.patient_id}",
                "author_role": "neq.system",
                "order": "created_at.asc,id.asc",
                "limit": "20",
            },
        )
        text_parts = [
            str(entry.get("content_plaintext", "")).strip()
            for entry in source_entries
            if str(entry.get("content_plaintext", "")).strip()
        ]
        if not text_parts:
            raise WorkerBackendError("worker_source_empty", retryable=False)

        patients = await self._select(
            "patients",
            {
                "select": "display_name",
                "id": f"eq.{job.patient_id}",
                "clinic_id": f"eq.{job.clinic_id}",
                "limit": "1",
            },
        )
        known_names = [
            str(row["display_name"]).strip() for row in patients if row.get("display_name")
        ]

        created_by = sources[0].get("created_by")
        if created_by:
            profiles = await self._select(
                "profiles",
                {
                    "select": "display_name,preferred_name",
                    "id": f"eq.{created_by}",
                    "limit": "1",
                },
            )
            for profile in profiles:
                for field in ("display_name", "preferred_name"):
                    value = str(profile.get(field) or "").strip()
                    if value:
                        known_names.append(value)

        return SourceDocument(
            text="\n\n".join(text_parts),
            known_names=tuple(dict.fromkeys(known_names)),
        )


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
            raise _worker_http_error(response.status_code)
        return response.json()

    async def _insert(self, table: str, payload: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=15.0, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/rest/v1/{table}",
                headers={**self._headers(), "prefer": "return=minimal"},
                json=payload,
            )
        if response.is_error:
            raise _worker_http_error(response.status_code)

    async def claim(self) -> ScribeJob | None:
        body = await self._rpc("claim_ai_scribe_job", {"p_lease_seconds": 120})
        if body is None or (isinstance(body, dict) and body.get("id") is None):
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
