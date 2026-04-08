from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo_async import UserRepoAsync
from app.security.password import verify_password
from app.security.jwt import create_jwt


async def authenticate_user(db: AsyncSession, username: str, password: str) -> str | None:
    user = await UserRepoAsync.get_by_username_active(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None

    payload = {
        "user_id": str(user.user_id),
        "username": user.username,
        "is_admin": user.is_admin,
    }
    return create_jwt(payload)
