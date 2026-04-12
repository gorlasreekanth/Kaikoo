import json
from datetime import date
from app.services.llm_service import chat

PROCESS_NOTE_SYSTEM = """You are Kaikoo, a personal assistant that processes short notes.
You always respond with valid JSON only — no prose, no markdown fences.
The user's existing categories and their most recent notes are provided as context."""

PROCESS_NOTE_TEMPLATE = """NEW NOTE:
"{content}"

EXISTING CATEGORIES (name → recent note snippets):
{categories_json}

Respond with this exact JSON shape:
{{
  "category": "<category name>",
  "is_new_category": true | false,
  "append_to_note_id": "<uuid>" | null,
  "intent": null | {{
    "type": "calendar" | "email",
    "calendar": {{
      "title": "<string>",
      "start_time": "<ISO8601>",
      "end_time": "<ISO8601>",
      "description": "<string>"
    }} | null,
    "email": {{
      "recipient_hint": "<name or email>",
      "subject": "<string>",
      "body": "<string>"
    }} | null
  }}
}}

Rules:
- If the note continues a thought clearly related to an existing category's recent note, set append_to_note_id to that note's UUID.
- If the note belongs to an existing category but starts a new thought, set append_to_note_id to null and use that category name.
- If no category fits, set is_new_category to true and invent a concise category name (2-3 words, Title Case).
- If you detect meeting/event intent (times, dates, "schedule", "meeting"), populate the calendar field.
- If you detect email intent ("email", "send", "write to"), populate the email field.
- Dates/times must be ISO8601. Assume today is {today_date} if no year is given.
- If intent is unclear, set intent to null."""


async def process_note(content: str, categories_context: list[dict], user_llm_settings=None) -> dict:
    """
    Returns dict with keys: category, is_new_category, append_to_note_id, intent
    """
    categories_json = json.dumps(categories_context, indent=2) if categories_context else "[]"
    user_msg = PROCESS_NOTE_TEMPLATE.format(
        content=content,
        categories_json=categories_json,
        today_date=date.today().isoformat(),
    )

    raw = await chat(
        system=PROCESS_NOTE_SYSTEM,
        user_message=user_msg,
        role="fast",
        max_tokens=1024,
        user_llm_settings=user_llm_settings,
    )

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


SUMMARIZE_SYSTEM = """You are a personal assistant summarizing a user's private notes.
Be concise and insightful. Format the summary as clean prose paragraphs.
Do not use bullet lists unless the notes are highly discrete items.
Identify recurring themes and highlight any action items."""

SUMMARIZE_TEMPLATE = """Summarize the following notes from the "{category_name}" category.
There are {count} notes from {date_range}.

NOTES (oldest first):
{notes_text}

Write a summary of 2-4 paragraphs."""


async def summarize_category(category_name: str, notes: list[dict], user_llm_settings=None) -> str:
    if not notes:
        return "No notes to summarize."

    notes_text = "\n\n---\n\n".join(
        f"[{n['created_at']}]\n{n['content']}" for n in notes
    )
    date_range = f"{notes[0]['created_at'][:10]} – {notes[-1]['created_at'][:10]}"

    user_msg = SUMMARIZE_TEMPLATE.format(
        category_name=category_name,
        count=len(notes),
        date_range=date_range,
        notes_text=notes_text,
    )

    return await chat(
        system=SUMMARIZE_SYSTEM,
        user_message=user_msg,
        role="quality",
        max_tokens=2048,
        user_llm_settings=user_llm_settings,
    )
