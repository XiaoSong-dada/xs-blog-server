from __future__ import annotations
from typing import Optional
from app.repositories.sql_builders._parts import QueryParts, BuiltQuery
from app.schemas.article import ArticleQuery


def build_article_list_query(search: Optional[ArticleQuery] = None) -> BuiltQuery:
    base_select = """
    SELECT id, author_id, title, slug, content_md, created_at, 
    updated_at, published_at ,deleted_at, view_count  
    FROM article
    """
    base_count = "SELECT COUNT(*) FROM article"

    q = QueryParts()

    if search:
        q.where_like("slug", search.slug)
        q.where_like("title", search.title)
        q.where_like("content_md", search.content_md)
        q.where_is_null("deleted_at")

    where = q.where_sql()

    # 注意：分页的 LIMIT/OFFSET 由 fetch_page 统一追加
    data_sql = base_select + where + " ORDER BY title"
    count_sql = base_count + where

    return BuiltQuery(data_sql=data_sql, count_sql=count_sql, params=tuple(q.params))
