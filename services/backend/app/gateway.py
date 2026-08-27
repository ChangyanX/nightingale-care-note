from typing import Any

import httpx

from app.config import Settings


class SupabaseGatewayError(Exception):
    """Sanitized failure raised by the Supabase Auth or Data API."""

    def __init__(self, *, status_code: int, code: str | None = None) -> None:
        super().__init__(code or "supabase_request_failed")
        self.status_code = status_code
        self.code = code


class SupabaseGateway:
    def __init__(self, settings: Settings) -> None:
        self.base_url = str(settings.supabase_url).rstrip("/")
        self.publishable_key = settings.supabase_publishable_key

    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "apikey": self.publishable_key,
            "authorization": f"Bearer {access_token}",
            "content-type": "application/json",
        }

    async def authenticate(self, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{self.base_url}/auth/v1/user",
                headers=self._headers(access_token),
            )
        return self._decode_object(response)

    async def select(
        self,
        table: str,
        access_token: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{self.base_url}/rest/v1/{table}",
                headers=self._headers(access_token),
                params=params,
            )
        return self._decode_list(response)

    async def rpc(
        self,
        function_name: str,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                f"{self.base_url}/rest/v1/rpc/{function_name}",
                headers={**self._headers(access_token), "prefer": "return=representation"},
                json=payload,
            )
        return self._decode_object(response)

    @staticmethod
    def _error(response: httpx.Response) -> SupabaseGatewayError:
        code: str | None = None
        try:
            body = response.json()
            if isinstance(body, dict) and isinstance(body.get("code"), str):
                code = body["code"]
        except ValueError:
            pass
        return SupabaseGatewayError(status_code=response.status_code, code=code)

    @classmethod
    def _decode_object(cls, response: httpx.Response) -> dict[str, Any]:
        if response.is_error:
            raise cls._error(response)
        body = response.json()
        if not isinstance(body, dict):
            raise SupabaseGatewayError(status_code=502, code="unexpected_response_shape")
        return body

    @classmethod
    def _decode_list(cls, response: httpx.Response) -> list[dict[str, Any]]:
        if response.is_error:
            raise cls._error(response)
        body = response.json()
        if not isinstance(body, list) or not all(isinstance(item, dict) for item in body):
            raise SupabaseGatewayError(status_code=502, code="unexpected_response_shape")
        return body
