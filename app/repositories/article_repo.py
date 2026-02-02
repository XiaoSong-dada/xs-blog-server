from app.schemas.article import Article, ArticleQuery
from app.repositories.base import fetch_one, fetch_page, fetch_count
from app.repositories.sql_builders.article_list import build_article_list_query
import psycopg
from app.repositories.base import execute
from app.schemas.article import Article, ArticleCreated, ArticleUpdate, ArticleDelete
from typing import Optional


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


def detail_article_by_slug(conn: psycopg.Connection, slug: str) -> Article:
    sql = """
    SELECT id, author_id, title, slug, content_md,
    created_at, updated_at, published_at, deleted_at,view_count  
    FROM article
    WHERE slug = %s
    """
    data = fetch_one(conn, sql, (slug,))
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


def delete_article(conn: psycopg.Connection, article: ArticleDelete) -> bool:
    sql = """
            UPDATE article SET deleted_at = %s WHERE id = %s;
        """
    params = (article.deleted_at, article.id)

    affected = execute(conn, sql, params)
    return affected == 1
