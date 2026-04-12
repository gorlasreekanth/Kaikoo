"""Unit tests for claude_service with mocked OpenRouter client."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services import claude_service


def _make_response(text: str):
    """Build a minimal mock that mimics OpenAI chat completion response shape."""
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ── process_note ─────────────────────────────────────────────────────────────

async def test_process_note_basic_categorization(mocker):
    payload = {
        "category": "Work",
        "is_new_category": False,
        "append_to_note_id": None,
        "intent": None,
    }
    mock_create = AsyncMock(return_value=_make_response(json.dumps(payload)))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    result = await claude_service.process_note("Finish the Q3 report", [])
    assert result["category"] == "Work"
    assert result["is_new_category"] is False
    assert result["append_to_note_id"] is None
    assert result["intent"] is None


async def test_process_note_new_category(mocker):
    payload = {
        "category": "Home Improvement",
        "is_new_category": True,
        "append_to_note_id": None,
        "intent": None,
    }
    mock_create = AsyncMock(return_value=_make_response(json.dumps(payload)))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    result = await claude_service.process_note("Fix the leaky tap in the kitchen", [])
    assert result["is_new_category"] is True
    assert result["category"] == "Home Improvement"


async def test_process_note_calendar_intent(mocker):
    payload = {
        "category": "Meetings",
        "is_new_category": False,
        "append_to_note_id": None,
        "intent": {
            "type": "calendar",
            "calendar": {
                "title": "Team standup",
                "start_time": "2026-04-07T09:00:00",
                "end_time": "2026-04-07T09:30:00",
                "description": "Daily sync",
            },
            "email": None,
        },
    }
    mock_create = AsyncMock(return_value=_make_response(json.dumps(payload)))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    result = await claude_service.process_note("Schedule team standup tomorrow 9am", [])
    assert result["intent"]["type"] == "calendar"
    assert result["intent"]["calendar"]["title"] == "Team standup"


async def test_process_note_email_intent(mocker):
    payload = {
        "category": "Communication",
        "is_new_category": True,
        "append_to_note_id": None,
        "intent": {
            "type": "email",
            "calendar": None,
            "email": {
                "recipient_hint": "Alice",
                "subject": "Project update",
                "body": "Hi Alice, here is the latest update...",
            },
        },
    }
    mock_create = AsyncMock(return_value=_make_response(json.dumps(payload)))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    result = await claude_service.process_note("Email Alice about project update", [])
    assert result["intent"]["type"] == "email"
    assert result["intent"]["email"]["recipient_hint"] == "Alice"


async def test_process_note_strips_markdown_fences(mocker):
    raw = "```json\n" + json.dumps({"category": "Ideas", "is_new_category": True, "append_to_note_id": None, "intent": None}) + "\n```"
    mock_create = AsyncMock(return_value=_make_response(raw))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    result = await claude_service.process_note("Buy a whiteboard", [])
    assert result["category"] == "Ideas"


async def test_process_note_with_categories_context(mocker):
    """Verifies that categories context is passed through to the API call."""
    payload = {"category": "Work", "is_new_category": False, "append_to_note_id": None, "intent": None}
    mock_create = AsyncMock(return_value=_make_response(json.dumps(payload)))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    categories_context = [{"id": "cat-1", "name": "Work", "recent_notes": [{"id": "n-1", "snippet": "previous note"}]}]
    await claude_service.process_note("Follow-up on the report", categories_context)

    call_kwargs = mock_create.call_args[1]
    # Context appears in the user message (index 1)
    assert "Work" in call_kwargs["messages"][1]["content"]


async def test_process_note_append_to_existing(mocker):
    note_id = "550e8400-e29b-41d4-a716-446655440000"
    payload = {
        "category": "Work",
        "is_new_category": False,
        "append_to_note_id": note_id,
        "intent": None,
    }
    mock_create = AsyncMock(return_value=_make_response(json.dumps(payload)))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    result = await claude_service.process_note("Additional details about the report", [])
    assert result["append_to_note_id"] == note_id


# ── summarize_category ────────────────────────────────────────────────────────

async def test_summarize_category_returns_string(mocker):
    mock_create = AsyncMock(return_value=_make_response("This is a summary of your work notes."))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    notes = [{"content": "Finished report", "created_at": "2026-04-01T10:00:00"}]
    result = await claude_service.summarize_category("Work", notes)
    assert isinstance(result, str)
    assert len(result) > 0


async def test_summarize_category_empty_notes():
    result = await claude_service.summarize_category("Work", [])
    assert result == "No notes to summarize."


async def test_summarize_category_uses_summary_model(mocker):
    mock_create = AsyncMock(return_value=_make_response("Summary text here."))
    mocker.patch.object(claude_service.client.chat.completions, "create", mock_create)

    await claude_service.summarize_category("Work", [{"content": "Note", "created_at": "2026-04-01"}])
    call_kwargs = mock_create.call_args[1]
    assert call_kwargs["model"] == claude_service.settings.openrouter_summary_model
