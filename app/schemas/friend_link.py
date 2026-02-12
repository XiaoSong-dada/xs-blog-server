import uuid
from datetime import datetime
from app.schemas.base import Base
from app.schemas.params import PageQuery
from typing import Optional
from uuid import UUID


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


class FriendLinkUpdate(Base):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class FriendLinkUpdateRequest(FriendLinkUpdate):
    id: UUID


class FriendLinkCreate(Base):
    name: str
    url: str
    description: Optional[str] = None
    sort_order: Optional[int] = 0
