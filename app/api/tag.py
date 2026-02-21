import logging
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.deps import get_db
from app.schemas.base import SuccessResponse, SuccessResponseBase, ErrorResponse
from app.schemas.tag import TagCreate, TagUpdate
from app.schemas.user import UserInDB
from app.security.permissions import require_admin
from app.services.tag_service import TagService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=SuccessResponse)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_admin),
):
    try:
        tag = await TagService.create_tag(db, tag_in)
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)
    return SuccessResponse(message="ok", code=status.HTTP_201_CREATED, data=tag)


@router.get("", response_model=SuccessResponse)
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    tags = await TagService.get_all_tags(db)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=tags)


@router.get("/hot", response_model=SuccessResponse)
async def get_hot_tags(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    tags = await TagService.get_tags_with_count(db, limit)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=tags)


@router.get("/{tag_id}", response_model=SuccessResponse)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        tag = await TagService.get_tag(db, tag_id)
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=tag)


@router.put("/{tag_id}", response_model=SuccessResponse)
async def update_tag(
    tag_id: UUID,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_admin),
):
    try:
        tag = await TagService.update_tag(db, tag_id, tag_in)
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)
    return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=tag)


@router.delete("/{tag_id}", response_model=SuccessResponseBase)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_admin),
):
    try:
        await TagService.delete_tag(db, tag_id)
    except AppError as e:
        return ErrorResponse(message=e.message, code=e.code)
    return SuccessResponseBase(message="ok", code=status.HTTP_200_OK)
