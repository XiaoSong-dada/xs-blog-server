from app.db.transaction import transaction
from app.repositories.user_repo import create_user, delete_by_username
from app.schemas.user import UserCreate, UserInDB
from app.security.password import get_password_hash

class UsernameTakenError(RuntimeError):
    """业务异常：用户名已存在"""

# 注册新用户
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
            raise UsernameTakenError("用户已存在！")
        
# 创建管理员账号       
def register_admin_user(user: UserCreate) -> None:
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
        is_admin=True,
    )
    with transaction() as conn:
        ok = create_user(conn, user_in_db)
        if not ok:
            # 这属于业务失败，可控
            raise UsernameTakenError("用户已存在！")
        
def delete_user(username: str, admin_user) -> None:
    if not admin_user["is_admin"]:
        raise UsernameTakenError("无权限删除用户！")

    if admin_user["username"] == username:
        raise UsernameTakenError("不能删除自己！")

    with transaction() as conn:
        ok = delete_by_username(conn, username)
        if not ok:
            raise UsernameTakenError("用户不存在！")