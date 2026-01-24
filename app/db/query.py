from app.db.connection import get_connection

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