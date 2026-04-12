import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LLMSettings(Base):
    __tablename__ = "llm_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'anthropic' | 'openai' | null (use default)
    api_key: Mapped[str | None] = mapped_column(nullable=True)  # Fernet-encrypted
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)  # preferred model, null = app default
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="llm_settings")


from app.models.user import User  # noqa: E402
