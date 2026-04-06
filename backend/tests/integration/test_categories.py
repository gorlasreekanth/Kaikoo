"""Integration tests for /categories endpoints."""
import pytest
from unittest.mock import AsyncMock
from app.services import claude_service


def _mock_claude(mocker, category: str = "Work"):
    mocker.patch.object(claude_service, "process_note", AsyncMock(return_value={
        "category": category, "is_new_category": True, "append_to_note_id": None, "intent": None,
    }))


# ── GET /categories ───────────────────────────────────────────────────────────

async def test_list_categories_empty(client, auth_headers):
    resp = await client.get("/api/v1/categories", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_categories_returns_created(client, auth_headers, mocker):
    _mock_claude(mocker, "Work")
    await client.post("/api/v1/notes", json={"content": "note"}, headers=auth_headers)

    resp = await client.get("/api/v1/categories", headers=auth_headers)
    cats = resp.json()
    assert len(cats) == 1
    assert cats[0]["name"] == "Work"


async def test_list_categories_multiple(client, auth_headers, mocker):
    for name in ["Work", "Health", "Ideas"]:
        _mock_claude(mocker, name)
        await client.post("/api/v1/notes", json={"content": f"{name} note"}, headers=auth_headers)

    resp = await client.get("/api/v1/categories", headers=auth_headers)
    names = [c["name"] for c in resp.json()]
    assert set(names) == {"Work", "Health", "Ideas"}


async def test_list_categories_requires_auth(client):
    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 401


async def test_categories_have_color_and_count(client, auth_headers, mocker):
    _mock_claude(mocker, "Work")
    await client.post("/api/v1/notes", json={"content": "note"}, headers=auth_headers)

    cat = (await client.get("/api/v1/categories", headers=auth_headers)).json()[0]
    assert cat["color"].startswith("#")
    assert cat["note_count"] == 1


# ── DELETE /categories/{id} ───────────────────────────────────────────────────

async def test_delete_category(client, auth_headers, mocker):
    _mock_claude(mocker, "Temp")
    r = await client.post("/api/v1/notes", json={"content": "note"}, headers=auth_headers)
    cat_id = r.json()["category"]["id"]

    del_resp = await client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["ok"] is True

    cats = await client.get("/api/v1/categories", headers=auth_headers)
    assert cats.json() == []


async def test_delete_category_not_found(client, auth_headers):
    resp = await client.delete("/api/v1/categories/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_category_requires_auth(client):
    resp = await client.delete("/api/v1/categories/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 401


async def test_cannot_delete_another_users_category(client, mocker, db):
    from app.models.user import User
    from app.services.auth_service import create_access_token

    _mock_claude(mocker, "Private")

    user_a = User(email="a@test.com", name="A", google_id="ga-del")
    db.add(user_a)
    await db.commit()
    await db.refresh(user_a)
    headers_a = {"Authorization": f"Bearer {create_access_token(str(user_a.id))}"}
    r = await client.post("/api/v1/notes", json={"content": "A's note"}, headers=headers_a)
    cat_id = r.json()["category"]["id"]

    user_b = User(email="b@test.com", name="B", google_id="gb-del")
    db.add(user_b)
    await db.commit()
    await db.refresh(user_b)
    headers_b = {"Authorization": f"Bearer {create_access_token(str(user_b.id))}"}

    resp = await client.delete(f"/api/v1/categories/{cat_id}", headers=headers_b)
    assert resp.status_code == 404
