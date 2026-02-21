import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport

from app.main import app


async def _admin_auth_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/auth/login", json={"username": "xiaosong", "password": "plmOKN123"}
    )
    assert login.status_code == 200
    token = (login.json().get("data") or {}).get("token")
    assert token
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_create_tag():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _admin_auth_headers(client)
        suffix = uuid4().hex[:8]
        response = await client.post(
            "/api/tag",
            headers=headers,
            json={"name": f"Python-{suffix}", "slug": f"python-{suffix}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"].startswith("Python-")
        assert data["slug"].startswith("python-")
        assert "id" in data


@pytest.mark.anyio
async def test_get_all_tags():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _admin_auth_headers(client)
        suffix = uuid4().hex[:8]
        await client.post(
            "/api/tag",
            headers=headers,
            json={"name": f"Java-{suffix}", "slug": f"java-{suffix}"},
        )

        response = await client.get("/api/tag")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 1
        assert any(str(t["name"]).startswith("Java-") for t in data)


@pytest.mark.anyio
async def test_update_tag():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _admin_auth_headers(client)
        suffix = uuid4().hex[:8]
        create_resp = await client.post(
            "/api/tag",
            headers=headers,
            json={"name": f"Go-{suffix}", "slug": f"go-{suffix}"},
        )
        assert create_resp.status_code == 200
        tag_id = create_resp.json()["data"]["id"]

        response = await client.put(
            f"/api/tag/{tag_id}",
            headers=headers,
            json={"name": f"Golang-{suffix}", "slug": f"golang-{suffix}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == f"Golang-{suffix}"
        assert data["slug"] == f"golang-{suffix}"


@pytest.mark.anyio
async def test_delete_tag():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _admin_auth_headers(client)
        suffix = uuid4().hex[:8]
        create_resp = await client.post(
            "/api/tag",
            headers=headers,
            json={"name": f"Rust-{suffix}", "slug": f"rust-{suffix}"},
        )
        assert create_resp.status_code == 200
        tag_id = create_resp.json()["data"]["id"]

        response = await client.delete(f"/api/tag/{tag_id}", headers=headers)
        assert response.status_code == 200

        verify_resp = await client.get(f"/api/tag/{tag_id}")
        assert verify_resp.status_code == 200
        assert verify_resp.json().get("code") == 404
