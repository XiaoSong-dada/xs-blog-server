from app.core.exceptions import AppError
from uuid import UUID, uuid4
from app.schemas.article import (
    ArticleQuery,
    ArticleCreated,
    ArticleUpdate,
    ArticleDelete,
    ArticlePublish,
    ArticleSearchQuery,
    BatchArticlePublish,
)
from fastapi import status
from app.utils.datetime_utils import utc_now
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.article_repo_async import ArticleRepoAsync


class ArticleService:
    @staticmethod
    async def get_article_page(
        db: AsyncSession,
        search: ArticleQuery | None = None,
        current_user_id: UUID | None = None,
    ) -> dict:
        search = search or ArticleQuery()

        article, total = await ArticleRepoAsync.list_article(
            db,
            limit=search.limit,
            offset=search.offset,
            search=search,
            user_id=current_user_id,
        )

        return {
            "data": [a.model_dump() for a in article],
            "total": total,
            "limit": search.limit,
            "offset": search.offset,
        }

    @staticmethod
    async def get_publish_article_page(
        db: AsyncSession,
        search: ArticleQuery | None = None,
        current_user_id: UUID | None = None,
    ) -> dict:
        search = search or ArticleQuery()

        article, total = await ArticleRepoAsync.list_publish_article(
            db,
            limit=search.limit,
            offset=search.offset,
            search=search,
            user_id=current_user_id,
        )

        return {
            "data": [a.model_dump() for a in article],
            "total": total,
            "limit": search.limit,
            "offset": search.offset,
        }

    @staticmethod
    async def search_publish_article(
        db: AsyncSession,
        query: ArticleSearchQuery,
        current_user_id: UUID | None = None,
    ) -> dict:
        article, total = await ArticleRepoAsync.search_article(
            db,
            query,
            user_id=current_user_id,
        )

        return {
            "data": [a.model_dump() for a in article],
            "total": total,
            "limit": query.limit,
            "offset": query.offset,
        }

    @staticmethod
    async def get_article_by_slug(db: AsyncSession, slug: str):
        article = await ArticleRepoAsync.detail_article_by_slug(db, slug)
        if not article:
            raise AppError("article not found", code=status.HTTP_404_NOT_FOUND)
        return article

    @staticmethod
    async def get_publish_article_by_slug(db: AsyncSession, slug: str):
        article = await ArticleRepoAsync.detail_publish_article_by_slug(db, slug)
        if not article:
            raise AppError("article not found", code=status.HTTP_404_NOT_FOUND)
        return article

    @staticmethod
    async def get_article_by_id(db: AsyncSession, article_id: str):
        article = await ArticleRepoAsync.detail_article_by_id(db, article_id)
        if not article:
            raise AppError("article not found", code=status.HTTP_404_NOT_FOUND)
        return article

    @staticmethod
    async def create_article(db: AsyncSession, article: ArticleCreated) -> UUID:
        article.id = uuid4()
        repeat = await ArticleRepoAsync.detail_article_by_slug(db, article.slug)
        if repeat:
            raise AppError("slug重复", code=status.HTTP_409_CONFLICT)

        ok = await ArticleRepoAsync.create_article(db, article)
        if not ok:
            raise AppError("新增失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return article.id

    @staticmethod
    async def update_article(db: AsyncSession, article: ArticleUpdate) -> bool:
        repeat = await ArticleRepoAsync.exists_slug_except_id(db, article.slug, article.id)
        if repeat:
            raise AppError("slug重复", code=status.HTTP_409_CONFLICT)

        ok = await ArticleRepoAsync.update_article(db, article)
        if not ok:
            raise AppError("修改失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return True

    @staticmethod
    async def delete_article(db: AsyncSession, article_id: UUID) -> bool:
        article = ArticleDelete(id=article_id, deleted_at=utc_now())
        ok = await ArticleRepoAsync.delete_article(db, article)
        if not ok:
            raise AppError("删除失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    @staticmethod
    async def publish_article(db: AsyncSession, article_id: UUID) -> bool:
        exists_article = await ArticleRepoAsync.is_delete(db, article_id)
        if not exists_article:
            raise AppError("文章未找到", code=status.HTTP_404_NOT_FOUND)

        article = ArticlePublish(id=article_id, published_at=utc_now())
        ok = await ArticleRepoAsync.publish_article(db, article)
        if not ok:
            raise AppError("发布失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    @staticmethod
    async def batch_publish_article(db: AsyncSession, article_ids: list[UUID]) -> bool:
        exists_article = await ArticleRepoAsync.check_array_id_is_delete(db, article_ids)
        if not exists_article:
            raise AppError("文章未找到或已删除", code=status.HTTP_404_NOT_FOUND)

        article = BatchArticlePublish(id=article_ids, published_at=utc_now())
        ok = await ArticleRepoAsync.batch_publish_article(db, article)
        if not ok:
            raise AppError("发布失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    @staticmethod
    async def add_publish_view(db: AsyncSession, article_id: UUID) -> bool:
        ok = await ArticleRepoAsync.add_view(db, str(article_id))
        if not ok:
            raise AppError("新增浏览量失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True

    @staticmethod
    async def replace_article_tags(
        db: AsyncSession,
        article_id: UUID,
        tag_ids: list[UUID],
    ) -> bool:
        # Existence check should be handled in service layer.
        exists = await ArticleRepoAsync.is_delete(db, article_id)
        if not exists:
            return False

        # Keep only existing tags before writing relation rows.
        valid_tag_ids = await ArticleRepoAsync.get_existing_tag_ids(db, tag_ids)
        await ArticleRepoAsync.replace_article_tags(db, article_id, valid_tag_ids)
        return True

    @staticmethod
    async def batch_import_article_tags(
        db: AsyncSession,
        article_ids: list[UUID],
        tag_ids: list[UUID],
    ) -> dict:
        valid_article_ids = await ArticleRepoAsync.get_existing_article_ids(db, article_ids)
        valid_tag_ids = await ArticleRepoAsync.get_existing_tag_ids(db, tag_ids)

        inserted = await ArticleRepoAsync.batch_import_article_tags(
            db,
            valid_article_ids,
            valid_tag_ids,
        )

        expected_pairs = len(valid_article_ids) * len(valid_tag_ids)
        return {
            "inserted": inserted,
            "expected_pairs": expected_pairs,
            "skipped": max(expected_pairs - inserted, 0),
            "valid_article_count": len(valid_article_ids),
            "valid_tag_count": len(valid_tag_ids),
        }
