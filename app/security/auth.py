from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt import decode_jwt

security = HTTPBearer()

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
):
    token = creds.credentials
    payload = decode_jwt(token)  # 你已有 jwt 工具
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # payload里一般有 user_id/username/is_admin
    return payload  # 或去DB查用户对象