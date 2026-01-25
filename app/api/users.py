from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.security.permissions import require_admin
from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.user import UserCreate
from app.services.user_service import UsernameTakenError, register_user, delete_user

router = APIRouter()


@router.post("/register", status_code=201)
def register(user: UserCreate):
    try:
        register_user(user)
        return SuccessResponse(message="注册成功", code=201)
    except UsernameTakenError:
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(message="用户名已存在", code=409).dict(),
        )

@router.delete("/delete/{user_name}", status_code=200)
def delete(user_name: str, admin_user = Depends(require_admin)):
    try:
        delete_user(user_name, admin_user=admin_user)
        return SuccessResponse(message="用户删除成功", code=200)
    except UsernameTakenError:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(message="用户不存在", code=404).dict(),
        )