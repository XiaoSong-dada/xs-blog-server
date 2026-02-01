import logging
from fastapi import APIRouter, Depends, status
from app.schemas.base import (
    SuccessResponse,
    PaginatedResponse,
    SuccessResponseBase,
    ErrorResponse,
)
from app.schemas.article import ArticleQuery, ArticleCreated
from app.schemas.user import UserInDB
from app.services.article_service import (
    get_article_page,
    get_article_by_slug,
    create_article,
)
from app.security.permissions import require_login

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse)
def list(query: ArticleQuery = Depends()):
    logger.info("query: %s", query)
    article_data = get_article_page(query)
    return PaginatedResponse(message="ok", code=status.HTTP_200_OK, **article_data)


@router.get("/{slug}", response_model=SuccessResponse)
def slug_search(slug: str):
    logger.info("query: %s", slug)
    article = get_article_by_slug(slug)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=article)


@router.post("", response_model=SuccessResponseBase)
def create(acticle: ArticleCreated, _user: UserInDB = Depends(require_login)):
    logger.info("acticle: %s", acticle)
    acticle.author_id = _user.user_id

    ok = create_article(acticle)
    if not ok:
        return ErrorResponse(
            message="新增失败", code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return SuccessResponseBase(message="ok", code=status.HTTP_200_OK)
