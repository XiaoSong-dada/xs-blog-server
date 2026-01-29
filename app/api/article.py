from fastapi import APIRouter, Depends
import logging

from app.security.permissions import require_admin
from app.schemas.base import SuccessResponse, PaginatedResponse
from app.schemas.article import Article, ArticleQuery
from app.services.article_service import get_article_page

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse)
def list(query: ArticleQuery = Depends()):
    logger.info("query: %s", query)
    article_data = get_article_page(query)
    return PaginatedResponse(message="ok", code=200, **article_data)
