from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_factory(url: str) -> async_sessionmaker[AsyncSession]:
    # prepared_statement_cache_size=0 is required for Supabase's PgBouncer pooler
    # (transaction mode doesn't support prepared statements). Harmless for local PG.
    engine = create_async_engine(
        url,
        echo=settings.environment == "development",
        connect_args={"prepared_statement_cache_size": 0},
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Build per-region session factories.
# If regional URLs are configured, use them; otherwise fall back to single DATABASE_URL.
REGIONS: dict[str, async_sessionmaker[AsyncSession]] = {}

if settings.database_url_apac:
    REGIONS["apac"] = _make_factory(settings.database_url_apac)
if settings.database_url_noam:
    REGIONS["noam"] = _make_factory(settings.database_url_noam)
if not REGIONS and settings.database_url:
    REGIONS["default"] = _make_factory(settings.database_url)


def get_session_factory(region: str) -> async_sessionmaker[AsyncSession]:
    """Return the session factory for a region, falling back to whatever is available."""
    return REGIONS.get(region) or next(iter(REGIONS.values()))


async def get_db():
    """Yield a session from the first available engine. Used by tests and local single-DB dev."""
    factory = next(iter(REGIONS.values()))
    async with factory() as session:
        yield session
