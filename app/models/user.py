import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import ORMBase


class User(ORMBase):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    email: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str | None] = mapped_column(String(1), nullable=True)

    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_update_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_admin: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    nick_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
