from fastapi import Depends, HTTPException, Request
import logging
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt import decode_jwt
from app.services.user_service import get_cache_user_detail

logger = logging.getLogger(__name__)


security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
):
    token = creds.credentials
    payload = decode_jwt(token)  # 你已有 jwt 工具
    if not payload or "username" not in payload:
        raise HTTPException(status_code=401, detail="Not authenticated")

    logger.info("login user %s", payload)
    username = payload["username"]

    # 否则从数据库查询
    user = get_cache_user_detail(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 4. 返回用户对象或用户信息，进一步提升 API 层级结构化
    return user


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(security_optional),
):
    if creds is None:
        return None

    token = creds.credentials
    payload = decode_jwt(token)
    if not payload or "username" not in payload:
        return None

    username = payload["username"]
    user = get_cache_user_detail(username)
    if not user:
        return None

    return user
