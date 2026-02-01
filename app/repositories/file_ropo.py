import psycopg
from app.schemas.file import File
from app.repositories.base import execute


def create_file(conn: psycopg.Connection, file: File) -> File | None:
    sql = """
    INSERT INTO files (
         owner_user_id, bucket, original_name, stored_path,
        content_type, size, sha256
    )
    VALUES ( %s, %s, %s, %s, %s, %s, %s)
    RETURNING  owner_user_id, bucket, original_name, stored_path,
              content_type, size, sha256, created_at, deleted_at
    """
    params = (
        file.owner_user_id,
        file.bucket,
        file.original_name,
        file.stored_path,
        file.content_type,
        file.size,
        file.sha256,
    )
    affected = execute(conn, sql, params)
    return affected == 1
