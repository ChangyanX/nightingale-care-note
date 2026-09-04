import argparse
import asyncio
import logging

from app.worker import (
    ScribeWorker,
    SupabaseSourceDocumentLoader,
    SupabaseWorkerBackend,
    WorkerBackendError,
)
from app.worker.config import create_scribe_provider, get_worker_settings


async def run(*, once: bool, poll_interval: float) -> int:
    settings = get_worker_settings()
    source_loader = SupabaseSourceDocumentLoader(settings)
    backend = SupabaseWorkerBackend(settings, source_loader)
    worker = ScribeWorker(backend, create_scribe_provider(settings))

    logging.getLogger(__name__).info(
        "scribe_worker_started",
        extra={"provider": settings.llm_provider, "once": once},
    )
    while True:
        try:
            processed = await worker.run_once()
        except WorkerBackendError as error:
            logging.getLogger(__name__).error(
                "scribe_worker_unavailable code=%s retryable=%s",
                error.code,
                error.retryable,
            )
            if once or not error.retryable:
                return 1
            await asyncio.sleep(poll_interval)
            continue
        if once:
            return 0
        if not processed:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the durable Nightingale AI-scribe worker")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    parser.add_argument("--poll-interval", type=float, default=1.0)
    arguments = parser.parse_args()
    if not 0.1 <= arguments.poll_interval <= 30:
        parser.error("--poll-interval must be between 0.1 and 30 seconds")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        raise SystemExit(
            asyncio.run(run(once=arguments.once, poll_interval=arguments.poll_interval))
        )
    except KeyboardInterrupt:
        pass
