from app.schemas.user import UserInDB, UserListQuery
from app.repositories.base import fetch_one, fetch_page, fetch_count
from app.repositories.sql_builders.user_list import build_user_list_query
import psycopg
from app.repositories.base import execute
from uuid import UUID


# 获取用户
def get_user_by_username(conn: psycopg.Connection, username: str) -> UserInDB | None:
    sql = """
    SELECT user_id, username, password, status, is_admin, avatar_url, email, nick_name
    FROM users
    WHERE username = %s
    """
    data = fetch_one(conn, sql, (username,))
    return UserInDB(**data) if data else None


# 获取用户通过id
def get_user_by_id(conn: psycopg.Connection, user_id: str) -> UserInDB | None:
    sql = """
    SELECT user_id, username, password, status, is_admin, avatar_url, email, nick_name
    FROM users
    WHERE user_id = %s
    """
    data = fetch_one(conn, sql, (user_id,))
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


def delete_by_username(conn: psycopg.Connection, username: str) -> bool:
    """
    删除用户
    返回值语义（标准）：
    - True  = 删除成功
    - False = 用户不存在导致未删除（业务可预期失败）
    - 其他 DB/SQL 异常：抛出（系统失败）
    """
    select_sql = """
    SELECT user_id FROM users WHERE username = %s
    """
    user = fetch_one(conn, select_sql, (username,))
    if not user:
        return False

    sql = """
    DELETE FROM users
    WHERE user_id = %s
    """
    affected = execute(conn, sql, (user["user_id"],))
    return affected == 1


def list_users(
    conn: psycopg.Connection,
    limit: int = 10,
    offset: int = 0,
    search: UserListQuery | None = None,
) -> tuple[list[UserInDB], int]:

    built = build_user_list_query(search)

    rows = fetch_page(conn, built.data_sql, built.params, limit=limit, offset=offset)
    total = fetch_count(conn, built.count_sql, built.params)

    return [UserInDB(**row) for row in rows], total


def update_user(conn: psycopg.Connection, user_id: UUID, changes: dict) -> bool:
    allowed_fields = {"email", "nick_name", "avatar_url"}
    updates = {k: v for k, v in changes.items() if k in allowed_fields}

    if not updates:
        return True

    set_clause = ", ".join([f"{field} = %s" for field in updates.keys()])
    sql = f"""
    UPDATE users
    SET {set_clause}
    WHERE user_id = %s
    """
    params = tuple(updates.values()) + (user_id,)
    affected = execute(conn, sql, params)
    return affected == 1


def update_user_password_rope(conn: psycopg.Connection, user: UserInDB) -> bool:
    sql = """
    UPDATE users  SET password = %s WHERE user_id = %s
    """
    params = (
        user.password,
        user.user_id,
    )
    affected = execute(conn, sql, params)
    return affected == 1

def check_email_exists(conn: psycopg.Connection, email: str) -> bool:
    sql = """
    SELECT user_id FROM users WHERE email = %s
    LIMIT 1
    """
    user = fetch_one(conn, sql, (email,))
    return user is not None