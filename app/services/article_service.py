from app.core.exceptions import AppError
from app.db.transaction import transaction
from app.repositories.article_repo import (
    list_article,
    detail_article_by_slug,
    create_article as create,
)
from app.schemas.article import ArticleQuery, ArticleCreated
from fastapi import status


def get_article_page(search: ArticleQuery | None = None):
    search = search or ArticleQuery()

    with transaction() as conn:
        article, total = list_article(
            conn,
            limit=search.limit,
            offset=search.offset,
            search=search,
        )

    return {
        "data": [a.model_dump() for a in article],
        "total": total,
        "limit": search.limit,
        "offset": search.offset,
    }


def get_article_by_slug(slug: str):
    with transaction() as conn:
        article = detail_article_by_slug(conn, slug)
        if not article:
            raise AppError("article not found", code=status.HTTP_404_NOT_FOUND)

    return article


def create_article(article: ArticleCreated) -> bool:

    with transaction() as conn:
        repeat = detail_article_by_slug(conn, article.slug)
        if repeat:
            raise AppError("slug重复", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        ok = create(conn, article)
        if not ok:
            raise AppError("新增失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return True
