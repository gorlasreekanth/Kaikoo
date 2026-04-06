"""Integration tests for /integrations endpoint."""
import pytest
from app.models.integration import Integration


# ── GET /integrations ─────────────────────────────────────────────────────────

async def test_list_integrations_all_disconnected(client, auth_headers):
    resp = await client.get("/api/v1/integrations", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    services = {i["service"] for i in data}
    assert services == {"google_calendar", "gmail", "notion"}
    assert all(not i["connected"] for i in data)


async def test_list_integrations_requires_auth(client):
    resp = await client.get("/api/v1/integrations")
    assert resp.status_code == 401


async def test_list_integrations_shows_connected_when_token_present(client, auth_headers, test_user, db):
    from app.utils.token_crypto import encrypt_token

    integration = Integration(
        user_id=test_user.id,
        service="gmail",
        access_token=encrypt_token("fake-access-token"),
        refresh_token=encrypt_token("fake-refresh-token"),
    )
    db.add(integration)
    await db.commit()

    resp = await client.get("/api/v1/integrations", headers=auth_headers)
    data = resp.json()
    gmail = next(i for i in data if i["service"] == "gmail")
    assert gmail["connected"] is True


async def test_list_integrations_not_connected_without_access_token(client, auth_headers, test_user, db):
    """An Integration row without an access_token is treated as disconnected."""
    integration = Integration(
        user_id=test_user.id,
        service="notion",
        access_token=None,
    )
    db.add(integration)
    await db.commit()

    resp = await client.get("/api/v1/integrations", headers=auth_headers)
    notion = next(i for i in resp.json() if i["service"] == "notion")
    assert notion["connected"] is False


async def test_integrations_isolated_between_users(client, mocker, db):
    """Integration connected for user A should not show as connected for user B."""
    from app.models.user import User
    from app.services.auth_service import create_access_token
    from app.utils.token_crypto import encrypt_token

    user_a = User(email="ia@test.com", name="A", google_id="ga-int")
    db.add(user_a)
    await db.commit()
    await db.refresh(user_a)
    db.add(Integration(user_id=user_a.id, service="gmail", access_token=encrypt_token("tok")))
    await db.commit()

    user_b = User(email="ib@test.com", name="B", google_id="gb-int")
    db.add(user_b)
    await db.commit()
    await db.refresh(user_b)
    headers_b = {"Authorization": f"Bearer {create_access_token(str(user_b.id))}"}

    resp = await client.get("/api/v1/integrations", headers=headers_b)
    gmail = next(i for i in resp.json() if i["service"] == "gmail")
    assert gmail["connected"] is False
