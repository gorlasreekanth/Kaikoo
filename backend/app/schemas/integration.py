from pydantic import BaseModel


class IntegrationStatus(BaseModel):
    service: str
    connected: bool
    email: str | None = None
