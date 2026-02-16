from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.article_like_repo import ArticleLikeRepo
from app.repositories.article_repo_async import ArticleRepoAsync


class ArticleLikeService:
    @staticmethod
    async def toggle_like(db: AsyncSession, user_id: str, article_id: str) -> Tuple[bool, int]:
        """切换文章点赞状态：
        - 验证文章存在
        - 调用仓库完成 toggle（软删除/恢复/插入）
        返回 (liked, like_count)
        """
        # 验证文章存在且未被删除
        ok = await ArticleRepoAsync.exists_id(db, article_id)
        if not ok:
            raise ValueError("article not found")

        liked, count = await ArticleLikeRepo.toggle_like(db, user_id, article_id)
        return liked, count
