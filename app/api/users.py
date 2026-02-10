from fastapi import APIRouter, Depends, status
import logging

from app.security.permissions import require_admin, require_login
from app.schemas.base import (
    SuccessResponse,
    PaginatedResponse,
    SuccessResponseBase,
    ErrorResponse,
)
from app.schemas.user import (
    UserCreate,
    UserListQuery,
    UserInDB,
    UserUpdate,
    UserUpdatePassword,
)
from app.services.user_service import (
    register_user,
    delete_user,
    get_users_page,
    update_user,
    update_password,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
def register(user: UserCreate):
    register_user(user)
    return SuccessResponse(message="register success", code=201)


@router.delete("/{user_name}", status_code=200)
def delete(user_name: str, admin_user=Depends(require_admin)):
    delete_user(user_name, admin_user=admin_user)
    return SuccessResponse(message="delete success", code=200)


@router.get("", response_model=PaginatedResponse)
def list_users(query: UserListQuery = Depends(), _admin=Depends(require_admin)):
    logger.info("query: %s", query)
    user_data = get_users_page(query)
    return PaginatedResponse(message="ok", code=200, **user_data)


@router.get("/owner/info", response_model=SuccessResponse)
def get_user_by_name(_user: UserInDB = Depends(require_login)):
    logger.info("查询账号信息: %s", _user)

    return SuccessResponse(message="ok", code=200, data=_user.model_dump())


@router.put("/owner/info", response_model=SuccessResponseBase)
def update_user_info(user_update: UserUpdate, user: UserInDB = Depends(require_login)):
    logger.info("更新账号信息: %s", user_update)
    updated_user = user.model_copy(update=user_update.model_dump(exclude_unset=True))
    ok = update_user(updated_user)
    if not ok:
        return ErrorResponse("用户信息更新失败", code=500)
    return SuccessResponseBase(message="ok", code=200)


@router.put("/owner/password", response_model=SuccessResponseBase)
def update_user_info(
    user_update: UserUpdatePassword, user: UserInDB = Depends(require_login)
):
    logger.info("修改账号密码: %s", user_update)
    
    if not user_update.old_password:
        return ErrorResponse("用户旧密码不能为空", code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    
    user_in_db =  user.model_copy(update=user_update.model_dump(exclude_unset=True))

    ok = update_password(user_in_db, user_update.old_password , user.password)

    if not ok:
        return ErrorResponse("用户信息更新失败", code=500)
    return SuccessResponseBase(message="ok", code=200)
