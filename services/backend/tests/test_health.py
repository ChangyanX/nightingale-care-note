import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "nightingale-api"}
    assert response.headers["x-request-id"]


@pytest.mark.asyncio
async def test_authenticated_route_requires_bearer_token() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
