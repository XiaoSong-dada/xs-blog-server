from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.base import ErrorResponse, SuccessResponse
from app.schemas.user import UserCreate
from app.services.user_service import UsernameTakenError, register_user

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
