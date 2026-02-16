from __future__ import annotations

from typing import Tuple, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modals.article_like import ArticleLike


class ArticleLikeRepo:
    @staticmethod
    async def user_liked(db: AsyncSession, user_id: str, article_id: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(ArticleLike)
            .where(
                ArticleLike.article_id == article_id,
                ArticleLike.user_id == user_id,
                ArticleLike.deleted_at.is_(None),
            )
        )
        cnt = await db.scalar(stmt)
        return int(cnt or 0) > 0

    @staticmethod
    async def count_likes(db: AsyncSession, article_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ArticleLike)
            .where(ArticleLike.article_id == article_id, ArticleLike.deleted_at.is_(None))
        )
        cnt = await db.scalar(stmt)
        return int(cnt or 0)

    @staticmethod
    async def toggle_like(db: AsyncSession, user_id: str, article_id: str) -> Tuple[bool, int]:
        """Toggle like status within a transaction/context managed by caller.

        Returns (liked, like_count).
        """
        # 1) 尝试软删除（取消点赞）
        stmt_del = (
            update(ArticleLike)
            .where(
                ArticleLike.article_id == article_id,
                ArticleLike.user_id == user_id,
                ArticleLike.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
            .returning(ArticleLike.id)
        )
        res = await db.execute(stmt_del)
        deleted_row = res.first()
        if deleted_row:
            await db.commit()
            return False, await ArticleLikeRepo.count_likes(db, article_id)

        # 2) 未找到未删除记录，尝试复原已删除记录
        stmt_restore = (
            update(ArticleLike)
            .where(
                ArticleLike.article_id == article_id,
                ArticleLike.user_id == user_id,
                ArticleLike.deleted_at.is_not(None),
            )
            .values(deleted_at=None, created_at=func.now())
            .returning(ArticleLike.id)
        )
        res2 = await db.execute(stmt_restore)
        restored = res2.first()
        if restored:
            await db.commit()
            return True, await ArticleLikeRepo.count_likes(db, article_id)

        # 3) 插入新记录
        obj = ArticleLike(article_id=article_id, user_id=user_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

        return True, await ArticleLikeRepo.count_likes(db, article_id)

    @staticmethod
    async def list_likes_by_user(db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        stmt = (
            select(ArticleLike.id, ArticleLike.article_id, ArticleLike.user_id, ArticleLike.created_at)
            .where(ArticleLike.user_id == user_id, ArticleLike.deleted_at.is_(None))
            .order_by(ArticleLike.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        rows = res.all()
        return [dict(r._mapping) for r in rows]
