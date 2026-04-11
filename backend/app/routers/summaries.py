from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.category import Category
from app.models.note import Note
from app.services import claude_service

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("/{category_id}")
async def get_summary(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat_result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    notes_result = await db.execute(
        select(Note)
        .where(Note.category_id == category_id)
        .order_by(Note.created_at.asc())
    )
    notes = notes_result.scalars().all()

    if not notes:
        raise HTTPException(status_code=404, detail="No notes in this category")

    notes_data = [
        {"content": n.content, "created_at": n.created_at.isoformat()}
        for n in notes
    ]

    summary_text = await claude_service.summarize_category(category.name, notes_data)

    return {
        "summary": summary_text,
        "note_count": len(notes),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "category_name": category.name,
    }
