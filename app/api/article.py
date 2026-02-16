import logging
from fastapi import APIRouter, Depends, status
from app.schemas.base import (
    SuccessResponse,
    PaginatedResponse,
    SuccessResponseBase,
    ErrorResponse,
)
from uuid import UUID
from app.schemas.article import ArticleQuery, ArticleCreated, ArticleUpdate
from app.schemas.user import UserInDB
from app.services.article_service import (
    get_article_page,
    get_article_by_slug,
    create_article,
    update_article,
    delete_acticle,
    publish_acticle,
    get_article_by_id,
    batch_publish_acticle,
)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.security.permissions import require_login
from app.services.article_like_service import ArticleLikeService
from app.security.permissions import require_admin
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse)
def list_article(query: ArticleQuery = Depends()):
    logger.info("query: %s", query)
    article_data = get_article_page(query)
    return PaginatedResponse(message="ok", code=status.HTTP_200_OK, **article_data)


@router.get("/{slug}", response_model=SuccessResponse)
def slug_search(slug: str, _user: UserInDB = Depends(require_admin)):
    logger.info("query: %s", slug)
    article = get_article_by_slug(slug)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=article)


@router.get("/id/{id}", response_model=SuccessResponse)
def slug_search_id(id: str, _user: UserInDB = Depends(require_admin)):
    logger.info("query: %s", id)
    article = get_article_by_id(id)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=article)


@router.post("", response_model=SuccessResponse)
def create(acticle: ArticleCreated, _user: UserInDB = Depends(require_admin)):
    logger.info("acticle: %s", acticle)
    acticle.author_id = _user.user_id

    article_id = create_article(acticle)
    if not article_id:
        return ErrorResponse(
            message="新增失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return SuccessResponse(
        message="ok", code=status.HTTP_201_CREATED, data=dict(article_id=article_id)
    )


@router.put("", response_model=SuccessResponseBase)
def update(acticle: ArticleUpdate, _user: UserInDB = Depends(require_admin)):
    logger.info("acticle: %s", acticle)

    ok = update_article(acticle)
    if not ok:
        return ErrorResponse(
            message="修改失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return SuccessResponseBase(message="ok", code=status.HTTP_200_OK)


@router.delete("/{id}", response_model=SuccessResponseBase)
def delete(id: UUID, _user: UserInDB = Depends(require_admin)):
    logger.info("acticle_id: %s", id)

    ok = delete_acticle(id)
    if not ok:
        return ErrorResponse(
            message="删除失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return SuccessResponseBase(message="ok", code=status.HTTP_200_OK)


@router.post("/{id}", response_model=SuccessResponseBase)
def publish(id: UUID, _user: UserInDB = Depends(require_admin)):
    logger.info("publish acticle_id: %s", id)

    ok = publish_acticle(id)
    if not ok:
        return ErrorResponse(
            message="发布失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return SuccessResponseBase(message="ok", code=status.HTTP_200_OK)


@router.post("/batch/publish", response_model=SuccessResponseBase)
def batch_publish(id_array: list[str], _user: UserInDB = Depends(require_admin)):
    logger.info("batch publish acticle_id: %s", id_array)
    id_array
    if len(id_array) == 0:
        return ErrorResponse(
            message="批量发布数组不能为空", code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )

    ok = batch_publish_acticle(id_array)
    if not ok:
        return ErrorResponse(
            message="发布失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return SuccessResponseBase(message="ok", code=status.HTTP_200_OK)


@router.post("/{article_id}/like", response_model=SuccessResponse)
async def like_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_login),
):
    try:
        liked, count = await ArticleLikeService.toggle_like(db, _user.user_id, article_id)
    except ValueError:
        return ErrorResponse(message="文章不存在", code=status.HTTP_404_NOT_FOUND)

    return SuccessResponse(
        message="ok",
        code=status.HTTP_200_OK,
        data={"liked": liked, "like_count": count},
    )
