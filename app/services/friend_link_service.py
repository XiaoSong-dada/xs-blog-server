from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.friend_link_repo import FriendLinkRepo

async def get_friend_links(db: AsyncSession):
    items = await FriendLinkRepo.list_all(db)
    return items or []
