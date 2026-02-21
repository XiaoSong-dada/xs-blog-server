from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.article_tag import ArticleTag


class TagRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, tag_id: UUID) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Tag | None:
        stmt = select(Tag).where(Tag.name == name).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Tag | None:
        stmt = select(Tag).where(Tag.slug == slug).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, tag: Tag) -> Tag:
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def delete(db: AsyncSession, tag: Tag) -> None:
        await db.delete(tag)
        await db.commit()

    @staticmethod
    async def get_tags_with_count(db: AsyncSession, limit: int = 10) -> Sequence[tuple[Tag, int]]:
        stmt = (
            select(Tag, func.count(ArticleTag.article_id).label("article_count"))
            .outerjoin(ArticleTag, Tag.id == ArticleTag.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(ArticleTag.article_id).desc(), Tag.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.all()
