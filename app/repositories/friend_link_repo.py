from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.modals.friend_link import FriendLink
from typing import Optional
from sqlalchemy import bindparam
from app.schemas.friend_link import (
    FriendLinkListQuery,
    FriendLinkUpdate,
    FriendLinkCreate,
)


class FriendLinkRepo:
    @staticmethod
    async def list_all(
        db: AsyncSession,
        query: Optional[FriendLinkListQuery] = None,
    ) -> list[FriendLink]:

        conditions = [FriendLink.is_active.is_(True)]
        if query and query.name:
            conditions.append(FriendLink.name.ilike(f"%{query.name}%"))

        total_stmt = select(func.count()).select_from(FriendLink).where(*conditions)
        total = await db.scalar(total_stmt)
        total = int(total or 0)

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

        return items, total

    @staticmethod
    async def create_one(
        db: AsyncSession,
        payload: FriendLinkCreate,
    ) -> FriendLink:

        obj = FriendLink(
            name=payload.name,
            url=str(payload.url),
            description=payload.description,
            sort_order=payload.sort_order or 0,
            is_active=True,
        )

        # 3️⃣ 入库
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

        return obj


    @staticmethod
    async def get_one(
        db: AsyncSession,
        id: str,
        *,
        active_only: bool = True,
    ) -> Optional[FriendLink]:
        conditions = [FriendLink.id == id]

        if active_only:
            conditions.append(FriendLink.is_active.is_(True))

        stmt = select(FriendLink).where(*conditions).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()
    

    @staticmethod
    async def hard_delete_one(
        db: AsyncSession,
        id: str,
    ) -> bool:
        obj = await FriendLinkRepo.get_one(db, id, active_only=False)
        if not obj:
            return False

        await db.delete(obj)
        await db.commit()
        return True
    
    @staticmethod
    async def check_one(
        db: AsyncSession,
        id: str,
        payload: FriendLinkUpdate,
    ) -> Optional[FriendLink]:
        
        return 

    @staticmethod
    async def update_one(
        db: AsyncSession,
        id: str,
        payload: FriendLinkUpdate,
    ) -> Optional[FriendLink]:
        obj = await FriendLinkRepo.get_one(db, id, active_only=False)
        if not obj:
            return None

        data = payload.model_dump(exclude_unset=True)

        # 允许更新的字段白名单（防止把 id/is_active 等乱改）
        allowed = {"name", "url", "description", "sort_order"}
        for k, v in data.items():
            if k in allowed:
                setattr(obj, k, v)

        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def soft_delete_one(
        db: AsyncSession,
        id: str,
    ) -> bool:
        obj = await FriendLinkRepo.get_one(db, id, active_only=False)
        if not obj:
            return False

        # 已经被删过也算成功（幂等）
        if obj.is_active is False:
            return True

        obj.is_active = False
        await db.commit()
        return True
