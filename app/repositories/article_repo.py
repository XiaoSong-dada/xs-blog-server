from app.schemas.article import (
    Article,
    ArticleQuery,
    ArticleSearchQuery,
    ArticleSearchOut,
)
from app.repositories.base import fetch_one, fetch_page, fetch_count
from app.repositories.sql_builders.article_list import (
    build_article_list_query,
    build_publish_article_list_query,
    build_search_list_query,
)
import psycopg
from app.repositories.base import execute
from app.schemas.article import (
    Article,
    ArticleCreated,
    ArticleUpdate,
    ArticleDelete,
    ArticlePublish,
    BatchArticlePublish,
    ArticleExportOut,
)
from typing import Optional
from uuid import UUID


def list_article(
    conn: psycopg.Connection,
    limit: int = 10,
    offset: int = 0,
    search: Optional[ArticleQuery] = None,
) -> tuple[list[Article], int]:

    built = build_article_list_query(search)

    rows = fetch_page(conn, built.data_sql, built.params, limit=limit, offset=offset)
    total = fetch_count(conn, built.count_sql, built.params)

    return [Article(**row) for row in rows], total


def list_publish_article(
    conn: psycopg.Connection,
    limit: int = 10,
    offset: int = 0,
    search: Optional[ArticleQuery] = None,
) -> tuple[list[Article], int]:

    built = build_publish_article_list_query(search)

    rows = fetch_page(conn, built.data_sql, built.params, limit=limit, offset=offset)
    total = fetch_count(conn, built.count_sql, built.params)

    return [Article(**row) for row in rows], total


def detail_article_by_slug(conn: psycopg.Connection, slug: str) -> Article:
    sql = """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count  
    FROM article
    WHERE slug = %s
    """
    data = fetch_one(conn, sql, (slug,))
    return Article(**data) if data else None


def detail_publish_article_by_slug(conn: psycopg.Connection, slug: str) -> Article:
    sql = """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count  
    FROM article
    WHERE slug = %s AND published_at IS NOT NUll
    """
    data = fetch_one(conn, sql, (slug,))
    return Article(**data) if data else None


def detail_article_by_id(conn: psycopg.Connection, id: str) -> Article:
    sql = """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count  
    FROM article
    WHERE id = %s
    """
    data = fetch_one(conn, sql, (id,))
    return Article(**data) if data else None


def create_article(conn: psycopg.Connection, article: ArticleCreated) -> bool:
    sql = """
    INSERT INTO article ( id, author_id, title, slug, content_md)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (slug) DO NOTHING
    """
    params = (
        article.id,
        article.author_id,
        article.title,
        article.slug,
        article.content_md,
    )

    affected = execute(conn, sql, params)
    return affected == 1


def update_article(conn: psycopg.Connection, article: ArticleUpdate) -> bool:
    sql = """
        UPDATE article
        SET title = %s, slug = %s, content_md = %s
        WHERE id = %s;
    """
    params = (
        article.title,
        article.slug,
        article.content_md,
        article.id,
    )

    affected = execute(conn, sql, params)
    return affected == 1


def exists_slug_except_id(conn, slug: str, article_id: str) -> bool:
    sql = """
    SELECT 1
    FROM article
    WHERE slug = %s AND id != %s
    LIMIT 1
    """
    return fetch_one(conn, sql, (slug, article_id)) is not None


def exists_id(conn, article_id: str) -> bool:
    sql = """
    SELECT 1
    FROM article
    WHERE id = %s
    LIMIT 1
    """
    return fetch_one(conn, sql, (article_id,)) is not None


def is_delete(conn, article_id: UUID) -> bool:
    sql = """
    SELECT 1
    FROM article
    WHERE id = %s and deleted_at IS NULL
    LIMIT 1
    """
    return fetch_one(conn, sql, (article_id,)) is not None


def check_array_id_is_delete(conn, article_id: list[UUID]) -> bool:
    sql = """
    SELECT 1
    FROM article
    WHERE id = ANY(%s) and deleted_at IS NULL
    LIMIT 1
    """
    return fetch_one(conn, sql, (article_id,)) is not None


def delete_article(conn: psycopg.Connection, article: ArticleDelete) -> bool:
    sql = """
            UPDATE article SET deleted_at = %s WHERE id = %s;
        """
    params = (article.deleted_at, article.id)

    affected = execute(conn, sql, params)
    return affected == 1


def publish_article(conn: psycopg.Connection, article: ArticlePublish) -> bool:
    sql = """
            UPDATE article SET published_at = %s WHERE id = %s;
        """
    params = (article.published_at, article.id)

    affected = execute(conn, sql, params)
    return affected == 1


def batch_publish_article(
    conn: psycopg.Connection, article: BatchArticlePublish
) -> bool:
    sql = """
            UPDATE article SET published_at = %s WHERE id = ANY(%s);
        """
    params = (article.published_at, article.id)

    affected = execute(conn, sql, params)
    return affected == len(article.id)


def add_view(conn: psycopg.Connection, id: str) -> bool:
    sql = """
        UPDATE article
        SET view_count = view_count + 1
        WHERE id = %s
        RETURNING id;
    """
    params = (id,)

    affected = execute(conn, sql, params)
    return affected == 1


def search_article(
    conn: psycopg.Connection, query: ArticleSearchQuery
) -> tuple[list[ArticleSearchOut], int]:

    built = build_search_list_query(query)

    rows = fetch_page(
        conn, built.data_sql, built.params, limit=query.limit, offset=query.offset
    )
    total = fetch_count(conn, built.count_sql, built.params)

    return [ArticleSearchOut(**row) for row in rows], total


def search_article_by_ids(
    conn: psycopg.Connection, article_ids: list[UUID]
) -> list[ArticleExportOut]:

    sql = """
    SELECT id,  title, content_md  
    FROM article
    WHERE id = ANY(%s)
    """
    rows = fetch_page(conn, sql, (article_ids,), limit=len(article_ids), offset=0)

    return [ArticleExportOut(**row) for row in rows]
