from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.deps import get_db
from app.schemas.base import ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.comment import CommentCreate, CommentQuery, CommentReplyCreate
from app.schemas.user import UserInDB
from app.security.permissions import require_login
from app.services.comment_service import CommentService

router = APIRouter()


@router.get("/{article_id}/comments", response_model=PaginatedResponse)
async def list_article_comments(
    article_id: str,
    query: CommentQuery = Depends(),
    db: AsyncSession = Depends(get_db),
):
    try:
        items, total = await CommentService.list_article_comments(
            db, article_id=article_id, limit=query.limit, offset=query.offset
        )
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)

    return PaginatedResponse(
        message="ok",
        code=status.HTTP_200_OK,
        data=items,
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.post("/{article_id}/comments", response_model=SuccessResponse)
async def create_article_comment(
    article_id: str,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_login),
):
    try:
        item = await CommentService.create_comment(
            db,
            article_id=article_id,
            user_id=str(_user.user_id),
            content=payload.content,
        )
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)

    return SuccessResponse(message="ok", code=status.HTTP_201_CREATED, data=item)


@router.post("/{article_id}/comments/{comment_id}/reply", response_model=SuccessResponse)
async def reply_article_comment(
    article_id: str,
    comment_id: str,
    payload: CommentReplyCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_login),
):
    try:
        item = await CommentService.reply_comment(
            db,
            article_id=article_id,
            parent_comment_id=comment_id,
            user_id=str(_user.user_id),
            content=payload.content,
            reply_to_user_id=str(payload.reply_to_user_id)
            if payload.reply_to_user_id
            else None,
        )
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)

    return SuccessResponse(message="ok", code=status.HTTP_201_CREATED, data=item)
