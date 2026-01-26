# app/repositories/base.py

from __future__ import annotations

from typing import Any, Mapping, Sequence, TypeAlias
import psycopg

# 兼容 tuple / list / dict / None 的参数形式
Params: TypeAlias = Sequence[Any] | Mapping[str, Any] | None
Row: TypeAlias = dict[str, Any]


def _ensure_params(params: Params) -> None:
    if isinstance(params, str):
        raise TypeError("params must be tuple/list/dict; for single param use (value,)")


def _row_to_dict(cur: psycopg.Cursor, row: Sequence[Any]) -> Row:
    """
    将 cursor.fetchone()/fetchall() 返回的 row 转成 dict。
    注意：cur.description 只有在执行过 SQL 后才会有值。
    """
    colnames = [desc[0] for desc in cur.description]
    return dict(zip(colnames, row))


def fetch_one(conn: psycopg.Connection, sql: str, params: Params = None) -> Row | None:
    """
    执行查询并返回单条记录（dict），没有记录返回 None。
    - 不创建连接
    - 不提交事务（读操作不需要 commit）
    """
    with conn.cursor() as cur:
        if isinstance(params, str):
            raise TypeError("params must be tuple/list/dict; for single param use (value,)")
        cur.execute(sql, params)
        row = cur.fetchone()
        if row is None:
            return None
        return _row_to_dict(cur, row)


def fetch_all(conn: psycopg.Connection, sql: str, params: Params = None) -> list[Row]:
    """
    执行查询并返回多条记录（list[dict]），没有记录返回 []。
    - 不创建连接
    - 不提交事务
    """
    with conn.cursor() as cur:
        if isinstance(params, str):
            raise TypeError("params must be tuple/list/dict; for single param use (value,)")
        cur.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return []
        return [_row_to_dict(cur, row) for row in rows]

# 分页获取记录
def fetch_page(
    conn: psycopg.Connection,
    sql: str,
    params: Params = None,
    limit: int = 10,
    offset: int = 0,
) -> list[Row]:
    """
    执行分页查询并返回多条记录（list[dict]），没有记录返回 []。
    - 不创建连接
    - 不提交事务
    """
    # 分页 SQL 语句
    paged_sql = f"{sql} LIMIT %s OFFSET %s"
    
    # 处理查询参数
    if params is None:
        paged_params = (limit, offset)
    elif isinstance(params, (list, tuple)):
        paged_params = (*params, limit, offset)
    elif isinstance(params, dict):
        paged_params = {**params, "limit": limit, "offset": offset}
    elif isinstance(params, str):  # 如果只有一个参数（例如：用户名）
        paged_params = (params, limit, offset)
    else:
        raise TypeError("params must be tuple, list, or dict. For single param use (value,)")

    # 执行查询
    try:
        with conn.cursor() as cur:
            cur.execute(paged_sql, paged_params)
            rows = cur.fetchall()

            colnames = [desc[0] for desc in cur.description]

            return [dict(zip(colnames, row)) for row in rows] if rows else []
    except psycopg.Error as e:
        raise Exception(f"Database error occurred: {e}")

# 获取页数
def fetch_count(conn: psycopg.Connection, sql: str, params: Params = None) -> int:
    with conn.cursor() as cur:
        if isinstance(params, str):
            raise TypeError("params must be tuple/list/dict; for single param use (value,)")
        cur.execute(sql, params)
        row = cur.fetchone()
        return int(row[0]) if row else 0


def execute(conn: psycopg.Connection, sql: str, params: Params = None) -> int:
    """
    通用写操作执行器：
    - 返回 rowcount（受影响行数）
    - 不 commit/rollback（事务由 service 的 transaction() 统一负责）
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount
    

