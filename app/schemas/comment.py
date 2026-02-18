from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

from pydantic import Field

from app.schemas.base import Base
from app.schemas.params import PageQuery


class CommentCreate(Base):
    content: str = Field(min_length=1)


class CommentReplyCreate(Base):
    content: str = Field(min_length=1)
    reply_to_user_id: Optional[UUID] = None


class CommentQuery(PageQuery):
    pass


class CommentOut(Base):
    id: UUID = Field(default_factory=uuid4)
    article_id: UUID
    user_id: UUID
    content: str
    parent_id: Optional[UUID] = None
    root_id: UUID
    reply_to_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    username: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None


class CommentThreadOut(Base):
    comment: CommentOut
    replies: list[CommentOut] = Field(default_factory=list)
