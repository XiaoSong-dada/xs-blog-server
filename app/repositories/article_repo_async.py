from __future__ import annotations

from typing import Optional, Tuple, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.schemas.article import (
    Article,
    ArticleCreated,
    ArticleUpdate,
    ArticleDelete,
    ArticlePublish,
    BatchArticlePublish,
    ArticleSearchQuery,
    ArticleSearchOut,
    ArticleExportOut,
)
from app.repositories.sql_builders.article_list import (
    build_article_list_query,
    build_publish_article_list_query,
    build_search_list_query,
)


async def _fetch_one_as_dict(db: AsyncSession, sql: str, params: Optional[dict] = None) -> Optional[dict]:
    res = await db.execute(text(sql), params or {})
    row = res.fetchone()
    return dict(row._mapping) if row else None


async def _fetch_all_as_dict(db: AsyncSession, sql: str, params: Optional[dict] = None) -> List[dict]:
    res = await db.execute(text(sql), params or {})
    rows = res.fetchall()
    return [dict(r._mapping) for r in rows] if rows else []


class ArticleRepoAsync:
    @staticmethod
    async def list_article(
        db: AsyncSession, limit: int = 10, offset: int = 0, search: Optional[ArticleSearchQuery] = None
    ) -> Tuple[List[Article], int]:
        built = build_article_list_query(search)

        data_sql = f"{built.data_sql} LIMIT :limit OFFSET :offset"
        params = {**(built.params or {}), "limit": limit, "offset": offset}

        rows = await _fetch_all_as_dict(db, data_sql, params)
        count_sql = built.count_sql
        total_row = await _fetch_one_as_dict(db, count_sql, built.params)
        total = int(total_row.get("count", 0)) if total_row else 0

        return [Article(**r) for r in rows], total

    @staticmethod
    async def list_publish_article(
        db: AsyncSession, limit: int = 10, offset: int = 0, search: Optional[ArticleSearchQuery] = None
    ) -> Tuple[List[Article], int]:
        built = build_publish_article_list_query(search)

        data_sql = f"{built.data_sql} LIMIT :limit OFFSET :offset"
        params = {**(built.params or {}), "limit": limit, "offset": offset}

        rows = await _fetch_all_as_dict(db, data_sql, params)
        count_sql = built.count_sql
        total_row = await _fetch_one_as_dict(db, count_sql, built.params)
        total = int(total_row.get("count", 0)) if total_row else 0

        return [Article(**r) for r in rows], total

    @staticmethod
    async def detail_article_by_slug(db: AsyncSession, slug: str) -> Optional[Article]:
        sql = text(
            """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count
    FROM article
    WHERE slug = :slug
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"slug": slug})
        return Article(**row) if row else None

    @staticmethod
    async def detail_publish_article_by_slug(db: AsyncSession, slug: str) -> Optional[Article]:
        sql = text(
            """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count
    FROM article
    WHERE slug = :slug AND published_at IS NOT NULL
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"slug": slug})
        return Article(**row) if row else None

    @staticmethod
    async def detail_article_by_id(db: AsyncSession, id: str) -> Optional[Article]:
        sql = text(
            """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count
    FROM article
    WHERE id = :id
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"id": id})
        return Article(**row) if row else None

    @staticmethod
    async def create_article(db: AsyncSession, article: ArticleCreated) -> Optional[str]:
        sql = text(
            """
    INSERT INTO article ( id, author_id, title, slug, content_md)
    VALUES (:id, :author_id, :title, :slug, :content_md)
    ON CONFLICT (slug) DO NOTHING
    RETURNING id
    """
        )
        params = {
            "id": article.id,
            "author_id": article.author_id,
            "title": article.title,
            "slug": article.slug,
            "content_md": article.content_md,
        }
        res = await db.execute(sql, params)
        row = res.fetchone()
        if not row:
            return None
        await db.commit()
        return str(row[0])

    @staticmethod
    async def update_article(db: AsyncSession, article: ArticleUpdate) -> bool:
        sql = text(
            """
        UPDATE article
        SET title = :title, slug = :slug, content_md = :content_md
        WHERE id = :id;
    """
        )
        params = {
            "title": article.title,
            "slug": article.slug,
            "content_md": article.content_md,
            "id": article.id,
        }
        res = await db.execute(sql, params)
        await db.commit()
        return res.rowcount == 1

    @staticmethod
    async def exists_slug_except_id(db: AsyncSession, slug: str, article_id: str) -> bool:
        sql = text(
            """
    SELECT 1
    FROM article
    WHERE slug = :slug AND id != :id
    LIMIT 1
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"slug": slug, "id": article_id})
        return row is not None

    @staticmethod
    async def exists_id(db: AsyncSession, article_id: str) -> bool:
        sql = text(
            """
    SELECT 1
    FROM article
    WHERE id = :id
    LIMIT 1
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"id": article_id})
        return row is not None

    @staticmethod
    async def is_delete(db: AsyncSession, article_id: UUID) -> bool:
        sql = text(
            """
    SELECT 1
    FROM article
    WHERE id = :id and deleted_at IS NULL
    LIMIT 1
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"id": article_id})
        return row is not None

    @staticmethod
    async def check_array_id_is_delete(db: AsyncSession, article_ids: list[UUID]) -> bool:
        sql = text(
            """
    SELECT 1
    FROM article
    WHERE id = ANY(:ids) and deleted_at IS NULL
    LIMIT 1
    """
        )
        row = await _fetch_one_as_dict(db, sql.text, {"ids": article_ids})
        return row is not None

    @staticmethod
    async def delete_article(db: AsyncSession, article: ArticleDelete) -> bool:
        sql = text("""
            UPDATE article SET deleted_at = :deleted_at WHERE id = :id;
        """)
        params = {"deleted_at": article.deleted_at, "id": article.id}
        res = await db.execute(sql, params)
        await db.commit()
        return res.rowcount == 1

    @staticmethod
    async def publish_article(db: AsyncSession, article: ArticlePublish) -> bool:
        sql = text("""
            UPDATE article SET published_at = :published_at WHERE id = :id;
        """)
        params = {"published_at": article.published_at, "id": article.id}
        res = await db.execute(sql, params)
        await db.commit()
        return res.rowcount == 1

    @staticmethod
    async def batch_publish_article(db: AsyncSession, article: BatchArticlePublish) -> bool:
        sql = text("""
            UPDATE article SET published_at = :published_at WHERE id = ANY(:ids);
        """)
        params = {"published_at": article.published_at, "ids": article.id}
        res = await db.execute(sql, params)
        await db.commit()
        return res.rowcount == len(article.id)

    @staticmethod
    async def add_view(db: AsyncSession, id: str) -> bool:
        sql = text("""
        UPDATE article
        SET view_count = view_count + 1
        WHERE id = :id
        RETURNING id;
    """)
        res = await db.execute(sql, {"id": id})
        await db.commit()
        return res.rowcount == 1

    @staticmethod
    async def search_article(db: AsyncSession, query: ArticleSearchQuery) -> Tuple[List[ArticleSearchOut], int]:
        built = build_search_list_query(query)

        data_sql = f"{built.data_sql} LIMIT :limit OFFSET :offset"
        params = {**(built.params or {}), "limit": query.limit, "offset": query.offset}

        rows = await _fetch_all_as_dict(db, data_sql, params)
        total_row = await _fetch_one_as_dict(db, built.count_sql, built.params)
        total = int(total_row.get("count", 0)) if total_row else 0

        return [ArticleSearchOut(**r) for r in rows], total

    @staticmethod
    async def search_article_by_ids(db: AsyncSession, article_ids: list[UUID]) -> List[ArticleExportOut]:
        sql = text(
            """
    SELECT id,  title, content_md  
    FROM article
    WHERE id = ANY(:ids)
    """
        )
        rows = await _fetch_all_as_dict(db, sql.text, {"ids": article_ids})
        return [ArticleExportOut(**r) for r in rows]
