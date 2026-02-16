from fastapi import Depends, HTTPException
from app.security.auth import get_current_user, get_current_user_optional


def require_admin(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return user


def require_login(user=Depends(get_current_user)):
    return user


def require_login_optional(user=Depends(get_current_user_optional)):
    return user
