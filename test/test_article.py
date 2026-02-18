from fastapi.testclient import TestClient
from app.main import app
from app.schemas.article import ArticleQuery
import pytest

client = TestClient(app)


def test_get_article_list():
    payload = ArticleQuery(title=None, slug=None, content_md=None).model_dump(
        exclude_none=True
    )
    r = client.get("/api/article", params=payload)
    assert r.status_code == 200
    body = r.json()
    items = body.get("data") or []
    if items:
        assert "comment_count" in items[0]


def test_get_article_detail_by_slug_db_not_has():
    r = client.get("/api/article/a")
    assert r.status_code == 404


def test_get_article_detail_by_slug_db_has():
    r = client.get("/api/article/test-title")
    assert r.status_code == 200


def test_publish_search_list_ok():
    r = client.get("/api/publish/search/list", params={"query": "容", "limit": 10, "offset": 0})
    assert r.status_code == 200


@pytest.fixture(scope="module")
def user_token_and_username():
    r = client.post(
        "/api/auth/login", json={"username": "xiaosong", "password": "1234"}
    )
    assert r.status_code == 200
    data = r.json().get("data") or {}
    token = data.get("token")
    assert token
    return token
