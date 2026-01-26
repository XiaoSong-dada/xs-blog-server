from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.repositories.sql_builders._parts import QueryParts
from app.schemas.user import UserListQuery


@dataclass(frozen=True)
class BuiltQuery:
    data_sql: str
    count_sql: str
    params: tuple[Any, ...]


def build_user_list_query(search: UserListQuery | None = None) -> BuiltQuery:
    base_select = """
    SELECT user_id, username, password, status, is_admin, avatar_url, email, nick_name
    FROM users
    """
    base_count = "SELECT COUNT(*) FROM users"

    q = QueryParts()

    if search:
        q.where_like("username", search.username)
        q.where_like("email", search.email)
        q.where_like("nick_name", search.nick_name)
        q.where_eq("is_admin", search.is_admin)

    where = q.where_sql()

    # 注意：分页的 LIMIT/OFFSET 由 fetch_page 统一追加
    data_sql = base_select + where + " ORDER BY user_id"
    count_sql = base_count + where

    return BuiltQuery(data_sql=data_sql, count_sql=count_sql, params=tuple(q.params))
