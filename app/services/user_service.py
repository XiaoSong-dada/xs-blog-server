from app.db.transaction import transaction
from app.repositories.user_repo import create_user
from app.schemas.user import UserCreate, UserInDB
from app.utils.password import get_password_hash

class UsernameTakenError(RuntimeError):
    """业务异常：用户名已存在"""

def register_user(user: UserCreate) -> None:
    """
    service 负责把 repo 的返回值翻译成业务含义。
    - repo 返回 False：业务失败（用户名已存在）
    - repo 抛异常：系统失败（向上抛，由更上层统一处理/记录）
    """
    user_in_db = UserInDB(
        username=user.username,
        password=get_password_hash(user.password),
        email=user.email,
        nick_name=user.nick_name,
    )
    with transaction() as conn:
        ok = create_user(conn, user_in_db)
        if not ok:
            # 这属于业务失败，可控
            raise UsernameTakenError("username already exists")
