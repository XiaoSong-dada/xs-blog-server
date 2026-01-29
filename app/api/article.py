from fastapi import APIRouter, Depends
import logging

from app.schemas.base import SuccessResponse, PaginatedResponse
from app.schemas.article import ArticleQuery
from app.services.article_service import get_article_page, get_article_by_slug

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse)
def list(query: ArticleQuery = Depends()):
    logger.info("query: %s", query)
    article_data = get_article_page(query)
    return PaginatedResponse(message="ok", code=200, **article_data)


@router.get("/{slug}", response_model=SuccessResponse)
def slug_search(slug: str):
    logger.info("query: %s", slug)
    article = get_article_by_slug(slug)
    return SuccessResponse(message="ok", code=200, data=article)
