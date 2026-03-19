import uuid
from datetime import datetime
from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    note_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
