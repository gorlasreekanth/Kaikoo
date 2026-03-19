import uuid
from pydantic import BaseModel


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    user: UserOut
