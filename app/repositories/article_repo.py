from app.schemas.article import Article, ArticleQuery
from app.repositories.base import fetch_one, fetch_page, fetch_count
from app.repositories.sql_builders.article_list import build_article_list_query
import psycopg
from app.repositories.base import execute
from app.schemas.article import Article
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
