from app.core.exceptions import AppError
from app.db.transaction import transaction
from uuid import UUID, uuid4
from app.repositories.article_repo import (
    list_article,
    detail_article_by_id,
    detail_article_by_slug,
    detail_publish_article_by_slug,
    list_publish_article,
    create_article as create,
    update_article as update,
    exists_slug_except_id,
    delete_article as delete,
    is_delete,
    publish_article as publish,
    add_view,
)
from app.schemas.article import (
    ArticleQuery,
    ArticleCreated,
    ArticleUpdate,
    ArticleDelete,
    ArticlePublish,
)
from fastapi import status
from app.utils.datetime_utils import utc_now


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


def get_publish_article_page(search: ArticleQuery | None = None):
    search = search or ArticleQuery()

    with transaction() as conn:
        article, total = list_publish_article(
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


def get_publish_article_by_slug(slug: str):
    with transaction() as conn:
        article = detail_publish_article_by_slug(conn, slug)
        if not article:
            raise AppError("article not found", code=status.HTTP_404_NOT_FOUND)

    return article


def get_article_by_id(id: str):
    with transaction() as conn:
        article = detail_article_by_id(conn, id)
        if not article:
            raise AppError("article not found", code=status.HTTP_404_NOT_FOUND)

    return article


def create_article(article: ArticleCreated) -> str:

    with transaction() as conn:
        article.id = uuid4()
        repeat = detail_article_by_slug(conn, article.slug)
        if repeat:
            raise AppError("slug重复", code=status.HTTP_409_CONFLICT)

        ok = create(conn, article)
        if not ok:
            raise AppError("新增失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return article.id


def update_article(article: ArticleUpdate) -> bool:
    with transaction() as conn:
        # slug 修改查重
        repeat = exists_slug_except_id(conn, article.slug, article.id)
        if repeat:
            raise AppError("slug重复", code=status.HTTP_409_CONFLICT)

        ok = update(conn, article)
        if not ok:
            raise AppError("修改失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return True


def delete_acticle(id: UUID) -> bool:

    with transaction() as conn:
        article = ArticleDelete(id=id, deleted_at=utc_now())

        ok = delete(conn, article)
        if not ok:
            raise AppError("删除失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return True


def publish_acticle(id: UUID) -> bool:

    with transaction() as conn:
        exists_article = is_delete(conn, id)
        if not exists_article:
            raise AppError("文章未找到", code=status.HTTP_404_NOT_FOUND)

        article = ArticlePublish(
            id=id,
            published_at=utc_now(),
        )

        ok = publish(conn, article)
        if not ok:
            raise AppError("发布失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return True


def add_publish_view(id: UUID) -> bool:
    with transaction() as conn:
        ok = add_view(conn, id)
    if not ok:
        raise AppError("新增浏览量失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return True
