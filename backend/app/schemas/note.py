import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.category import CategoryOut


class NoteOut(BaseModel):
    id: uuid.UUID
    content: str
    source: str
    category_id: uuid.UUID | None
    category: CategoryOut | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CalendarPayload(BaseModel):
    title: str
    start_time: str
    end_time: str
    description: str


class EmailPayload(BaseModel):
    recipient_hint: str
    subject: str
    body: str


class NoteAction(BaseModel):
    type: str  # 'calendar' | 'email'
    calendar: CalendarPayload | None = None
    email: EmailPayload | None = None


class NoteCreateResponse(BaseModel):
    note: NoteOut
    category: CategoryOut
    action: NoteAction | None = None


class PaginatedNotes(BaseModel):
    items: list[NoteOut]
    total: int
    page: int
    limit: int
