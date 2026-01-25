from app.utils.password import verify_password
from app.repositories.user_repo import get_user_by_username
from app.utils.jwt import create_jwt
from app.schemas.user import UserOut

def authenticate_user(username: str, password: str):
    user_info = get_user_by_username(username)

    if not user_info:
        return None
    
    if not verify_password(password, user_info.password):
        return None
    
    user_out = UserOut(**user_info.model_dump())
    return create_jwt(user_out.model_dump())
