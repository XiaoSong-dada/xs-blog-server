from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.tag import Tag
from app.repositories.tag_repo import TagRepository
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, TagWithCountResponse


class TagService:
    @staticmethod
    async def create_tag(db: AsyncSession, tag_in: TagCreate) -> TagResponse:
        existing_tag = await TagRepository.get_by_name(db, tag_in.name)
        if existing_tag:
            raise AppError("标签名称已存在", code=status.HTTP_409_CONFLICT)

        existing_slug = await TagRepository.get_by_slug(db, tag_in.slug)
        if existing_slug:
            raise AppError("标签别名已存在", code=status.HTTP_409_CONFLICT)

        tag = Tag(**tag_in.model_dump())
        created = await TagRepository.create(db, tag)
        return TagResponse.model_validate(created)

    @staticmethod
    async def get_tag(db: AsyncSession, tag_id: UUID) -> TagResponse:
        tag = await TagRepository.get_by_id(db, tag_id)
        if not tag:
            raise AppError("标签不存在", code=status.HTTP_404_NOT_FOUND)
        return TagResponse.model_validate(tag)

    @staticmethod
    async def get_all_tags(db: AsyncSession) -> list[TagResponse]:
        tags = await TagRepository.list_all(db)
        return [TagResponse.model_validate(tag) for tag in tags]

    @staticmethod
    async def get_tags_with_count(db: AsyncSession, limit: int = 10) -> list[TagWithCountResponse]:
        tags_with_count = await TagRepository.get_tags_with_count(db, limit)
        return [
            TagWithCountResponse(
                id=tag.id,
                name=tag.name,
                slug=tag.slug,
                created_at=tag.created_at,
                article_count=int(count),
            )
            for tag, count in tags_with_count
        ]

    @staticmethod
    async def update_tag(db: AsyncSession, tag_id: UUID, tag_in: TagUpdate) -> TagResponse:
        tag = await TagRepository.get_by_id(db, tag_id)
        if not tag:
            raise AppError("标签不存在", code=status.HTTP_404_NOT_FOUND)

        if tag_in.name and tag_in.name != tag.name:
            existing_tag = await TagRepository.get_by_name(db, tag_in.name)
            if existing_tag:
                raise AppError("标签名称已存在", code=status.HTTP_409_CONFLICT)
            tag.name = tag_in.name

        if tag_in.slug and tag_in.slug != tag.slug:
            existing_slug = await TagRepository.get_by_slug(db, tag_in.slug)
            if existing_slug:
                raise AppError("标签别名已存在", code=status.HTTP_409_CONFLICT)
            tag.slug = tag_in.slug

        await db.commit()
        await db.refresh(tag)
        return TagResponse.model_validate(tag)

    @staticmethod
    async def delete_tag(db: AsyncSession, tag_id: UUID) -> None:
        tag = await TagRepository.get_by_id(db, tag_id)
        if not tag:
            raise AppError("标签不存在", code=status.HTTP_404_NOT_FOUND)

        await TagRepository.delete(db, tag)
