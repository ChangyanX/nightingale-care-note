import json
import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

access_logger = logging.getLogger("nightingale.access")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID without inspecting or logging clinical request bodies."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class StructuredAccessLogMiddleware(BaseHTTPMiddleware):
    """Emit metadata-only JSON access events; query strings and bodies are excluded."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        event = {
            "event": "http_access",
            "request_id": getattr(request.state, "request_id", "unavailable"),
            "method": request.method,
            "path_template": str(getattr(route, "path", "unmatched")),
            "status_code": response.status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }
        access_logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))
        return response
