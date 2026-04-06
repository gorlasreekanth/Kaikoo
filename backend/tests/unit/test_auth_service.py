"""Unit tests for auth_service: JWT creation and user upsert logic."""
import pytest
from jose import jwt
from app.services.auth_service import create_access_token, upsert_user
from app.config import settings
from app.models.user import User


# ── JWT ──────────────────────────────────────────────────────────────────────

def test_create_access_token_structure():
    token = create_access_token("user-123")
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "user-123"
    assert "exp" in payload


def test_create_access_token_different_ids_differ():
    t1 = create_access_token("user-aaa")
    t2 = create_access_token("user-bbb")
    assert t1 != t2


def test_create_access_token_is_string():
    token = create_access_token("any-id")
    assert isinstance(token, str)
    assert len(token) > 20


# ── upsert_user ───────────────────────────────────────────────────────────────

async def test_upsert_user_creates_new(db):
    idinfo = {
        "sub": "google-new-001",
        "email": "new@example.com",
        "name": "New User",
        "picture": "https://example.com/avatar.jpg",
    }
    user = await upsert_user(db, idinfo)
    assert user.id is not None
    assert user.email == "new@example.com"
    assert user.name == "New User"
    assert user.avatar_url == "https://example.com/avatar.jpg"
    assert user.google_id == "google-new-001"


async def test_upsert_user_updates_existing(db):
    idinfo = {"sub": "google-existing", "email": "existing@example.com", "name": "Old Name", "picture": None}
    user_first = await upsert_user(db, idinfo)

    idinfo["name"] = "New Name"
    idinfo["picture"] = "https://example.com/new.jpg"
    user_second = await upsert_user(db, idinfo)

    assert user_first.id == user_second.id  # same user row
    assert user_second.name == "New Name"
    assert user_second.avatar_url == "https://example.com/new.jpg"


async def test_upsert_user_preserves_id_on_update(db):
    idinfo = {"sub": "google-stable", "email": "stable@example.com", "name": "A", "picture": None}
    u1 = await upsert_user(db, idinfo)
    idinfo["name"] = "B"
    u2 = await upsert_user(db, idinfo)
    assert u1.id == u2.id


async def test_upsert_user_missing_optional_fields(db):
    """picture and name are optional — should not crash."""
    idinfo = {"sub": "google-minimal", "email": "minimal@example.com"}
    user = await upsert_user(db, idinfo)
    assert user.email == "minimal@example.com"
    assert user.name is None
