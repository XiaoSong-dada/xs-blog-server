from app.schemas.user import UserInDB
from app.repositories.base import fetch_one
import psycopg
from app.repositories.base import execute


# 获取用户
def get_user_by_username(conn: psycopg.Connection, username: str) -> UserInDB | None:
    sql = """
    SELECT user_id, username, password, status, is_admin, avatar_url, email, nick_name
    FROM users
    WHERE username = %s
    """
    data = fetch_one(conn, sql, (username,))
    return UserInDB(**data) if data else None

# 创建用户
def create_user(conn: psycopg.Connection, user: UserInDB) -> bool:
    """
    返回值语义（标准）：
    - True  = 插入成功
    - False = username 冲突导致未插入（业务可预期失败）
    - 其他 DB/SQL 异常：抛出（系统失败）
    """
    sql = """
    INSERT INTO users (user_id, username, password, status, is_admin, avatar_url, email, nick_name)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (username) DO NOTHING
    """
    params = (
        user.user_id,
        user.username,
        user.password,
        user.status,
        user.is_admin,
        user.avatar_url,
        user.email,
        user.nick_name,
    )

    affected = execute(conn, sql, params)
    return affected == 1