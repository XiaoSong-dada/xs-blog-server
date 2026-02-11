from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.friend_link_repo import FriendLinkRepo
from app.schemas.friend_link import FriendLinkListQuery
from typing import Optional
async def get_friend_links(db: AsyncSession , query: FriendLinkListQuery) -> list:
    if query.name:
        name = query.name.strip()
        if not name:
            name = None
        query.name = name

    items , total = await FriendLinkRepo.list_all(db, query)
    
    return items , total
