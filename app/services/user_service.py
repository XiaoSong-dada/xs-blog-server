from app.core.exceptions import AppError
from app.db.transaction import transaction
from app.repositories.user_repo import (
    create_user,
    delete_by_username,
    list_users,
    get_user_by_username,
    get_user_by_id,
    update_user as update_user_repo,
)
from app.schemas.user import UserCreate, UserInDB, UserListQuery
from app.security.password import get_password_hash
from app.utils.verification import is_null_or_empty


def register_user(user: UserCreate) -> None:
    user_in_db = UserInDB(
        username=user.username,
        password=get_password_hash(user.password),
        email=user.email,
        nick_name=user.nick_name,
    )
    with transaction() as conn:
        ok = create_user(conn, user_in_db)
        if not ok:
            raise AppError("username already exists", code=409)


def register_admin_user(user: UserCreate) -> None:
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
            raise AppError("username already exists", code=409)


def delete_user(username: str, admin_user) -> None:
    if not admin_user.is_admin:
        raise AppError("admin required", code=403)

    if admin_user.username == username:
        raise AppError("cannot delete yourself", code=400)

    with transaction() as conn:
        ok = delete_by_username(conn, username)
        if not ok:
            raise AppError("user not found", code=404)


def get_users_page(search: UserListQuery | None = None):
    search = search or UserListQuery()

    with transaction() as conn:
        users, total = list_users(
            conn,
            limit=search.limit,
            offset=search.offset,
            search=search,
        )

    return {
        "data": [u.model_dump() for u in users],
        "total": total,
        "limit": search.limit,
        "offset": search.offset,
    }


def get_cache_user_detail(username: str) -> UserInDB:
    if is_null_or_empty(username):
        raise AppError("查询用户名不能为空!", code=404)
    with transaction() as conn:
        user = get_user_by_username(conn, username)
        if not user:
            raise AppError("用户未找到", code=404)
    return user


def get_user_detail_by_id(user_id: str) -> UserInDB:
    if is_null_or_empty(user_id):
        raise AppError("查询用户名不能为空!", code=404)
    with transaction() as conn:
        user = get_user_by_id(conn, user_id)
        if not user:
            raise AppError("用户未找到", code=404)
    return user

def update_user(user: UserInDB)->bool:
    with transaction() as conn:
        ok = update_user_repo(conn, user)
        if not ok:
            raise AppError("用户信息更新失败", code=500)

    return ok