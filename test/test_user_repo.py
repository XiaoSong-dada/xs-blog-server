from app.repositories.user_repo import get_user_by_username

def test_get_user_by_username_not_exists():
    user = get_user_by_username("example_username")
    assert user is None
