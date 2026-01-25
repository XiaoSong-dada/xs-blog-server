from typing import Any, Mapping, Sequence
import psycopg
from app.db.connection import get_connection

Params = Sequence[Any] | Mapping[str, Any] | None

 # 执行 SQL 查询并返回单条记录的字典表示
def fetch_one(sql, params) -> dict|None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row:
                colnames = [desc[0] for desc in cur.description]
                return dict(zip(colnames, row))
   
    return None

# 执行 SQL 查询并返回多条记录的字典列表表示
def fetch_all(sql, params) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                colnames = [desc[0] for desc in cur.description]
                return [dict(zip(colnames, row)) for row in rows]
    return []


def execute(conn: psycopg.Connection, sql: str, params: Params = None) -> int:
    """
    通用写操作执行器：
    - 返回 rowcount（受影响行数）
    - 不 commit/rollback（事务由 transaction() 统一负责）
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount
