from app.core.exceptions import AppError
from app.db.transaction import transaction
from app.repositories.article_repo import list_article
from app.schemas.article import ArticleQuery, Article
from app.security.password import get_password_hash


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
