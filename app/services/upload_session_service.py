# app/services/upload_session_service.py
from __future__ import annotations

import time
import uuid
from typing import Optional
from redis.asyncio import Redis
from app.core.redis import get_redis
from app.utils.redis_keys import key_upload_session, key_upload_session_files

SESSION_TTL_SECONDS = 600
LOCK_TTL_MS = 10_000  # 10 秒，commit 通常够了


class UploadSessionService:
    @staticmethod
    async def create(user_id: str) -> dict:
        r = get_redis()
        session_id = str(uuid.uuid4())
        key = key_upload_session(session_id)

        now = int(time.time())
        mapping = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": str(now),
            "status": "OPEN",
        }

        # 先写，再设过期（两步够用；如果你追求原子可以用 pipeline）
        await r.hset(key, mapping=mapping)
        await r.expire(key, SESSION_TTL_SECONDS)

        return {"session_id": session_id, "expires_in": SESSION_TTL_SECONDS}

    @staticmethod
    async def get(session_id: str) -> Optional[dict]:
        r = get_redis()
        key = key_upload_session(session_id)

        if not await r.exists(key):
            return None
        return await r.hgetall(key)

    @staticmethod
    async def refresh(session_id: str) -> bool:
        """滑动续期：每次 upload 时调用"""
        r = get_redis()
        key = key_upload_session(session_id)
        return await r.expire(key, SESSION_TTL_SECONDS)

    @staticmethod
    async def update_to_committing(session_id: str) -> bool:
        redis: Redis = get_redis()  # 你自己的 redis 连接

        key = key_upload_session(session_id)

        lua = """
        local status = redis.call("HGET", KEYS[1], "status")
        if status ~= ARGV[1] then
            return 0
        end
        redis.call("HSET", KEYS[1], "status", ARGV[2])
        return 1
        """

        result = await redis.eval(lua, 1, key, "OPEN", "COMMITTING")
        return int(result) == 1

    @staticmethod
    async def add_file(session_id: str, file_id: str) -> None:
        """记录上传的文件 id（set 去重）"""
        r = get_redis()
        files_key = key_upload_session_files(session_id)

        await r.sadd(files_key, file_id)
        # files 集合也要跟着 session 一起过期
        await r.expire(files_key, SESSION_TTL_SECONDS)

    @staticmethod
    async def list_files(session_id: str) -> list[str]:
        r = get_redis()
        files_key = key_upload_session_files(session_id)
        return list(await r.smembers(files_key))

    # 添加分布式锁
    @staticmethod
    async def acquire_commit_lock(session_id: str) -> str | None:
        r = get_redis()
        lock_key = f"lock:upload_session:commit:{session_id}"
        lock_value = str(uuid.uuid4())

        ok = await r.set(
            lock_key,
            lock_value,
            nx=True,
            px=LOCK_TTL_MS,
        )

        if ok:
            return lock_value  # 拿到锁
        return None  # 没拿到
