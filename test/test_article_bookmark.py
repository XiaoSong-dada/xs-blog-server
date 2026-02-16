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


@pytest.mark.anyio
async def test_bookmark_fields_in_article_publish_and_search_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login", json={"username": "xiaosong", "password": "plmOKN123"}
        )
        assert login.status_code == 200
        token = (login.json().get("data") or {}).get("token")
        assert token

        unique_kw = f"bookmarkkw{uuid4().hex[:8]}"
        slug = f"test-bookmark-fields-{uuid4().hex[:8]}"
        payload = {
            "title": f"title-{unique_kw}",
            "slug": slug,
            "content_md": f"content-{unique_kw}",
        }

        create_resp = await client.post(
            "/api/article",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        article_id = ((create_resp.json().get("data") or {}).get("article_id"))
        assert article_id

        publish_resp = await client.post(
            f"/api/article/{article_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert publish_resp.status_code == 200

        bookmark_resp = await client.post(
            f"/api/article/{article_id}/bookmark",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert bookmark_resp.status_code == 200

        article_list_resp = await client.get(
            "/api/article",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert article_list_resp.status_code == 200
        article_items = (article_list_resp.json().get("data") or [])
        target_article = next((it for it in article_items if it.get("id") == article_id), None)
        assert target_article is not None
        assert "bookmark_count" in target_article
        assert "bookmarked" in target_article

        publish_list_resp = await client.get(
            "/api/publish",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert publish_list_resp.status_code == 200
        publish_items = (publish_list_resp.json().get("data") or [])
        target_publish = next((it for it in publish_items if it.get("id") == article_id), None)
        assert target_publish is not None
        assert "bookmark_count" in target_publish
        assert "bookmarked" in target_publish

        search_resp = await client.get(
            "/api/publish/search/list",
            params={"kw": unique_kw, "limit": 20, "offset": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200
        search_items = (search_resp.json().get("data") or [])
        if search_items:
            target_search = next((it for it in search_items if it.get("id") == article_id), None)
            if target_search is not None:
                assert "bookmark_count" in target_search
                assert "bookmarked" in target_search

        cleanup_resp = await client.delete(
            f"/api/article/{article_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cleanup_resp.status_code == 200
