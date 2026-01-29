from app.schemas.article import Article, ArticleQuery
from app.repositories.base import fetch_one, fetch_page, fetch_count
from app.repositories.sql_builders.article_list import build_article_list_query
import psycopg
from app.repositories.base import execute
from app.schemas.article import Article
from typing import Optional


def get_detail_article_by_slug(
    conn: psycopg.Connection, limit: int = 10, offset: int = 0, slug: str = ""
) -> Article:

    return Article


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
