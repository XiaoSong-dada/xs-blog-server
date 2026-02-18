from __future__ import annotations

from typing import List, Tuple
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_bookmark import ArticleBookmark
from app.models.article import Article


class ArticleBookmarkRepo:
    @staticmethod
    async def user_bookmarked(db: AsyncSession, user_id: str, article_id: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(ArticleBookmark)
            .where(
                ArticleBookmark.article_id == article_id,
                ArticleBookmark.user_id == user_id,
                ArticleBookmark.deleted_at.is_(None),
            )
        )
        cnt = await db.scalar(stmt)
        return int(cnt or 0) > 0

    @staticmethod
    async def count_bookmarks(db: AsyncSession, article_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ArticleBookmark)
            .where(
                ArticleBookmark.article_id == article_id,
                ArticleBookmark.deleted_at.is_(None),
            )
        )
        cnt = await db.scalar(stmt)
        return int(cnt or 0)

    @staticmethod
    async def toggle_bookmark(db: AsyncSession, user_id: str, article_id: str) -> Tuple[bool, int]:
        """Toggle bookmark status within a transaction/context managed by caller.

        Returns (bookmarked, bookmark_count).
        """
        # 1) 尝试软删除（取消收藏）
        stmt_del = (
            update(ArticleBookmark)
            .where(
                ArticleBookmark.article_id == article_id,
                ArticleBookmark.user_id == user_id,
                ArticleBookmark.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
            .returning(ArticleBookmark.id)
        )
        res = await db.execute(stmt_del)
        deleted_row = res.first()
        if deleted_row:
            await db.commit()
            return False, await ArticleBookmarkRepo.count_bookmarks(db, article_id)

        # 2) 未找到未删除记录，尝试复原已删除记录
        stmt_restore = (
            update(ArticleBookmark)
            .where(
                ArticleBookmark.article_id == article_id,
                ArticleBookmark.user_id == user_id,
                ArticleBookmark.deleted_at.is_not(None),
            )
            .values(deleted_at=None, created_at=func.now())
            .returning(ArticleBookmark.id)
        )
        res2 = await db.execute(stmt_restore)
        restored = res2.first()
        if restored:
            await db.commit()
            return True, await ArticleBookmarkRepo.count_bookmarks(db, article_id)

        # 3) 插入新记录
        obj = ArticleBookmark(article_id=article_id, user_id=user_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

        return True, await ArticleBookmarkRepo.count_bookmarks(db, article_id)

    @staticmethod
    async def list_bookmarks_by_user(
        db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[dict], int]:
        # join with Article to return article fields (title, slug, content_md)
        conditions = [
            ArticleBookmark.deleted_at.is_(None),
            ArticleBookmark.user_id == user_id,
            Article.deleted_at.is_(None),
        ]

        total_stmt = (
            select(func.count()).select_from(ArticleBookmark).join(Article, Article.id == ArticleBookmark.article_id).where(*conditions)
        )
        total = await db.scalar(total_stmt)
        total = int(total or 0)

        stmt = (
            select(
                ArticleBookmark.id,
                ArticleBookmark.article_id,
                ArticleBookmark.user_id,
                ArticleBookmark.created_at,
                Article.title,
                Article.slug,
                Article.content_md,
            )
            .select_from(ArticleBookmark)
            .join(Article, Article.id == ArticleBookmark.article_id)
            .where(
                ArticleBookmark.user_id == user_id,
                ArticleBookmark.deleted_at.is_(None),
                Article.deleted_at.is_(None),
            )
            .order_by(ArticleBookmark.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        rows = res.all()
        return [dict(r._mapping) for r in rows], total
