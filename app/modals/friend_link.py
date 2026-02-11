import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column 
from app.db.base import TimestampMixin

from app.db.base import ORMBase
class FriendLink(ORMBase, TimestampMixin):
    __tablename__ = "friendship_link"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str | None] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool | None] = mapped_column(
        Boolean,
        server_default="true"
    )