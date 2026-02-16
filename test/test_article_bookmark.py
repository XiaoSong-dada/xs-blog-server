import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from uuid import uuid4


@pytest.mark.anyio
async def test_bookmark_toggle_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # login
        login = await client.post(
            "/api/auth/login", json={"username": "xiaosong", "password": "plmOKN123"}
        )
        assert login.status_code == 200
        token = (login.json().get("data") or {}).get("token")
        assert token

        # create an article
        slug = f"test-bookmark-{uuid4().hex[:8]}"
        payload = {"title": "test bookmark", "slug": slug, "content_md": "content"}
        r = await client.post("/api/article", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json().get("data") or {}
        article_id = data.get("article_id")
        assert article_id

        # bookmark the article (first time -> bookmarked True)
        r = await client.post(f"/api/article/{article_id}/bookmark", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        resp = r.json()
        assert resp.get("data") is not None
        assert resp["data"]["bookmarked"] is True
        assert resp["data"]["bookmark_count"] >= 1

        # list bookmarks -> should contain this article
        rlist = await client.get("/api/article/bookmarks/list", headers={"Authorization": f"Bearer {token}"})
        assert rlist.status_code == 200
        list_data = rlist.json().get("data") or []
        assert any(item.get("article_id") == article_id for item in list_data)

        # toggle again -> should unbookmarked
        r2 = await client.post(f"/api/article/{article_id}/bookmark", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200
        resp2 = r2.json()
        assert resp2["data"]["bookmarked"] is False

        # cleanup: delete article
        r3 = await client.delete(f"/api/article/{article_id}", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200
