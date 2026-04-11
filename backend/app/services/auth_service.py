from datetime import datetime, timedelta, timezone
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.user import User


async def verify_google_token(id_token_str: str) -> dict:
    request = google_requests.Request()
    idinfo = id_token.verify_oauth2_token(
        id_token_str,
        request,
        settings.google_client_id,
    )
    return idinfo


async def find_user_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    """Look up a user by Google ID without creating or modifying anything."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def upsert_user(db: AsyncSession, idinfo: dict) -> User:
    google_id = idinfo["sub"]
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_id=google_id,
            email=idinfo.get("email", ""),
            name=idinfo.get("name"),
            avatar_url=idinfo.get("picture"),
        )
        db.add(user)
    else:
        user.name = idinfo.get("name", user.name)
        user.avatar_url = idinfo.get("picture", user.avatar_url)

    await db.commit()
    await db.refresh(user)
    return user


def create_access_token(user_id: str, region: str = "default") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "region": region, "exp": expire},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
