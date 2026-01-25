from contextlib import contextmanager
import psycopg
from app.db.connection import get_connection

@contextmanager
def transaction() -> psycopg.Connection:
    """
    标准事务封装：
    - 成功：commit
    - 异常：rollback 并向上抛（让 service 统一处理/记录）
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
