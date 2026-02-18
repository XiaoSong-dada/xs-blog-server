from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update, text, exists, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article as ArticleModel
from app.models.article_like import ArticleLike
from app.models.article_bookmark import ArticleBookmark
from app.models.comment import Comment
from app.schemas.article import (
    Article,
    ArticleQuery,
    ArticleSearchQuery,
    ArticleSearchOut,
    ArticleCreated,
    ArticleUpdate,
    ArticleDelete,
    ArticlePublish,
    BatchArticlePublish,
    ArticleExportOut,
)


class ArticleRepoAsync:
    @staticmethod
    async def list_article(
        db: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        search: Optional[ArticleQuery] = None,
        user_id: Optional[UUID] = None,
    ) -> tuple[list[Article], int]:
        conditions = []
        if search:
            if search.slug:
                conditions.append(ArticleModel.slug.ilike(f"%{search.slug}%"))
            if search.title:
                conditions.append(ArticleModel.title.ilike(f"%{search.title}%"))
            if search.content_md:
                conditions.append(ArticleModel.content_md.ilike(f"%{search.content_md}%"))
            if search.published_at == "1":
                conditions.append(ArticleModel.published_at.is_not(None))
            elif search.published_at == "0":
                conditions.append(ArticleModel.published_at.is_(None))

        conditions.append(ArticleModel.deleted_at.is_(None))

        total_stmt = select(func.count()).select_from(ArticleModel).where(*conditions)
        total = await db.scalar(total_stmt)
        total = int(total or 0)

        like_count_subquery = (
            select(func.count())
            .select_from(ArticleLike)
            .where(
                ArticleLike.article_id == ArticleModel.id,
                ArticleLike.deleted_at.is_(None),
            )
            .correlate(ArticleModel)
            .scalar_subquery()
        )

        bookmark_count_subquery = (
            select(func.count())
            .select_from(ArticleBookmark)
            .where(
                ArticleBookmark.article_id == ArticleModel.id,
                ArticleBookmark.deleted_at.is_(None),
            )
            .correlate(ArticleModel)
            .scalar_subquery()
        )

        comment_count_subquery = (
            select(func.count())
            .select_from(Comment)
            .where(
                Comment.article_id == ArticleModel.id,
                Comment.deleted_at.is_(None),
            )
            .correlate(ArticleModel)
            .scalar_subquery()
        )

        liked_expr = literal(False)
        bookmarked_expr = literal(False)
        if user_id is not None:
            liked_expr = exists(
                select(1)
                .select_from(ArticleLike)
                .where(
                    ArticleLike.article_id == ArticleModel.id,
                    ArticleLike.user_id == user_id,
                    ArticleLike.deleted_at.is_(None),
                )
            )
            bookmarked_expr = exists(
                select(1)
                .select_from(ArticleBookmark)
                .where(
                    ArticleBookmark.article_id == ArticleModel.id,
                    ArticleBookmark.user_id == user_id,
                    ArticleBookmark.deleted_at.is_(None),
                )
            )

        items_stmt = (
            select(
                ArticleModel.id,
                ArticleModel.author_id,
                ArticleModel.title,
                ArticleModel.slug,
                ArticleModel.content_md,
                ArticleModel.view_count,
                func.coalesce(like_count_subquery, 0).label("like_count"),
                liked_expr.label("liked"),
                func.coalesce(bookmark_count_subquery, 0).label("bookmark_count"),
                bookmarked_expr.label("bookmarked"),
                func.coalesce(comment_count_subquery, 0).label("comment_count"),
                ArticleModel.created_at,
                ArticleModel.updated_at,
                ArticleModel.published_at,
                ArticleModel.deleted_at,
            )
            .where(*conditions)
            .order_by(ArticleModel.title.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(items_stmt)
        items = result.all()

        return [Article(**dict(r._mapping)) for r in items], total

    @staticmethod
    async def list_publish_article(
        db: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        search: Optional[ArticleQuery] = None,
        user_id: Optional[UUID] = None,
    ) -> tuple[list[Article], int]:
        conditions = [ArticleModel.deleted_at.is_(None), ArticleModel.published_at.is_not(None)]
        if search:
            if search.slug:
                conditions.append(ArticleModel.slug.ilike(f"%{search.slug}%"))
            if search.title:
                conditions.append(ArticleModel.title.ilike(f"%{search.title}%"))
            if search.content_md:
                conditions.append(ArticleModel.content_md.ilike(f"%{search.content_md}%"))

        total_stmt = select(func.count()).select_from(ArticleModel).where(*conditions)
        total = await db.scalar(total_stmt)
        total = int(total or 0)

        like_count_subquery = (
            select(func.count())
            .select_from(ArticleLike)
            .where(
                ArticleLike.article_id == ArticleModel.id,
                ArticleLike.deleted_at.is_(None),
            )
            .correlate(ArticleModel)
            .scalar_subquery()
        )

        bookmark_count_subquery = (
            select(func.count())
            .select_from(ArticleBookmark)
            .where(
                ArticleBookmark.article_id == ArticleModel.id,
                ArticleBookmark.deleted_at.is_(None),
            )
            .correlate(ArticleModel)
            .scalar_subquery()
        )

        comment_count_subquery = (
            select(func.count())
            .select_from(Comment)
            .where(
                Comment.article_id == ArticleModel.id,
                Comment.deleted_at.is_(None),
            )
            .correlate(ArticleModel)
            .scalar_subquery()
        )

        liked_expr = literal(False)
        bookmarked_expr = literal(False)
        if user_id is not None:
            liked_expr = exists(
                select(1)
                .select_from(ArticleLike)
                .where(
                    ArticleLike.article_id == ArticleModel.id,
                    ArticleLike.user_id == user_id,
                    ArticleLike.deleted_at.is_(None),
                )
            )
            bookmarked_expr = exists(
                select(1)
                .select_from(ArticleBookmark)
                .where(
                    ArticleBookmark.article_id == ArticleModel.id,
                    ArticleBookmark.user_id == user_id,
                    ArticleBookmark.deleted_at.is_(None),
                )
            )

        items_stmt = (
            select(
                ArticleModel.id,
                ArticleModel.author_id,
                ArticleModel.title,
                ArticleModel.slug,
                ArticleModel.content_md,
                ArticleModel.view_count,
                func.coalesce(like_count_subquery, 0).label("like_count"),
                liked_expr.label("liked"),
                func.coalesce(bookmark_count_subquery, 0).label("bookmark_count"),
                bookmarked_expr.label("bookmarked"),
                func.coalesce(comment_count_subquery, 0).label("comment_count"),
                ArticleModel.created_at,
                ArticleModel.updated_at,
                ArticleModel.published_at,
                ArticleModel.deleted_at,
            )
            .where(*conditions)
            .order_by(ArticleModel.title.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(items_stmt)
        items = result.all()

        return [Article(**dict(r._mapping)) for r in items], total

    @staticmethod
    async def detail_article_by_slug(db: AsyncSession, slug: str) -> Optional[Article]:
        stmt = select(ArticleModel).where(ArticleModel.slug == slug).limit(1)
        result = await db.execute(stmt)
        item = result.scalars().first()
        return Article.model_validate(item) if item else None

    @staticmethod
    async def detail_publish_article_by_slug(db: AsyncSession, slug: str) -> Optional[Article]:
        stmt = (
            select(ArticleModel)
            .where(
                ArticleModel.slug == slug,
                ArticleModel.published_at.is_not(None),
                ArticleModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        item = result.scalars().first()
        return Article.model_validate(item) if item else None

    @staticmethod
    async def detail_article_by_id(db: AsyncSession, id: str) -> Optional[Article]:
        stmt = select(ArticleModel).where(ArticleModel.id == id).limit(1)
        result = await db.execute(stmt)
        item = result.scalars().first()
        return Article.model_validate(item) if item else None

    @staticmethod
    async def create_article(db: AsyncSession, article: ArticleCreated) -> bool:
        repeat_stmt = select(ArticleModel.id).where(ArticleModel.slug == article.slug).limit(1)
        repeat = await db.scalar(repeat_stmt)
        if repeat:
            return False

        obj = ArticleModel(
            id=article.id,
            author_id=article.author_id,
            title=article.title,
            slug=article.slug,
            content_md=article.content_md,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return True

    @staticmethod
    async def update_article(db: AsyncSession, article: ArticleUpdate) -> bool:
        stmt = (
            update(ArticleModel)
            .where(ArticleModel.id == article.id)
            .values(
                title=article.title,
                slug=article.slug,
                content_md=article.content_md,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount == 1

    @staticmethod
    async def exists_slug_except_id(db: AsyncSession, slug: str, article_id: str) -> bool:
        stmt = (
            select(ArticleModel.id)
            .where(ArticleModel.slug == slug, ArticleModel.id != article_id)
            .limit(1)
        )
        row = await db.scalar(stmt)
        return row is not None

    @staticmethod
    async def exists_id(db: AsyncSession, article_id: str) -> bool:
        stmt = select(ArticleModel.id).where(ArticleModel.id == article_id).limit(1)
        row = await db.scalar(stmt)
        return row is not None

    @staticmethod
    async def is_delete(db: AsyncSession, article_id: UUID) -> bool:
        stmt = (
            select(ArticleModel.id)
            .where(ArticleModel.id == article_id, ArticleModel.deleted_at.is_(None))
            .limit(1)
        )
        row = await db.scalar(stmt)
        return row is not None

    @staticmethod
    async def check_array_id_is_delete(db: AsyncSession, article_id: list[UUID]) -> bool:
        stmt = (
            select(ArticleModel.id)
            .where(ArticleModel.id.in_(article_id), ArticleModel.deleted_at.is_(None))
            .limit(1)
        )
        row = await db.scalar(stmt)
        return row is not None

    @staticmethod
    async def delete_article(db: AsyncSession, article: ArticleDelete) -> bool:
        stmt = (
            update(ArticleModel)
            .where(ArticleModel.id == article.id)
            .values(deleted_at=article.deleted_at)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount == 1

    @staticmethod
    async def publish_article(db: AsyncSession, article: ArticlePublish) -> bool:
        stmt = (
            update(ArticleModel)
            .where(ArticleModel.id == article.id)
            .values(published_at=article.published_at)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount == 1

    @staticmethod
    async def batch_publish_article(db: AsyncSession, article: BatchArticlePublish) -> bool:
        stmt = (
            update(ArticleModel)
            .where(ArticleModel.id.in_(article.id))
            .values(published_at=article.published_at)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount == len(article.id)

    @staticmethod
    async def add_view(db: AsyncSession, id: str) -> bool:
        stmt = (
            update(ArticleModel)
            .where(ArticleModel.id == id)
            .values(view_count=ArticleModel.view_count + 1)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount == 1

    @staticmethod
    async def search_article(
        db: AsyncSession, query: ArticleSearchQuery, user_id: Optional[UUID] = None
    ) -> tuple[list[ArticleSearchOut], int]:
        kw = (query.kw or "").strip()
        if not kw:
            return [], 0

        data_stmt = text(
            """
            WITH q AS (
                SELECT plainto_tsquery('chinese_zh', :kw) AS query
            )
            SELECT
                a.id,
                a.slug,
                a.title,
                a.published_at,
                a.view_count,
                COALESCE((
                    SELECT COUNT(*) FROM public.article_like al
                    WHERE al.article_id = a.id AND al.deleted_at IS NULL
                ), 0) AS like_count,
                COALESCE((
                    SELECT COUNT(*) FROM public.article_bookmark ab
                    WHERE ab.article_id = a.id AND ab.deleted_at IS NULL
                ), 0) AS bookmark_count,
                COALESCE((
                    SELECT COUNT(*) FROM public.comment c
                    WHERE c.article_id = a.id AND c.deleted_at IS NULL
                ), 0) AS comment_count,
                CASE
                    WHEN CAST(:user_id AS uuid) IS NULL THEN FALSE
                    ELSE EXISTS (
                        SELECT 1
                        FROM public.article_like al2
                        WHERE al2.article_id = a.id
                          AND al2.user_id = CAST(:user_id AS uuid)
                          AND al2.deleted_at IS NULL
                    )
                END AS liked,
                CASE
                    WHEN CAST(:user_id AS uuid) IS NULL THEN FALSE
                    ELSE EXISTS (
                        SELECT 1
                        FROM public.article_bookmark ab2
                        WHERE ab2.article_id = a.id
                          AND ab2.user_id = CAST(:user_id AS uuid)
                          AND ab2.deleted_at IS NULL
                    )
                END AS bookmarked,
                ts_rank_cd(a.search_vector, q.query) AS rank,
                ts_headline(
                    'chinese_zh',
                    coalesce(a.content_md,''),
                    q.query,
                    'MaxWords=30, MinWords=10, StartSel=[[[, StopSel=]]]'
                ) AS snippet,
                (to_tsvector('chinese_zh', coalesce(a.title,'')) @@ q.query) AS hit_title,
                (to_tsvector('chinese_zh', coalesce(a.content_md,'')) @@ q.query) AS hit_content
            FROM public.article a
            CROSS JOIN q
            WHERE a.deleted_at IS NULL
              AND a.published_at IS NOT NULL
              AND a.search_vector @@ q.query
            ORDER BY rank DESC, a.published_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        count_stmt = text(
            """
            WITH q AS (
                SELECT plainto_tsquery('chinese_zh', :kw) AS query
            )
            SELECT COUNT(*) AS total
            FROM public.article a
            CROSS JOIN q
            WHERE a.deleted_at IS NULL
              AND a.published_at IS NOT NULL
              AND a.search_vector @@ q.query
            """
        )

        rows = await db.execute(
            data_stmt,
            {
                "kw": kw,
                "limit": query.limit,
                "offset": query.offset,
                "user_id": str(user_id) if user_id is not None else None,
            },
        )
        items = [ArticleSearchOut(**dict(r._mapping)) for r in rows.fetchall()]

        total_row = await db.execute(count_stmt, {"kw": kw})
        total = int(total_row.scalar() or 0)
        return items, total

    @staticmethod
    async def search_article_by_ids(
        db: AsyncSession, article_ids: list[UUID]
    ) -> list[ArticleExportOut]:
        stmt = (
            select(ArticleModel.id, ArticleModel.title, ArticleModel.content_md)
            .where(ArticleModel.id.in_(article_ids))
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [ArticleExportOut(**dict(r._mapping)) for r in rows]
