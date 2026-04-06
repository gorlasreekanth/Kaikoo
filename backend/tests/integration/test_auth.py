"""Integration tests for /auth endpoints."""
import pytest
from unittest.mock import patch, AsyncMock
from app.config import settings


# ── POST /auth/dev-login ──────────────────────────────────────────────────────

async def test_dev_login_returns_token_and_user(client):
    resp = await client.post("/api/v1/auth/dev-login")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "dev@kaikoo.local"
    assert data["user"]["name"] == "Dev User"


async def test_dev_login_is_idempotent(client):
    """Calling dev-login twice should return the same user (upsert, not duplicate)."""
    r1 = await client.post("/api/v1/auth/dev-login")
    r2 = await client.post("/api/v1/auth/dev-login")
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]


async def test_dev_login_blocked_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    resp = await client.post("/api/v1/auth/dev-login")
    assert resp.status_code == 404
    monkeypatch.setattr(settings, "environment", "development")


# ── GET /auth/me ──────────────────────────────────────────────────────────────

async def test_get_me_returns_current_user(client, test_user, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


async def test_get_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_get_me_rejects_invalid_token(client):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


# ── POST /auth/google ─────────────────────────────────────────────────────────

async def test_google_login_rejects_invalid_token(client):
    resp = await client.post("/api/v1/auth/google", json={"id_token": "bad-token"})
    assert resp.status_code == 401


async def test_google_login_creates_user_on_valid_token(client):
    mock_idinfo = {
        "sub": "google-from-test",
        "email": "google@example.com",
        "name": "Google User",
        "picture": None,
    }
    with patch("app.services.auth_service.id_token") as mock_id_token:
        mock_id_token.verify_oauth2_token.return_value = mock_idinfo
        resp = await client.post("/api/v1/auth/google", json={"id_token": "valid-google-token"})

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "google@example.com"
