import uuid
from datetime import datetime
from app.schemas.base import Base 
from app.schemas.params import PageQuery
from typing import Optional

class FriendLinkOut(Base):
    id: uuid.UUID
    name: str | None = None
    url: str | None = None
    description: str | None = None
    logo_url: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class FriendLinkListQuery(PageQuery):
    name: Optional[str] = None