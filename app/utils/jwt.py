import jwt
from app.core.config import settings
from app.utils.datetime_utils import utc_now_plus, utc_timestamp

def verify_jwt(token:str) -> dict:
    try:
        decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        # 处理过期的令牌
        return None
    except jwt.InvalidTokenError:
        # 处理无效的令牌
        return None
    
def create_jwt(data: dict) -> str:
    payload = data.copy()
    payload['exp'] = int((utc_timestamp(utc_now_plus(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))))
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token