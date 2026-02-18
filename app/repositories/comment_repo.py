from __future__ import annotations

from typing import Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.user import User


class CommentRepo:
    @staticmethod
    async def _get_comment_with_user(db: AsyncSession, comment_id: UUID) -> dict | None:
        stmt = (
            select(Comment, User.username, User.nick_name, User.avatar_url)
            .join(User, User.user_id == Comment.user_id)
            .where(Comment.id == comment_id, Comment.deleted_at.is_(None))
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row:
            return None

        comment = row[0]
        return {
            "id": comment.id,
            "article_id": comment.article_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "parent_id": comment.parent_id,
            "root_id": comment.root_id,
            "reply_to_user_id": comment.reply_to_user_id,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "username": row[1],
            "nick_name": row[2],
            "avatar_url": row[3],
        }

    @staticmethod
    async def get_active_comment_by_id(
        db: AsyncSession, comment_id: str
    ) -> Comment | None:
        comment_uuid = UUID(comment_id)
        stmt = (
            select(Comment)
            .where(Comment.id == comment_uuid, Comment.deleted_at.is_(None))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_root_comment(
        db: AsyncSession, article_id: str, user_id: str, content: str
    ) -> dict:
        comment_id = uuid4()
        obj = Comment(
            id=comment_id,
            article_id=UUID(article_id),
            user_id=UUID(user_id),
            content=content,
            parent_id=None,
            root_id=comment_id,
            reply_to_user_id=None,
        )
        db.add(obj)
        await db.commit()
        item = await CommentRepo._get_comment_with_user(db, obj.id)
        return item or {
            "id": obj.id,
            "article_id": obj.article_id,
            "user_id": obj.user_id,
            "content": obj.content,
            "parent_id": obj.parent_id,
            "root_id": obj.root_id,
            "reply_to_user_id": obj.reply_to_user_id,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "username": None,
            "nick_name": None,
            "avatar_url": None,
        }

    @staticmethod
    async def create_reply_comment(
        db: AsyncSession,
        article_id: str,
        user_id: str,
        parent_id: str,
        root_id: str,
        content: str,
        reply_to_user_id: str | None,
    ) -> dict:
        obj = Comment(
            article_id=UUID(article_id),
            user_id=UUID(user_id),
            content=content,
            parent_id=UUID(parent_id),
            root_id=UUID(root_id),
            reply_to_user_id=UUID(reply_to_user_id) if reply_to_user_id else None,
        )
        db.add(obj)
        await db.commit()
        item = await CommentRepo._get_comment_with_user(db, obj.id)
        return item or {
            "id": obj.id,
            "article_id": obj.article_id,
            "user_id": obj.user_id,
            "content": obj.content,
            "parent_id": obj.parent_id,
            "root_id": obj.root_id,
            "reply_to_user_id": obj.reply_to_user_id,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "username": None,
            "nick_name": None,
            "avatar_url": None,
        }

    @staticmethod
    async def list_article_threads(
        db: AsyncSession, article_id: str, limit: int = 10, offset: int = 0
    ) -> Tuple[list[dict], int]:
        article_uuid = UUID(article_id)
        base_conditions = [
            Comment.article_id == article_uuid,
            Comment.deleted_at.is_(None),
            Comment.parent_id.is_(None),
        ]

        total_stmt = select(func.count()).select_from(Comment).where(*base_conditions)
        total = await db.scalar(total_stmt)
        total = int(total or 0)

        top_stmt = (
            select(Comment, User.username, User.nick_name, User.avatar_url)
            .join(User, User.user_id == Comment.user_id)
            .where(*base_conditions)
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        top_res = await db.execute(top_stmt)
        top_rows = top_res.all()

        if not top_rows:
            return [], total

        root_ids = [item[0].id for item in top_rows]

        replies_stmt = (
            select(Comment, User.username, User.nick_name, User.avatar_url)
            .join(User, User.user_id == Comment.user_id)
            .where(
                Comment.article_id == article_uuid,
                Comment.deleted_at.is_(None),
                Comment.root_id.in_(root_ids),
                Comment.parent_id.is_not(None),
            )
            .order_by(Comment.created_at.asc())
        )
        replies_res = await db.execute(replies_stmt)
        replies = replies_res.all()

        replies_by_root: dict[UUID, list[dict]] = {}
        for row in replies:
            comment = row[0]
            replies_by_root.setdefault(comment.root_id, []).append(
                {
                    "id": comment.id,
                    "article_id": comment.article_id,
                    "user_id": comment.user_id,
                    "content": comment.content,
                    "parent_id": comment.parent_id,
                    "root_id": comment.root_id,
                    "reply_to_user_id": comment.reply_to_user_id,
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                    "username": row[1],
                    "nick_name": row[2],
                    "avatar_url": row[3],
                }
            )

        items: list[dict] = []
        for row in top_rows:
            comment = row[0]
            items.append(
                {
                    "comment": {
                        "id": comment.id,
                        "article_id": comment.article_id,
                        "user_id": comment.user_id,
                        "content": comment.content,
                        "parent_id": comment.parent_id,
                        "root_id": comment.root_id,
                        "reply_to_user_id": comment.reply_to_user_id,
                        "created_at": comment.created_at,
                        "updated_at": comment.updated_at,
                        "username": row[1],
                        "nick_name": row[2],
                        "avatar_url": row[3],
                    },
                    "replies": replies_by_root.get(comment.id, []),
                }
            )

        return items, total
