from fastapi.testclient import TestClient
from app.main import app
from app.utils.verification import is_null_or_empty
from app.schemas.user import UserCreate
from uuid import uuid4
import pytest

client = TestClient(app)

username = f"user_{uuid4().hex[:8]}"
def test_register():
    payload = UserCreate(username=username, password="123456").model_dump()
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201

admin_username = f"admin_{uuid4().hex[:8]}"
def test_register_admin():
    payload = UserCreate(username=admin_username, password="123456").model_dump()
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201


@pytest.fixture(scope="module")
def admin_token():
    r = client.post("/api/auth/login", json={"username": "xiaosong", "password": "1234"})
    assert r.status_code == 200
    data = r.json().get("data") or {}
    token = data.get("token")
    assert token
    return token

@pytest.fixture(scope="module")
def user_token_and_username():
    r = client.post("/api/auth/login", json={"username": username, "password": "123456"})
    assert r.status_code == 200
    data = r.json().get("data") or {}
    token = data.get("token")
    assert token
    return token, username


def test_delete_user_not_login():
    r = client.delete(
        f"/api/users/delete/{username}",
        headers={"Authorization": "Bearer invalid"},
    )
    assert r.status_code == 401


def test_delete_user_is_login_not_admin(user_token_and_username):
    user_token, target_username = user_token_and_username
    r = client.delete(
        f"/api/users/delete/{target_username}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 403

def test_delete_user_is_admin(admin_token):
    
    r = client.delete(
        f"/api/users/delete/{username}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200

    r = client.delete(
        f"/api/users/delete/{admin_username}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert r.status_code == 200

def test_is_null_or_empty():
    assert is_null_or_empty(None)
    assert is_null_or_empty("")
    assert not is_null_or_empty("abc")
