from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.friend_link_repo import FriendLinkRepo
from app.schemas.friend_link import (
    FriendLinkListQuery,
    FriendLinkUpdate,
    FriendLinkUpdateRequest,
    FriendLinkCreate,
)
from app.models.friend_link import FriendLink
from typing import Optional
from app.core.exceptions import AppError
from fastapi import status


async def get_friend_links(db: AsyncSession, query: FriendLinkListQuery) -> list:
    if query.name:
        name = query.name.strip()
        if not name:
            name = None
        query.name = name

    items, total = await FriendLinkRepo.list_all(db, query)

    return items, total


async def add_frind_link(db: AsyncSession, payload: FriendLinkCreate) -> bool:
    result = (await FriendLinkRepo.create_one(db, payload=payload),)
    return result


async def get_friend_link_detail(db: AsyncSession, id: str) -> FriendLink:
    if not id or len(id.strip()) == 0:
        raise AppError("传入id不能未空", status.HTTP_422_UNPROCESSABLE_CONTENT)

    result = await FriendLinkRepo.get_one(db, id=id)

    return result


async def delete_friend_link(db: AsyncSession, id: str) -> bool:
    result = await FriendLinkRepo.soft_delete_one(db, id=id)
    if not result:
        raise AppError("未找到要删除的友链", status.HTTP_404_NOT_FOUND)

    return True


async def update_frind_link(db: AsyncSession, payload: FriendLinkUpdateRequest) -> bool:
    is_active = await FriendLinkRepo.get_one(db=db, id=payload.id)

    if not is_active:
        raise AppError("未找到要修改的友链", status.HTTP_404_NOT_FOUND)

    result = await FriendLinkRepo.update_one(db, id=payload.id, payload=payload)

    return result != None


async def get_publish_frind_links(
    db: AsyncSession,
) -> list:

    items, total = await FriendLinkRepo.get_all_list(db)

    return items, total
