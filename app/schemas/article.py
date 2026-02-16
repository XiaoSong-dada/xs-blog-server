from app.schemas.base import Base
from app.schemas.params import PageQuery
from uuid import UUID, uuid4
from typing import Optional
from pydantic import Field
from datetime import datetime
from dataclasses import dataclass


class Article(Base):
    id: UUID = Field(default_factory=uuid4)
    author_id: UUID = Field(default_factory=uuid4)
    title: str
    slug: str
    content_md: str
    view_count: int
    like_count: int = 0
    liked: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class ArticleQuery(PageQuery):
    title: Optional[str] = None
    slug: Optional[str] = None
    content_md: Optional[str] = None
    published_at: Optional[str] = None


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


class ArticlePublish(Base):
    id: UUID
    published_at: datetime


@dataclass
class BatchArticlePublish:
    id: list[UUID]
    published_at: datetime


class ArticleSearchQuery(PageQuery):
    kw: Optional[str] = None


# a.id, a.slug, a.title, a.published_at, a.view_count
class ArticleSearchOut(Base):
    id: UUID
    slug: str
    title: str
    published_at: Optional[datetime] = None
    view_count: int
    like_count: int = 0
    liked: bool = False
    rank: Optional[float] = None
    snippet: Optional[str] = None
    hit_title: Optional[bool] = None
    hit_content: Optional[bool] = None


class ArticleExportOut(Base):
    id: UUID
    title: str
    content_md: str
