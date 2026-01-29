from fastapi.testclient import TestClient
from app.main import app
from app.schemas.article import ArticleQuery

client = TestClient(app)


def test_get_article_list():
    payload = ArticleQuery(title=None, slug=None, content_md=None).model_dump(exclude_none=True)
    r = client.get("/api/article", params=payload)
    assert r.status_code == 200
