from app.schemas.user import UserInDB
from app.db.query import fetch_one

# 获取用户
def get_user_by_username(username: str) -> UserInDB | None:
    user_data = fetch_one("SELECT user_id, username, password, status, is_admin, avatar_url, email, nick_name FROM users WHERE username = %s", (username,))
    if user_data:
        return UserInDB(
            user_id=user_data['user_id'],
            username=user_data['username'],
            password=user_data['password'],
            status=user_data['status'],
            is_admin=user_data['is_admin'],
            avatar_url=user_data['avatar_url'],
            email=user_data['email'],
            nick_name=user_data['nick_name'],
        )
    return None