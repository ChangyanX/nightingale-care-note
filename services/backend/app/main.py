from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.collaboration import router as collaboration_router
from app.api.foundation import router as foundation_router
from app.api.revisions import router as revisions_router
from app.api.scribe_jobs import router as scribe_jobs_router
from app.config import get_settings
from app.gateway import SupabaseGatewayError
from app.middleware import RequestIdMiddleware, StructuredAccessLogMiddleware
from app.schemas import HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Server-enforced API for the Nightingale longitudinal Care Note.",
)
app.add_middleware(StructuredAccessLogMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.include_router(foundation_router)
app.include_router(collaboration_router)
app.include_router(revisions_router)
app.include_router(scribe_jobs_router)


@app.exception_handler(SupabaseGatewayError)
async def handle_supabase_error(
    request: Request,
    error: SupabaseGatewayError,
) -> JSONResponse:
    del request
    if error.code == "40001":
        return JSONResponse(status_code=409, content={"detail": "Version conflict"})
    if error.code == "P0002" or error.status_code == 404:
        return JSONResponse(status_code=404, content={"detail": "Resource not found"})
    if error.status_code in (401, 403) or error.code == "42501":
        return JSONResponse(status_code=403, content={"detail": "Operation not permitted"})
    return JSONResponse(status_code=502, content={"detail": "Upstream data service error"})


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse()
