# app/utils/redis_keys.py
from app.core.config import settings


def key_upload_session(session_id: str) -> str:
    return f"{settings.REDIS_PREFIX}:upload_session:{session_id}"


def key_upload_session_files(session_id: str) -> str:
    return f"{settings.REDIS_PREFIX}:upload_session:{session_id}:files"


def key_lock(name: str) -> str:
    return f"{settings.REDIS_PREFIX}:lock:{name}"
