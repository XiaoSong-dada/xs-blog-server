from app.schemas.base import Base
from app.schemas.params import PageQuery
from app.schemas.tag import TagResponse
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import Field
from datetime import datetime
from dataclasses import dataclass


class Article(Base):
    id: UUID = Field(default_factory=uuid4)
    author_id: UUID = Field(default_factory=uuid4)
    author: Optional[str] = None
    title: str
    slug: str
    content_md: str
    view_count: int
    like_count: int = 0
    liked: bool = False
    bookmark_count: int = 0
    bookmarked: bool = False
    comment_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    tags: List[TagResponse] = Field(default_factory=list)


class ArticleQuery(PageQuery):
    title: Optional[str] = None
    slug: Optional[str] = None
    content_md: Optional[str] = None
    published_at: Optional[str] = None
    tag_id: Optional[UUID] = None


class ArticleCreated(Base):
    id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    title: str
    slug: str
    content_md: str
    tag_ids: Optional[List[UUID]] = None


class ArticleUpdate(Base):
    id: UUID
    title: str
    slug: str
    content_md: str
    tag_ids: Optional[List[UUID]] = None


class ArticleTagUpdate(Base):
    tag_ids: List[UUID] = Field(default_factory=list)


class ArticleTagBatchImport(Base):
    article_ids: List[UUID] = Field(default_factory=list)
    # Frontend contract uses `tags`; each item is a tag UUID.
    tags: List[UUID] = Field(default_factory=list)


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
    author_id: Optional[UUID] = None
    author: Optional[str] = None
    tags: List[TagResponse] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    view_count: int
    like_count: int = 0
    liked: bool = False
    bookmark_count: int = 0
    bookmarked: bool = False
    comment_count: int = 0
    rank: Optional[float] = None
    snippet: Optional[str] = None
    hit_title: Optional[bool] = None
    hit_content: Optional[bool] = None


class ArticleExportOut(Base):
    id: UUID
    title: str
    content_md: str
