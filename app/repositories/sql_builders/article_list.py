from __future__ import annotations
from typing import Optional
from app.repositories.sql_builders._parts import (
    QueryParts,
    BuiltQuery,
)

from app.schemas.article import ArticleQuery, ArticleSearchQuery


def build_article_list_query(search: Optional[ArticleQuery] = None) -> BuiltQuery:
    base_select = """
    SELECT a.id, a.author_id, COALESCE(u.nick_name, u.username) AS author, a.title, a.slug, a.content_md, a.created_at, 
    a.updated_at, a.published_at ,a.deleted_at, a.view_count,
    COALESCE(
        (
            SELECT json_agg(json_build_object('id', t.id, 'name', t.name, 'slug', t.slug, 'created_at', t.created_at))
            FROM article_tag at
            JOIN tag t ON at.tag_id = t.id
            WHERE at.article_id = a.id
        ),
        '[]'::json
    ) as tags
    FROM article a
    LEFT JOIN users u ON a.author_id = u.user_id
    """
    base_count = "SELECT COUNT(*) FROM article a"

    q = QueryParts()

    if search.published_at == "1":
        q.where_is_not_null("a.published_at")
    elif search.published_at == "0":
        q.where_is_null("a.published_at")

    if search:
        q.where_like("a.slug", search.slug)
        q.where_like("a.title", search.title)
        q.where_like("a.content_md", search.content_md)
        q.where_is_null("a.deleted_at")
        if search.tag_id:
            q.where_custom("EXISTS (SELECT 1 FROM article_tag at WHERE at.article_id = a.id AND at.tag_id = %s)", search.tag_id)

    where = q.where_sql()

    # 注意：分页的 LIMIT/OFFSET 由 fetch_page 统一追加
    data_sql = base_select + where + " ORDER BY a.title"
    count_sql = base_count + where

    return BuiltQuery(data_sql=data_sql, count_sql=count_sql, params=tuple(q.params))


def build_publish_article_list_query(
    search: Optional[ArticleQuery] = None,
) -> BuiltQuery:
    base_select = """
    SELECT a.id, a.author_id, COALESCE(u.nick_name, u.username) AS author, a.title, a.slug, a.content_md, a.created_at, 
    a.updated_at, a.published_at ,a.deleted_at, a.view_count,
    COALESCE(
        (
            SELECT json_agg(json_build_object('id', t.id, 'name', t.name, 'slug', t.slug, 'created_at', t.created_at))
            FROM article_tag at
            JOIN tag t ON at.tag_id = t.id
            WHERE at.article_id = a.id
        ),
        '[]'::json
    ) as tags
    FROM article a
    LEFT JOIN users u ON a.author_id = u.user_id
    """
    base_count = "SELECT COUNT(*) FROM article a"

    q = QueryParts()

    if search:
        q.where_like("a.slug", search.slug)
        q.where_like("a.title", search.title)
        q.where_like("a.content_md", search.content_md)
        q.where_is_null("a.deleted_at")
        q.where_is_not_null("a.published_at")
        if search.tag_id:
            q.where_custom("EXISTS (SELECT 1 FROM article_tag at WHERE at.article_id = a.id AND at.tag_id = %s)", search.tag_id)

    where = q.where_sql()

    # 注意：分页的 LIMIT/OFFSET 由 fetch_page 统一追加
    data_sql = base_select + where + " ORDER BY a.title"
    count_sql = base_count + where

    return BuiltQuery(data_sql=data_sql, count_sql=count_sql, params=tuple(q.params))


def build_search_list_query(search: ArticleSearchQuery) -> BuiltQuery:
    kw = (search.kw or "").strip()

    # 没关键词：你可以选择返回空，或者退化成普通列表（我建议返回空更清晰）
    if not kw:
        data_sql = """
             SELECT a.id, a.author_id, NULL::text AS author, a.slug, a.title, a.published_at, a.view_count,
                 '[]'::json AS tags,
                   0::float AS rank,
                   ''::text AS snippet,
                   false AS hit_title,
                   false AS hit_content
            FROM public.article a
            WHERE 1=0
        """
        count_sql = "SELECT 0"
        return BuiltQuery(data_sql=data_sql, count_sql=count_sql, params=tuple())

    data_sql = """
        WITH q AS (
            SELECT plainto_tsquery('chinese_zh', %s) AS query
        )
        SELECT
            a.id,
            a.author_id,
            COALESCE(u.nick_name, u.username) AS author,
            a.slug,
            a.title,
            a.published_at,
            a.view_count,
            COALESCE(
                (
                    SELECT json_agg(json_build_object('id', t.id, 'name', t.name, 'slug', t.slug, 'created_at', t.created_at))
                    FROM public.article_tag at
                    JOIN public.tag t ON at.tag_id = t.id
                    WHERE at.article_id = a.id
                ),
                '[]'::json
            ) AS tags,
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
        LEFT JOIN public.users u ON a.author_id = u.user_id
        CROSS JOIN q
        WHERE a.deleted_at IS NULL
          AND a.published_at IS NOT NULL
          AND a.search_vector @@ q.query
        ORDER BY rank DESC, a.published_at DESC
    """

    count_sql = """
        WITH q AS (
            SELECT plainto_tsquery('chinese_zh', %s) AS query
        )
        SELECT COUNT(*)
        FROM public.article a
        CROSS JOIN q
        WHERE a.deleted_at IS NULL
          AND a.published_at IS NOT NULL
          AND a.search_vector @@ q.query
    """

    # 注意：kw 要传两次，因为两条 SQL 各用一次
    return BuiltQuery(data_sql=data_sql, count_sql=count_sql, params=(kw,))
