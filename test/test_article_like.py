import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from uuid import uuid4


@pytest.mark.anyio
async def test_like_toggle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login", json={"username": "xiaosong", "password": "plmOKN123"}
        )
        assert login.status_code == 200
        token = (login.json().get("data") or {}).get("token")
        assert token

        # create an article
        slug = f"test-like-{uuid4().hex[:8]}"
        payload = {"title": "test like", "slug": slug, "content_md": "content"}
        r = await client.post("/api/article", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json().get("data") or {}
        article_id = data.get("article_id")
        assert article_id

        # like the article (first time -> liked True)
        r = await client.post(f"/api/article/{article_id}/like", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        resp = r.json()
        assert resp.get("data") is not None
        assert resp["data"]["liked"] is True
        assert resp["data"]["like_count"] >= 1

        # like again -> should toggle to unlike
        r2 = await client.post(f"/api/article/{article_id}/like", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200
        resp2 = r2.json()
        assert resp2["data"]["liked"] is False
        assert resp2["data"]["like_count"] >= 0

        # cleanup: delete article
        r3 = await client.delete(f"/api/article/{article_id}", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200
