from fastapi import Depends, APIRouter, Query, status
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.repositories.friend_link_repo import FriendLinkRepo
from app.schemas.friend_link import (
    FriendLinkOut,
    FriendLinkListQuery,
    FriendLinkUpdateRequest,
    FriendLinkCreate
)
from app.services.friend_link_service import (
    get_friend_links,
    get_friend_link_detail,
    update_frind_link,
    delete_friend_link,
    add_frind_link,
)
from app.schemas.base import (
    SuccessResponse,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponseBase,
)
from app.security.permissions import require_login, require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def list_links(
    q: FriendLinkListQuery = Depends(),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_friend_links(db, query=q)

    if not items:
        return ErrorResponse(message="暂无友链", code=404)

    data = [FriendLinkOut.model_validate(x) for x in items]
    return PaginatedResponse(
        message="获取友链成功",
        code=200,
        data=data,
        limit=q.limit,
        offset=q.offset,
        total=total,
    )


@router.get("/{id}")
async def detail_links(
    id: str, db: AsyncSession = Depends(get_db), _user=Depends(require_admin)
):
    if not id or len(id.strip()) == 0:
        return ErrorResponse(
            message="未传入id", code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )

    item = await get_friend_link_detail(db, id=id)

    if not item:
        return ErrorResponse(message="未找到相关链接", code=404)

    data = FriendLinkOut.model_validate(item)


    return SuccessResponse(
        message="获取友链成功",
        code=200,
        data=data,
    )

@router.post("")
async def create_link(
    params: FriendLinkCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
):

    item = await add_frind_link(db, params)

    if not item:
        return ErrorResponse(message="新增失败", code=404)

    return SuccessResponseBase(
        message="新增友链成功",
        code=status.HTTP_201_CREATED,
    )



@router.put("")
async def update_links(
    params: FriendLinkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
):
    if not params.id:
        return ErrorResponse(
            message="未传入id", code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )

    item = await update_frind_link(db, payload=params)

    if not item:
        return ErrorResponse(message="未找到相关链接", code=404)

    return SuccessResponseBase(
        message="修改友链成功",
        code=200,
    )


@router.delete("/{id}")
async def delete_link(
    id: str, db: AsyncSession = Depends(get_db), _user=Depends(require_admin)
):
    logger.info('这是传入的id：%s' , id)
    
    if not id:
        return ErrorResponse(
            message="未传入id", code=status.HTTP_421_MISDIRECTED_REQUEST
        )

    await delete_friend_link(db, id=id)

    return SuccessResponseBase(
        message="删除友链成功",
        code=200,
    )
