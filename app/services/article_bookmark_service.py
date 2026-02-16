from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.article_bookmark_repo import ArticleBookmarkRepo
from app.repositories.article_repo_async import ArticleRepoAsync
from app.core.exceptions import AppError
from fastapi import status


class ArticleBookmarkService:
    @staticmethod
    async def toggle_bookmark(db: AsyncSession, user_id: str, article_id: str) -> tuple[bool, int]:
        # 验证文章存在且未删除
        exists = await ArticleRepoAsync.exists_id(db, article_id)
        if not exists:
            raise AppError("文章不存在", status.HTTP_404_NOT_FOUND)

        bookmarked, count = await ArticleBookmarkRepo.toggle_bookmark(db, user_id=user_id, article_id=article_id)
        return bookmarked, count

    @staticmethod
    async def list_user_bookmarks(db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0):
        items = await ArticleBookmarkRepo.list_bookmarks_by_user(db, user_id=user_id, limit=limit, offset=offset)
        return items
