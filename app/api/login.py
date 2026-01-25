from fastapi import APIRouter
from app.schemas.login import LoginRequest
from app.utils.verification import is_null_or_empty
from app.schemas.base import ErrorResponse , SuccessResponse
from app.services.auth_service import authenticate_user
router = APIRouter()


@router.post("/login")
def login(UserRequest: LoginRequest):

    if is_null_or_empty(UserRequest.username) or is_null_or_empty(UserRequest.password):
        return ErrorResponse(message="用户名或密码不能为空", code=400)

    # 获取前端传入字段
    username = UserRequest.username
    password = UserRequest.password

    authenticate_user_result = authenticate_user(username, password)

    if not authenticate_user_result:
        return ErrorResponse(message="用户名或密码错误", code=401)

    return SuccessResponse(message="登录成功", code=200, data={"token": authenticate_user_result})