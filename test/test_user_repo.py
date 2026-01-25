from fastapi.testclient import TestClient
from app.main import app
from app.utils.verification import is_null_or_empty
from app.schemas.user import UserCreate
from uuid import uuid4

client = TestClient(app)

def test_login():
    r = client.post("/api/auth/login", json={"username":"admin","password":"123456"})
    assert r.status_code == 200

def test_register():
    username = f"admin_{uuid4().hex[:8]}"
    payload = UserCreate(username=username, password="123456").model_dump()
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201


def test_is_null_or_empty():
    assert is_null_or_empty(None)
    assert is_null_or_empty("")
    assert not is_null_or_empty("abc")
