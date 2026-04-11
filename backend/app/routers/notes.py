import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.note import Note
from app.models.category import Category
from app.models.integration import Integration
from app.schemas.note import NoteOut, NoteCreateResponse, PaginatedNotes, NoteAction, CalendarPayload, EmailPayload
from app.schemas.category import CategoryOut
from app.services import claude_service, notion_service
from app.utils.token_crypto import decrypt_token

router = APIRouter(prefix="/notes", tags=["notes"])

CATEGORY_COLORS = [
    "#7c6af7", "#f97316", "#06b6d4", "#22c55e",
    "#ec4899", "#eab308", "#8b5cf6", "#14b8a6",
]


async def _get_or_create_category(db: AsyncSession, user_id: uuid.UUID, name: str) -> Category:
    result = await db.execute(
        select(Category).where(Category.user_id == user_id, Category.name == name)
    )
    cat = result.scalar_one_or_none()
    if cat is None:
        # Pick a color based on existing count
        count_result = await db.execute(
            select(func.count()).select_from(Category).where(Category.user_id == user_id)
        )
        count = count_result.scalar() or 0
        color = CATEGORY_COLORS[count % len(CATEGORY_COLORS)]
        cat = Category(user_id=user_id, name=name, color=color, note_count=0)
        db.add(cat)
        await db.flush()
    return cat


class NoteCreateRequest(BaseModel):
    content: str
    source: str = "text"


class NoteUpdateRequest(BaseModel):
    content: str


@router.post("", response_model=NoteCreateResponse)
async def create_note(
    body: NoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Build context for Claude
    cats_result = await db.execute(
        select(Category).where(Category.user_id == current_user.id)
    )
    categories = cats_result.scalars().all()

    categories_context = []
    for cat in categories:
        notes_result = await db.execute(
            select(Note)
            .where(Note.category_id == cat.id)
            .order_by(Note.created_at.desc())
            .limit(3)
        )
        recent_notes = notes_result.scalars().all()
        categories_context.append({
            "id": str(cat.id),
            "name": cat.name,
            "recent_notes": [
                {"id": str(n.id), "snippet": n.content[:200]}
                for n in recent_notes
            ],
        })

    # Call Claude
    try:
        claude_result = await claude_service.process_note(body.content, categories_context)
    except Exception:
        claude_result = {"category": "General", "is_new_category": True, "append_to_note_id": None, "intent": None}

    category_name = claude_result.get("category", "General")
    append_to_id = claude_result.get("append_to_note_id")

    # Get or create category
    category = await _get_or_create_category(db, current_user.id, category_name)

    # Append or create note
    if append_to_id:
        try:
            append_uuid = uuid.UUID(append_to_id)
        except (ValueError, AttributeError):
            append_uuid = None
        note_result = await db.execute(
            select(Note).where(Note.id == append_uuid, Note.user_id == current_user.id)
        )
        existing_note = note_result.scalar_one_or_none()
        if existing_note:
            existing_note.content = existing_note.content + "\n\n" + body.content
            note = existing_note
        else:
            note = Note(user_id=current_user.id, category_id=category.id, content=body.content, source=body.source)
            db.add(note)
            category.note_count += 1
    else:
        note = Note(user_id=current_user.id, category_id=category.id, content=body.content, source=body.source)
        db.add(note)
        category.note_count += 1

    await db.commit()
    await db.refresh(note)
    await db.refresh(category)

    # Sync to Notion if connected
    try:
        notion_result = await db.execute(
            select(Integration).where(
                Integration.user_id == current_user.id,
                Integration.service == "notion",
            )
        )
        notion_integration = notion_result.scalar_one_or_none()
        if notion_integration and notion_integration.access_token:
            page_id = notion_integration.notion_default_page_id
            sync_result = notion_service.sync_note_to_notion(
                notion_integration, category_name, body.content, page_id
            )
            if not page_id:
                notion_integration.notion_default_page_id = sync_result.get("page_id")
                await db.commit()
    except Exception:
        pass  # Notion sync is best-effort

    # Build action from Claude intent
    action = None
    intent = claude_result.get("intent")
    if intent:
        if intent.get("type") == "calendar" and intent.get("calendar"):
            c = intent["calendar"]
            action = NoteAction(
                type="calendar",
                calendar=CalendarPayload(
                    title=c.get("title", ""),
                    start_time=c.get("start_time", ""),
                    end_time=c.get("end_time", ""),
                    description=c.get("description", ""),
                ),
            )
        elif intent.get("type") == "email" and intent.get("email"):
            e = intent["email"]
            action = NoteAction(
                type="email",
                email=EmailPayload(
                    recipient_hint=e.get("recipient_hint", ""),
                    subject=e.get("subject", ""),
                    body=e.get("body", ""),
                ),
            )

    return NoteCreateResponse(
        note=NoteOut.model_validate(note),
        category=CategoryOut.model_validate(category),
        action=action,
    )


@router.get("", response_model=PaginatedNotes)
async def list_notes(
    category_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Note).where(Note.user_id == current_user.id)
    if category_id:
        try:
            query = query.where(Note.category_id == uuid.UUID(category_id))
        except (ValueError, AttributeError):
            pass
    query = query.order_by(Note.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    notes = result.scalars().all()

    # Load categories
    for note in notes:
        if note.category_id:
            cat_result = await db.execute(select(Category).where(Category.id == uuid.UUID(str(note.category_id))))
            note.category = cat_result.scalar_one_or_none()

    return PaginatedNotes(
        items=[NoteOut.model_validate(n) for n in notes],
        total=total,
        page=page,
        limit=limit,
    )


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = _parse_uuid(note_id)
    result = await db.execute(select(Note).where(Note.id == uid, Note.user_id == current_user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.category_id:
        cat_result = await db.execute(select(Category).where(Category.id == uuid.UUID(str(note.category_id))))
        note.category = cat_result.scalar_one_or_none()
    return NoteOut.model_validate(note)


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: str,
    body: NoteUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = _parse_uuid(note_id)
    result = await db.execute(select(Note).where(Note.id == uid, Note.user_id == current_user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.content = body.content
    await db.commit()
    await db.refresh(note)
    if note.category_id:
        cat_result = await db.execute(select(Category).where(Category.id == uuid.UUID(str(note.category_id))))
        note.category = cat_result.scalar_one_or_none()
    return NoteOut.model_validate(note)


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = _parse_uuid(note_id)
    result = await db.execute(select(Note).where(Note.id == uid, Note.user_id == current_user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.category_id:
        cat_result = await db.execute(select(Category).where(Category.id == uuid.UUID(str(note.category_id))))
        cat = cat_result.scalar_one_or_none()
        if cat and cat.note_count > 0:
            cat.note_count -= 1
    await db.delete(note)
    await db.commit()
    return {"ok": True}
