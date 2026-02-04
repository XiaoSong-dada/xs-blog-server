import logging
from fastapi import APIRouter, Depends, status
from app.schemas.base import SuccessResponse, PaginatedResponse, SuccessResponseBase
from uuid import UUID
from app.schemas.article import ArticleQuery
from app.services.article_service import (
    get_publish_article_page,
    get_publish_article_by_slug,
    add_publish_view,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse)
def publish_list(query: ArticleQuery = Depends()):
    logger.info("query: %s", query)
    article_data = get_publish_article_page(query)
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
