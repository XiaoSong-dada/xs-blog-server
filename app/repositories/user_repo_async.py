from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepoAsync:
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        stmt = select(User).where(User.username == username).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_username_active(db: AsyncSession, username: str) -> User | None:
        stmt = (
            select(User)
            .where(User.username == username, User.status != "0")
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalars().first()
