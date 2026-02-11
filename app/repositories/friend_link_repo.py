from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modals.friend_link import FriendLink

class FriendLinkRepo:
    @staticmethod
    async def list_all(db: AsyncSession) -> list[FriendLink]:
        stmt = select(FriendLink).order_by(FriendLink.sort_order.asc().nulls_last(), FriendLink.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
