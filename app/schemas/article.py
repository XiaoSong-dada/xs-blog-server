from app.schemas.base import Base
from app.schemas.params import PageQuery
from uuid import UUID, uuid4
from typing import Optional
from pydantic import Field
from datetime import datetime


class Article(Base):
    id: UUID = Field(default_factory=uuid4)
    author_id: UUID = Field(default_factory=uuid4)
    title: str
    slug: str
    content_md: str
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class ArticleQuery(PageQuery):
    title: Optional[str] = None
    slug: Optional[str] = None
    content_md: Optional[str] = None


class ArticleCreated(Base):
    id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    title: str
    slug: str
    content_md: str


class ArticleUpdate(Base):
    id: UUID
    title: str
    slug: str
    content_md: str


class ArticleDelete(Base):
    id: UUID
    deleted_at: datetime
