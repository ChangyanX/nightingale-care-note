import base64
import binascii
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import (
    AccountProfileResponse,
    AvatarUploadRequest,
    AvatarUploadResponse,
    MembershipResponse,
    UpdateAccountProfileRequest,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
AVATAR_BUCKET = "profile-avatars"
MAX_AVATAR_BYTES = 1_048_576
AVATAR_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


def _valid_image_signature(content: bytes, content_type: str) -> bool:
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


async def _account_profile(
    auth: AuthDependency,
    client: SupabaseGateway,
    *,
    profile_row: dict[str, Any] | None = None,
) -> AccountProfileResponse:
    if profile_row is None:
        profiles = await client.select(
            "profiles",
            auth.access_token,
            {
                "select": "id,display_name,preferred_name,birth_date,avatar_path,avatar_mime_type",
                "id": f"eq.{auth.user_id}",
                "limit": "1",
            },
        )
        if not profiles:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile_row = profiles[0]
    memberships = await client.select(
        "clinic_memberships",
        auth.access_token,
        {"select": "clinic_id,role", "profile_id": f"eq.{auth.user_id}"},
    )
    patients = await client.select(
        "patients",
        auth.access_token,
        {
            "select": "id",
            "linked_profile_id": f"eq.{auth.user_id}",
            "limit": "1",
        },
    )
    avatar_url = None
    avatar_path = profile_row.get("avatar_path")
    if isinstance(avatar_path, str):
        avatar_url = await client.sign_storage_object(AVATAR_BUCKET, avatar_path, auth.access_token)
    return AccountProfileResponse(
        id=auth.user_id,
        email=auth.email,
        display_name=str(profile_row["display_name"]),
        preferred_name=str(profile_row.get("preferred_name") or profile_row["display_name"]),
        birth_date=profile_row.get("birth_date"),
        avatar_path=avatar_path if isinstance(avatar_path, str) else None,
        avatar_url=avatar_url,
        memberships=[MembershipResponse.model_validate(row) for row in memberships],
        linked_patient_id=patients[0]["id"] if patients else None,
    )


@router.get("/me/profile", response_model=AccountProfileResponse, tags=["account"])
async def get_account_profile(
    auth: AuthDependency,
    settings: SettingsDependency,
) -> AccountProfileResponse:
    return await _account_profile(auth, gateway(settings))


@router.patch("/me/profile", response_model=AccountProfileResponse, tags=["account"])
async def update_account_profile(
    request: UpdateAccountProfileRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> AccountProfileResponse:
    changes = request.model_dump(exclude_unset=True, mode="json")
    if not changes:
        raise HTTPException(status_code=422, detail="At least one profile field is required")
    if request.preferred_name is not None:
        changes["preferred_name"] = request.preferred_name.strip()
    client = gateway(settings)
    row = await client.rpc("update_own_profile", auth.access_token, {"p_changes": changes})
    return await _account_profile(auth, client, profile_row=row)


@router.post("/me/avatar", response_model=AvatarUploadResponse, tags=["account"])
async def upload_avatar(
    request: AvatarUploadRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> AvatarUploadResponse:
    try:
        content = base64.b64decode(request.data_base64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise HTTPException(status_code=422, detail="Avatar is not valid base64") from error
    if not content or len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Avatar must be no larger than 1 MB")
    if not _valid_image_signature(content, request.content_type):
        raise HTTPException(status_code=422, detail="Avatar content does not match its file type")

    extension = AVATAR_EXTENSIONS[request.content_type]
    object_path = f"{auth.user_id}/avatar.{extension}"
    client = gateway(settings)
    await client.upload_storage_object(
        AVATAR_BUCKET,
        object_path,
        auth.access_token,
        content,
        request.content_type,
    )
    await client.rpc(
        "update_own_profile",
        auth.access_token,
        {
            "p_changes": {
                "avatar_path": object_path,
                "avatar_mime_type": request.content_type,
            }
        },
    )
    signed_url = await client.sign_storage_object(AVATAR_BUCKET, object_path, auth.access_token)
    return AvatarUploadResponse(avatar_path=object_path, avatar_url=signed_url)
