"""Integration tests for /notes endpoints."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services import claude_service


def _mock_claude(mocker, payload: dict):
    mocker.patch.object(claude_service, "process_note", AsyncMock(return_value=payload))


BASIC_CLAUDE_RESPONSE = {
    "category": "Work",
    "is_new_category": True,
    "append_to_note_id": None,
    "intent": None,
}


# ── POST /notes ───────────────────────────────────────────────────────────────

async def test_create_note_returns_note_and_category(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    resp = await client.post("/api/v1/notes", json={"content": "Finish the roadmap", "source": "text"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["note"]["content"] == "Finish the roadmap"
    assert data["category"]["name"] == "Work"
    assert data["action"] is None


async def test_create_note_requires_auth(client):
    resp = await client.post("/api/v1/notes", json={"content": "test"})
    assert resp.status_code == 401


async def test_create_note_voice_source(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    resp = await client.post("/api/v1/notes", json={"content": "Voice note content", "source": "voice"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["note"]["source"] == "voice"


async def test_create_note_returns_calendar_action(client, auth_headers, mocker):
    payload = {
        "category": "Meetings",
        "is_new_category": True,
        "append_to_note_id": None,
        "intent": {
            "type": "calendar",
            "calendar": {"title": "Team sync", "start_time": "2026-04-07T10:00:00", "end_time": "2026-04-07T10:30:00", "description": ""},
            "email": None,
        },
    }
    _mock_claude(mocker, payload)
    resp = await client.post("/api/v1/notes", json={"content": "Schedule team sync tomorrow 10am"}, headers=auth_headers)
    assert resp.status_code == 200
    action = resp.json()["action"]
    assert action["type"] == "calendar"
    assert action["calendar"]["title"] == "Team sync"


async def test_create_note_returns_email_action(client, auth_headers, mocker):
    payload = {
        "category": "Comms",
        "is_new_category": True,
        "append_to_note_id": None,
        "intent": {
            "type": "email",
            "calendar": None,
            "email": {"recipient_hint": "Bob", "subject": "Hello", "body": "Hi Bob"},
        },
    }
    _mock_claude(mocker, payload)
    resp = await client.post("/api/v1/notes", json={"content": "Email Bob saying hello"}, headers=auth_headers)
    assert resp.status_code == 200
    action = resp.json()["action"]
    assert action["type"] == "email"
    assert action["email"]["recipient_hint"] == "Bob"


async def test_create_note_appends_to_existing(client, auth_headers, mocker, db):
    """When Claude returns append_to_note_id, the existing note's content is extended."""
    # Create the initial note
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    r1 = await client.post("/api/v1/notes", json={"content": "Part one"}, headers=auth_headers)
    note_id = r1.json()["note"]["id"]

    # Second note should append
    _mock_claude(mocker, {**BASIC_CLAUDE_RESPONSE, "is_new_category": False, "append_to_note_id": note_id})
    r2 = await client.post("/api/v1/notes", json={"content": "Part two"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["note"]["id"] == note_id
    assert "Part one" in r2.json()["note"]["content"]
    assert "Part two" in r2.json()["note"]["content"]


async def test_create_note_reuses_existing_category(client, auth_headers, mocker):
    """Second note in same category should reuse the existing Category row."""
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    await client.post("/api/v1/notes", json={"content": "Note A"}, headers=auth_headers)

    _mock_claude(mocker, {**BASIC_CLAUDE_RESPONSE, "is_new_category": False})
    await client.post("/api/v1/notes", json={"content": "Note B"}, headers=auth_headers)

    cats = await client.get("/api/v1/categories", headers=auth_headers)
    assert len(cats.json()) == 1


async def test_create_note_claude_failure_falls_back_to_general(client, auth_headers, mocker):
    """If Claude raises, the note still saves under 'General'."""
    mocker.patch.object(claude_service, "process_note", AsyncMock(side_effect=Exception("API error")))
    resp = await client.post("/api/v1/notes", json={"content": "A note that survives API failure"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["category"]["name"] == "General"


# ── GET /notes ────────────────────────────────────────────────────────────────

async def test_list_notes_empty(client, auth_headers):
    resp = await client.get("/api/v1/notes", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_notes_returns_created_notes(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    await client.post("/api/v1/notes", json={"content": "Note 1"}, headers=auth_headers)
    await client.post("/api/v1/notes", json={"content": "Note 2"}, headers=auth_headers)

    resp = await client.get("/api/v1/notes", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


async def test_list_notes_pagination(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    for i in range(5):
        await client.post("/api/v1/notes", json={"content": f"Note {i}"}, headers=auth_headers)

    resp = await client.get("/api/v1/notes?page=1&limit=2", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2


async def test_list_notes_filter_by_category(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    r = await client.post("/api/v1/notes", json={"content": "Work note"}, headers=auth_headers)
    cat_id = r.json()["category"]["id"]

    _mock_claude(mocker, {**BASIC_CLAUDE_RESPONSE, "category": "Personal", "is_new_category": True})
    await client.post("/api/v1/notes", json={"content": "Personal note"}, headers=auth_headers)

    resp = await client.get(f"/api/v1/notes?category_id={cat_id}", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["content"] == "Work note"


async def test_list_notes_isolated_between_users(client, mocker, db):
    """Notes from user A should not appear for user B."""
    from app.models.user import User
    from app.services.auth_service import create_access_token

    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)

    # User A
    user_a = User(email="a@test.com", name="A", google_id="ga")
    db.add(user_a)
    await db.commit()
    await db.refresh(user_a)
    headers_a = {"Authorization": f"Bearer {create_access_token(str(user_a.id))}"}
    await client.post("/api/v1/notes", json={"content": "User A note"}, headers=headers_a)

    # User B
    user_b = User(email="b@test.com", name="B", google_id="gb")
    db.add(user_b)
    await db.commit()
    await db.refresh(user_b)
    headers_b = {"Authorization": f"Bearer {create_access_token(str(user_b.id))}"}

    resp = await client.get("/api/v1/notes", headers=headers_b)
    assert resp.json()["total"] == 0


# ── GET /notes/{id} ───────────────────────────────────────────────────────────

async def test_get_note_by_id(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    created = await client.post("/api/v1/notes", json={"content": "Specific note"}, headers=auth_headers)
    note_id = created.json()["note"]["id"]

    resp = await client.get(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Specific note"


async def test_get_note_not_found(client, auth_headers):
    resp = await client.get("/api/v1/notes/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


# ── PATCH /notes/{id} ─────────────────────────────────────────────────────────

async def test_update_note_content(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    created = await client.post("/api/v1/notes", json={"content": "Original"}, headers=auth_headers)
    note_id = created.json()["note"]["id"]

    resp = await client.patch(f"/api/v1/notes/{note_id}", json={"content": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated"


async def test_update_note_not_found(client, auth_headers):
    resp = await client.patch("/api/v1/notes/00000000-0000-0000-0000-000000000000", json={"content": "X"}, headers=auth_headers)
    assert resp.status_code == 404


# ── DELETE /notes/{id} ────────────────────────────────────────────────────────

async def test_delete_note(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    created = await client.post("/api/v1/notes", json={"content": "Delete me"}, headers=auth_headers)
    note_id = created.json()["note"]["id"]

    del_resp = await client.delete(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["ok"] is True

    get_resp = await client.get(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_delete_note_not_found(client, auth_headers):
    resp = await client.delete("/api/v1/notes/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_decrements_category_note_count(client, auth_headers, mocker):
    _mock_claude(mocker, BASIC_CLAUDE_RESPONSE)
    r = await client.post("/api/v1/notes", json={"content": "To delete"}, headers=auth_headers)
    note_id = r.json()["note"]["id"]
    cat_id = r.json()["category"]["id"]

    await client.delete(f"/api/v1/notes/{note_id}", headers=auth_headers)

    cats = await client.get("/api/v1/categories", headers=auth_headers)
    cat = next(c for c in cats.json() if c["id"] == cat_id)
    assert cat["note_count"] == 0
