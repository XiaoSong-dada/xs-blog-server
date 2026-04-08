from __future__ import annotations

import hashlib
import json
import secrets

from app.core.redis import get_redis

CAPTCHA_TOKEN_TTL_SECONDS = 180
CAPTCHA_TOKEN_PREFIX = "captcha:token"


class CaptchaTokenService:
    @staticmethod
    def _build_key(token: str) -> str:
        return f"{CAPTCHA_TOKEN_PREFIX}:{token}"

    @staticmethod
    def _normalize_ua(user_agent: str | None) -> str:
        raw = (user_agent or "").strip()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    async def issue_token(
        username: str,
        client_ip: str,
        user_agent: str | None,
        ttl_seconds: int = CAPTCHA_TOKEN_TTL_SECONDS,
    ) -> tuple[str, int]:
        redis = get_redis()
        token = secrets.token_urlsafe(32)
        key = CaptchaTokenService._build_key(token)

        payload = {
            "username": username,
            "ip": client_ip,
            "ua_hash": CaptchaTokenService._normalize_ua(user_agent),
        }
        await redis.set(key, json.dumps(payload), ex=ttl_seconds)
        return token, ttl_seconds

    @staticmethod
    async def consume_and_validate(
        captcha_token: str,
        username: str,
        client_ip: str,
        user_agent: str | None,
    ) -> tuple[bool, str]:
        redis = get_redis()
        key = CaptchaTokenService._build_key(captcha_token)

        script = """
        local value = redis.call('GET', KEYS[1])
        if not value then
            return nil
        end
        redis.call('DEL', KEYS[1])
        return value
        """
        stored_payload = await redis.eval(script, 1, key)
        if not stored_payload:
            return False, "invalid_or_expired"

        try:
            parsed = json.loads(stored_payload)
        except (json.JSONDecodeError, TypeError):
            return False, "invalid_or_expired"

        expected_ua = CaptchaTokenService._normalize_ua(user_agent)
        if (
            parsed.get("username") != username
            or parsed.get("ip") != client_ip
            or parsed.get("ua_hash") != expected_ua
        ):
            return False, "binding_mismatch"

        return True, "ok"
