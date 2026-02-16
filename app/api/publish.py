import logging
from fastapi import APIRouter, Depends, status
from app.schemas.base import SuccessResponse, PaginatedResponse, SuccessResponseBase
from uuid import UUID
from app.schemas.article import ArticleQuery, ArticleSearchQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.schemas.user import UserInDB
from app.security.permissions import require_login_optional
from app.services.article_service import (
    get_publish_article_page,
    get_publish_article_by_slug,
    add_publish_view,
    search_publish_article,
    ArticleService,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse)
async def publish_list(
    query: ArticleQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    _user: UserInDB | None = Depends(require_login_optional),
):
    logger.info("query: %s", query)
    current_user_id = _user.user_id if _user else None
    article_data = await ArticleService.get_publish_article_page(
        db,
        query,
        current_user_id=current_user_id,
    )
    return PaginatedResponse(message="ok", code=status.HTTP_200_OK, **article_data)


# 允许获取已发布文章
@router.get("/{slug}", response_model=SuccessResponse)
def slug_search(slug: str):
    logger.info("query: %s", slug)
    article = get_publish_article_by_slug(slug)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=article)


# 增加浏览量
@router.post("/{id}/view", response_model=SuccessResponse)
def add_view(id: UUID):
    logger.info("query: %s", id)
    article = add_publish_view(id)
    return SuccessResponseBase(message="ok", code=status.HTTP_201_CREATED)


@router.get("/search/list", response_model=PaginatedResponse)
async def publish_search_list(
    query: ArticleSearchQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    _user: UserInDB | None = Depends(require_login_optional),
):
    logger.info("query: %s", query)
    current_user_id = _user.user_id if _user else None
    article_data = await ArticleService.search_publish_article(
        db,
        query,
        current_user_id=current_user_id,
    )

    logger.info("list query : %s", article_data)

    return PaginatedResponse(message="ok", code=status.HTTP_200_OK, **article_data)
