from app.ai.registry import get_function
from app.schemas.user import UserInDB


def check_permission(user: UserInDB, function_name: str) -> bool:
    fn = get_function(function_name)
    if fn is None:
        return False
    if fn.required_permission == "require_login":
        return True
    if fn.required_permission == "require_admin":
        return user.is_admin
    return False
