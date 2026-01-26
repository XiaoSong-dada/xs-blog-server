from app.core.exceptions import AppError
from app.db.transaction import transaction
from app.repositories.user_repo import create_user, delete_by_username, list_users
from app.schemas.user import UserCreate, UserInDB, UserListQuery
from app.security.password import get_password_hash


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
    if not admin_user["is_admin"]:
        raise AppError("admin required", code=403)

    if admin_user["username"] == username:
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
