import psycopg
from app.schemas.file import File
from app.repositories.base import fetch_one


def create_file(conn: psycopg.Connection, file: File) -> File | None:
    sql = """
    INSERT INTO files (
        id, owner_user_id, bucket, original_name, stored_path,
        content_type, size, sha256
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, owner_user_id, bucket, original_name, stored_path,
              content_type, size, sha256, created_at, deleted_at
    """
    params = (
        file.id,
        file.owner_user_id,
        file.bucket,
        file.original_name,
        file.stored_path,
        file.content_type,
        file.size,
        file.sha256,
    )
    data = fetch_one(conn, sql, params)
    return File(**data) if data else None
