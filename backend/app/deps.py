import uuid as uuid_lib
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.database import REGIONS, get_session_factory
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/google")


def _region_from_token(token: str) -> str | None:
    """Decode JWT and return the region claim, or None on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        region = payload.get("region")
        if region and region in REGIONS:
            return region
    except JWTError:
        pass
    return None


async def get_db_region(request: Request) -> str:
    """Extract the DB region from the JWT bearer token, falling back to default."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        region = _region_from_token(auth[7:])
        if region:
            return region
    return settings.default_region


async def get_db(region: str = Depends(get_db_region)) -> AsyncSession:
    """Yield a DB session for the caller's region."""
    factory = get_session_factory(region)
    async with factory() as session:
        yield session


def get_all_regions() -> dict[str, async_sessionmaker]:
    """Return the REGIONS dict. Exposed as a dependency so tests can override it."""
    return REGIONS


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        uid = uuid_lib.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
