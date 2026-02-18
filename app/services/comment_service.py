from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.exceptions import AppError
from app.repositories.article_repo_async import ArticleRepoAsync
from app.repositories.comment_repo import CommentRepo


class CommentService:
    @staticmethod
    def _ensure_uuid(raw_value: str, field_name: str) -> None:
        try:
            UUID(raw_value)
        except ValueError:
            raise AppError(f"{field_name} 格式不正确", status.HTTP_422_UNPROCESSABLE_ENTITY)

    @staticmethod
    async def list_article_comments(
        db: AsyncSession, article_id: str, limit: int = 10, offset: int = 0
    ):
        CommentService._ensure_uuid(article_id, "article_id")
        exists = await ArticleRepoAsync.exists_id(db, article_id)
        if not exists:
            raise AppError("文章不存在", status.HTTP_404_NOT_FOUND)

        items, total = await CommentRepo.list_article_threads(
            db, article_id=article_id, limit=limit, offset=offset
        )
        return items, total

    @staticmethod
    async def create_comment(
        db: AsyncSession, article_id: str, user_id: str, content: str
    ) -> dict:
        CommentService._ensure_uuid(article_id, "article_id")
        CommentService._ensure_uuid(user_id, "user_id")
        exists = await ArticleRepoAsync.exists_id(db, article_id)
        if not exists:
            raise AppError("文章不存在", status.HTTP_404_NOT_FOUND)

        return await CommentRepo.create_root_comment(
            db, article_id=article_id, user_id=user_id, content=content
        )

    @staticmethod
    async def reply_comment(
        db: AsyncSession,
        article_id: str,
        parent_comment_id: str,
        user_id: str,
        content: str,
        reply_to_user_id: str | None = None,
    ) -> dict:
        CommentService._ensure_uuid(article_id, "article_id")
        CommentService._ensure_uuid(parent_comment_id, "comment_id")
        CommentService._ensure_uuid(user_id, "user_id")
        if reply_to_user_id:
            CommentService._ensure_uuid(reply_to_user_id, "reply_to_user_id")

        exists = await ArticleRepoAsync.exists_id(db, article_id)
        if not exists:
            raise AppError("文章不存在", status.HTTP_404_NOT_FOUND)

        parent = await CommentRepo.get_active_comment_by_id(db, parent_comment_id)
        if parent is None:
            raise AppError("父评论不存在", status.HTTP_404_NOT_FOUND)

        if str(parent.article_id) != article_id:
            raise AppError("父评论不属于当前文章", status.HTTP_422_UNPROCESSABLE_ENTITY)

        return await CommentRepo.create_reply_comment(
            db,
            article_id=article_id,
            user_id=user_id,
            parent_id=parent_comment_id,
            root_id=str(parent.root_id),
            content=content,
            reply_to_user_id=reply_to_user_id,
        )
