"""
Shared fixtures for all backend tests.
Uses in-memory SQLite so no PostgreSQL is required.
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so Base knows about every table
from app.models import user, note, category, integration  # noqa: F401
from app.database import Base
from app.deps import get_db, get_all_regions
from app.main import app
from app.models.user import User
from app.services.auth_service import create_access_token

from cryptography.fernet import Fernet
from app.utils import token_crypto

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
# Generate a valid Fernet key for the entire test session
_TEST_FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _setup_fernet(monkeypatch):
    """Ensure every test uses a valid Fernet key."""
    monkeypatch.setattr(token_crypto.settings, "fernet_key", _TEST_FERNET_KEY)
    token_crypto._fernet = None
    yield
    token_crypto._fernet = None


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.DefaultEventLoopPolicy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    eng = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def db(engine):
    """Each test gets a fresh session; all data is deleted after the test."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    # Wipe all rows between tests
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def client(db, engine):
    """HTTPX async client wired to the FastAPI app with the test DB."""
    async def _override_db():
        yield db

    test_factory = async_sessionmaker(engine, expire_on_commit=False)

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_all_regions] = lambda: {"default": test_factory}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db) -> User:
    user = User(
        email="test@kaikoo.local",
        name="Test User",
        google_id="google-test-001",
        avatar_url=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    token = create_access_token(str(test_user.id), region="default")
    return {"Authorization": f"Bearer {token}"}
