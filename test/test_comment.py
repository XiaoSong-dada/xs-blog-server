import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from app.main import app


@pytest.mark.anyio
async def test_comment_create_reply_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login", json={"username": "xiaosong", "password": "plmOKN123"}
        )
        assert login.status_code == 200
        token = (login.json().get("data") or {}).get("token")
        assert token

        slug = f"test-comment-{uuid4().hex[:8]}"
        payload = {
            "title": "test comment",
            "slug": slug,
            "content_md": "comment content",
        }
        create_article = await client.post(
            "/api/article",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_article.status_code == 200
        article_id = ((create_article.json().get("data") or {}).get("article_id"))
        assert article_id

        create_comment = await client.post(
            f"/api/article/{article_id}/comments",
            json={"content": "这是主评论"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_comment.status_code == 200
        comment_data = create_comment.json().get("data") or {}
        root_comment_id = comment_data.get("id")
        assert root_comment_id
        assert comment_data.get("parent_id") is None

        reply_comment = await client.post(
            f"/api/article/{article_id}/comments/{root_comment_id}/reply",
            json={"content": "这是回复"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert reply_comment.status_code == 200
        reply_data = reply_comment.json().get("data") or {}
        assert reply_data.get("id")
        assert reply_data.get("parent_id") == root_comment_id
        assert reply_data.get("root_id") == root_comment_id

        list_comments = await client.get(
            f"/api/article/{article_id}/comments",
            params={"limit": 10, "offset": 0},
        )
        assert list_comments.status_code == 200
        data = list_comments.json().get("data") or []
        assert len(data) >= 1

        thread = data[0]
        assert "comment" in thread
        assert "replies" in thread
        assert thread["comment"]["id"] == root_comment_id
        assert any(item.get("id") == reply_data.get("id") for item in thread["replies"])

        cleanup = await client.delete(
            f"/api/article/{article_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cleanup.status_code == 200
