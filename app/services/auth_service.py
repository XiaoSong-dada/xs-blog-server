from app.db.read_connection import read_connection
from app.repositories.user_repo import get_user_by_username
from app.security.password import verify_password
from app.security.jwt import create_jwt
from app.schemas.user import UserOut

def authenticate_user(username: str, password: str) -> str | None:
    with read_connection() as conn:
        user = get_user_by_username(conn, username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None

    # 这里不需要持有 DB 连接了（尽快释放连接）
    user_out = UserOut(**user.model_dump())
    return create_jwt(user_out.model_dump())
