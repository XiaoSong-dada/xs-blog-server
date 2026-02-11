from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.modals.friend_link import FriendLink
from typing import Optional
from sqlalchemy import bindparam
from app.schemas.friend_link import FriendLinkListQuery

class FriendLinkRepo:
    @staticmethod
    async def list_all(
        db: AsyncSession,
        query: Optional[FriendLinkListQuery] = None,
    ) -> list[FriendLink]:

        # 1) 构造公共过滤条件
        conditions = [FriendLink.is_active.is_(True)]
        if query and query.name:
            conditions.append(FriendLink.name.ilike(f"%{query.name}%"))

        # 2) 查询 total（不带分页）
        total_stmt = select(func.count()).select_from(FriendLink).where(*conditions)
        total = await db.scalar(total_stmt)
        total = int(total or 0)

        # 3) 查询 items（带分页 + 排序）
        items_stmt = (
            select(FriendLink)
            .where(*conditions)
            .order_by(
                FriendLink.sort_order.asc().nulls_last(),
                FriendLink.created_at.desc(),
            )
            .limit(query.limit if query.limit else 10)
            .offset(query.offset if query.offset else 0)
        )
        result = await db.execute(items_stmt)
        items = result.scalars().all()

        return items , total
