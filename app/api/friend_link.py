from fastapi import Depends, APIRouter
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.repositories.friend_link_repo import FriendLinkRepo
from app.schemas.friend_link import FriendLinkOut
from app.schemas.base import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def list_links(db: AsyncSession = Depends(get_db)):
    items = await FriendLinkRepo.list_all(db)
    data = [FriendLinkOut.model_validate(x) for x in items]
    return SuccessResponse(message="获取友链成功", code=200, data=data)
