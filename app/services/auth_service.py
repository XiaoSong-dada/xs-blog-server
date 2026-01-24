from app.utils.password import get_password_hash
from app.repositories.user_repo import getUser

def authenticate_user(username: str, password: str):
    user_info = getUser(username)
    
    return 