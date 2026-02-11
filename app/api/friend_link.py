from fastapi import Depends, APIRouter, Query
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.repositories.friend_link_repo import FriendLinkRepo
from app.schemas.friend_link import FriendLinkOut, FriendLinkListQuery
from app.services.friend_link_service import get_friend_links
from app.schemas.base import SuccessResponse, PaginatedResponse, ErrorResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def list_links(
    q: FriendLinkListQuery = Depends(),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_friend_links(db, query=q)

    if not items:
        return ErrorResponse(message="暂无友链", code=200)

    data = [FriendLinkOut.model_validate(x) for x in items]
    return PaginatedResponse(
        message="获取友链成功",
        code=200,
        data=data,
        limit=q.limit,
        offset=q.offset,
        total=total,
    )
