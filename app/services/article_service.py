from app.core.exceptions import AppError
from app.db.transaction import transaction
from app.repositories.article_repo import list_article, detail_article_by_slug
from app.schemas.article import ArticleQuery


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
            raise AppError("article not found", code=404)

    return article
