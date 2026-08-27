from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.gateway import SupabaseGateway, SupabaseGatewayError

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthContext:
    user_id: UUID
    email: str | None
    access_token: str


async def get_auth_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if not settings.supabase_publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured",
        )

    try:
        user = await SupabaseGateway(settings).authenticate(credentials.credentials)
        user_id = UUID(str(user["id"]))
    except (KeyError, ValueError, SupabaseGatewayError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from error

    email_value = user.get("email")
    return AuthContext(
        user_id=user_id,
        email=email_value if isinstance(email_value, str) else None,
        access_token=credentials.credentials,
    )


AuthDependency = Annotated[AuthContext, Depends(get_auth_context)]
