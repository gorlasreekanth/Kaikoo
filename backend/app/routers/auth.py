from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.config import settings
from app.deps import get_current_user, get_all_regions
from app.models.user import User
from app.schemas.user import AuthResponse, UserOut
from app.services.auth_service import (
    verify_google_token,
    find_user_by_google_id,
    upsert_user,
    create_access_token,
)
from app.utils.geo import detect_region

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    id_token: str


@router.post("/google", response_model=AuthResponse)
async def google_login(
    body: GoogleLoginRequest,
    request: Request,
    regions: dict[str, async_sessionmaker] = Depends(get_all_regions),
):
    try:
        idinfo = await verify_google_token(body.id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_id = idinfo["sub"]

    # Search every regional DB for an existing user.
    for region, factory in regions.items():
        async with factory() as db:
            user = await find_user_by_google_id(db, google_id)
            if user:
                token = create_access_token(str(user.id), region=region)
                return AuthResponse(access_token=token, user=UserOut.model_validate(user))

    # New user — assign to nearest region based on timezone header.
    region = detect_region(request)
    factory = regions.get(region) or next(iter(regions.values()))
    async with factory() as db:
        user = await upsert_user(db, idinfo)
        token = create_access_token(str(user.id), region=region)
        return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/dev-login", response_model=AuthResponse)
async def dev_login(
    request: Request,
    regions: dict[str, async_sessionmaker] = Depends(get_all_regions),
):
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    idinfo = {
        "sub": "dev-user-001",
        "email": "dev@kaikoo.local",
        "name": "Dev User",
        "picture": None,
    }

    # Check all regions for existing dev user.
    for region, factory in regions.items():
        async with factory() as db:
            user = await find_user_by_google_id(db, idinfo["sub"])
            if user:
                token = create_access_token(str(user.id), region=region)
                return AuthResponse(access_token=token, user=UserOut.model_validate(user))

    # New dev user — assign to detected region.
    region = detect_region(request)
    factory = regions.get(region) or next(iter(regions.values()))
    async with factory() as db:
        user = await upsert_user(db, idinfo)
        token = create_access_token(str(user.id), region=region)
        return AuthResponse(access_token=token, user=UserOut.model_validate(user))
