import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("user_id", "service"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service: Mapped[str] = mapped_column(String(50), nullable=False)  # 'google_calendar' | 'gmail' | 'notion'
    access_token: Mapped[str | None] = mapped_column(nullable=True)   # encrypted
    refresh_token: Mapped[str | None] = mapped_column(nullable=True)  # encrypted
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[str | None] = mapped_column(nullable=True)
    notion_workspace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notion_default_page_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="integrations")


from app.models.user import User  # noqa: E402
